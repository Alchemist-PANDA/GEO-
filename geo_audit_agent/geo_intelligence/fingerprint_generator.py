import requests
from bs4 import BeautifulSoup

try:
    import extruct
    HAS_EXTRUCT = True
except ImportError:
    HAS_EXTRUCT = False


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
            val = desc_tag.get("content", "")
            meta_desc = val if isinstance(val, str) else ""

        # Extract all text
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text(separator=' ')

        # Extract JSON-LD and other microdata (extruct is optional)
        if HAS_EXTRUCT:
            data = extruct.extract(html, base_url=url)
        else:
            # Fallback: parse JSON-LD blocks directly with BeautifulSoup
            import json
            json_ld = []
            for tag in BeautifulSoup(html, "html.parser").find_all("script", type="application/ld+json"):
                try:
                    json_ld.append(json.loads(tag.string or ""))
                except (ValueError, TypeError):
                    continue
            data = {"json-ld": json_ld, "microdata": []}

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
    """Identifies most important keywords in the content using TF-IDF, falling back to frequency if sklearn is missing."""
    if not text or len(text) < 10:
        return []
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        vectorizer = TfidfVectorizer(stop_words='english', max_features=top_n)
        vectorizer.fit_transform([text])
        return vectorizer.get_feature_names_out().tolist()
    except ImportError:
        # Fallback keyword extraction using simple word frequencies minus basic English stop words
        import re
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        stop_words = {
            'the', 'and', 'a', 'to', 'of', 'in', 'i', 'is', 'that', 'it', 'on', 'you', 'this', 'for', 'but', 'with', 'as',
            'are', 'was', 'they', 'be', 'at', 'one', 'have', 'from', 'or', 'had', 'by', 'hot', 'word',
            'some', 'what', 'there', 'we', 'can', 'out', 'other', 'were', 'all', 'when', 'up', 'use',
            'your', 'how', 'said', 'an', 'each', 'she', 'which', 'do', 'their', 'time', 'if', 'will', 'way', 'about',
            'many', 'then', 'them', 'write', 'would', 'like', 'so', 'these', 'her', 'long', 'make', 'thing', 'see',
            'him', 'two', 'has', 'look', 'more', 'day', 'could', 'go', 'come', 'did', 'number', 'sound', 'no', 'most',
            'people', 'my', 'over', 'know', 'water', 'than', 'call', 'first', 'who', 'may', 'down', 'side', 'been',
            'now', 'find', 'any', 'new', 'work', 'part', 'take', 'get', 'place', 'made', 'live', 'where', 'after',
            'back', 'little', 'only', 'round', 'man', 'year', 'came', 'show', 'every', 'good', 'me', 'give', 'our',
            'under', 'name', 'very', 'through', 'just', 'form', 'sentence', 'great', 'think', 'say', 'help', 'low',
            'line', 'differ', 'turn', 'cause', 'much', 'mean', 'before', 'move', 'right', 'boy', 'old', 'too', 'same',
            'tell', 'does', 'set', 'three', 'want', 'air', 'well', 'also', 'play', 'small', 'end', 'put', 'home',
            'read', 'hand', 'port', 'large', 'spell', 'add', 'even', 'land', 'here', 'must', 'big', 'high', 'such',
            'follow', 'act', 'why', 'ask', 'men', 'change', 'went', 'light', 'kind', 'off', 'need', 'house', 'picture',
            'try', 'us', 'again', 'animal', 'point', 'mother', 'world', 'near', 'build', 'self', 'earth', 'father',
            'head', 'stand', 'own', 'page', 'should', 'country', 'found', 'answer', 'school', 'grow', 'study', 'still',
            'learn', 'plant', 'cover', 'food', 'sun', 'four', 'between', 'state', 'keep', 'eye', 'never', 'last',
            'let', 'thought', 'city', 'tree', 'cross', 'farm', 'hard', 'start', 'might', 'story', 'saw', 'far',
            'sea', 'draw', 'left', 'late', 'run', 'don', 'while', 'press', 'close', 'night', 'real', 'life', 'few',
            'north', 'open', 'seem', 'together', 'next', 'white', 'children', 'begin', 'got', 'walk', 'example',
            'ease', 'paper', 'group', 'always', 'music', 'those', 'both', 'mark', 'often', 'letter', 'until', 'mile',
            'river', 'car', 'feet', 'care', 'second', 'carry', 'took', 'rain', 'eat', 'room', 'friend',
            'began', 'idea', 'fish', 'mountain', 'stop', 'once', 'base', 'hear', 'horse', 'cut', 'sure', 'watch',
            'color', 'face', 'wood', 'main', 'enough', 'plain', 'girl', 'usual', 'young',
            'ready', 'above', 'ever', 'red', 'list', 'though', 'feel', 'talk', 'bird', 'soon', 'body', 'dog', 'family',
            'direct', 'pose', 'leave', 'song', 'measure', 'product', 'black', 'short', 'numeral', 'class',
            'wind', 'question', 'happen', 'complete', 'ship', 'area', 'half', 'rock', 'order', 'fire', 'south',
            'problem', 'piece', 'told', 'knew', 'pass', 'since', 'top', 'whole', 'king', 'space', 'heard', 'best',
            'hour', 'better', 'true', 'during', 'hundred', 'five', 'remember', 'step', 'early', 'hold', 'west',
            'ground', 'interest', 'reach', 'fast', 'verb', 'sing', 'listen', 'six', 'table', 'travel', 'less',
            'morning', 'ten', 'simple', 'several', 'vowel', 'toward', 'war', 'lay', 'against', 'pattern', 'slow',
            'center', 'love', 'person', 'money', 'serve', 'road', 'map', 'rule', 'govern', 'pull', 'cold',
            'notice', 'voice', 'unit', 'power', 'town', 'fine', 'certain', 'fly', 'fall', 'lead', 'cry', 'dark',
            'machine', 'note', 'wait', 'plan', 'figure', 'star', 'box', 'noun', 'field', 'rest', 'correct', 'able',
            'pound', 'done', 'beauty', 'drive', 'stood', 'contain', 'front', 'teach', 'week', 'final', 'gave', 'green',
            'oh', 'quick', 'develop', 'ocean', 'warm', 'free', 'minute', 'strong', 'special', 'mind', 'behind',
            'clear', 'tail', 'produce', 'fact', 'street', 'image', 'itself', 'offers'
        }
        filtered_words = [w for w in words if w not in stop_words and len(w) > 2]
        # Count frequencies
        freq: dict[str, int] = {}
        for w in filtered_words:
            freq[w] = freq.get(w, 0) + 1
        # Sort and return top n
        sorted_words = sorted(freq.items(), key=lambda x: x[1], reverse=True)
        return [w for w, f in sorted_words[:top_n]]

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
