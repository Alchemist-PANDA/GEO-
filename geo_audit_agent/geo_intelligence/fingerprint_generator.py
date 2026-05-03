import requests
from bs4 import BeautifulSoup
import extruct
from sklearn.feature_extraction.text import TfidfVectorizer

def crawl_competitor(url: str):
    """Extracts text and structured data from a competitor URL."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')

        # Basic metadata
        title = soup.title.string if soup.title else ""
        meta_desc = ""
        desc_tag = soup.find("meta", attrs={"name": "description"})
        if desc_tag:
            meta_desc = desc_tag.get("content", "")

        # Extract all text
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text(separator=' ')

        # Extract JSON-LD and other microdata
        base_url = url
        data = extruct.extract(html, base_url=base_url)

        return {
            "url": url,
            "title": title,
            "description": meta_desc,
            "text": text,
            "structured_data": data
        }
    except Exception as e:
        return {"url": url, "error": str(e)}

def extract_tfidf_keywords(text: str, top_n=20):
    """Identifies most important keywords in the content."""
    if not text or len(text) < 10:
        return []
    vectorizer = TfidfVectorizer(stop_words='english', max_features=top_n)
    try:
        tfidf_matrix = vectorizer.fit_transform([text])
        return vectorizer.get_feature_names_out().tolist()
    except:
        return []

def extract_schema_types(structured_data: dict):
    """Lists all Schema.org types found on the page."""
    types = set()
    if not structured_data:
        return []

    # Check JSON-LD
    for item in structured_data.get('json-ld', []):
        if isinstance(item, dict):
            t = item.get('@type')
            if t:
                if isinstance(t, list):
                    types.update(t)
                else:
                    types.add(t)

    # Check Microdata
    for item in structured_data.get('microdata', []):
        t = item.get('type')
        if t:
            types.add(t)

    return list(types)

def build_fingerprint(brand_name: str, url: str):
    """Generates a complete semantic fingerprint for a brand."""
    data = crawl_competitor(url)
    if "error" in data:
        return data

    keywords = extract_tfidf_keywords(data['text'])
    schemas = extract_schema_types(data['structured_data'])

    return {
        "brand_name": brand_name,
        "url": url,
        "keywords": keywords,
        "schema_types": schemas,
        "content_length": len(data['text']),
        "has_whitepaper": "whitepaper" in data['text'].lower() or "technical" in data['text'].lower()
    }
