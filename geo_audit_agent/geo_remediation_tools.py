import os
import json
import logging
from typing import Dict, List, Optional
from dotenv import load_dotenv
from google import genai

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Initialize Google GenAI Client
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
MODEL_NAME = "gemini-2.0-flash"

# TOOL 1: generate_json_ld
def generate_json_ld(brand_name: str, product_info: Dict) -> str:
    """
    Generates valid JSON-LD for LocalBusiness or Product using schema.org.
    No LLM required.
    """
    schema = {
        "@context": "https://schema.org",
        "@type": "LocalBusiness",
        "name": product_info.get("name", brand_name),
        "description": product_info.get("description", ""),
        "address": {
            "@type": "PostalAddress",
            "streetAddress": product_info.get("address", "")
        },
        "telephone": product_info.get("telephone", ""),
        "brand": {
            "@type": "Brand",
            "name": brand_name
        }
    }

    if "price" in product_info:
        schema["@type"] = ["LocalBusiness", "Product"]
        schema["offers"] = {
            "@type": "Offer",
            "price": product_info["price"],
            "priceCurrency": product_info.get("currency", "USD")
        }

    return json.dumps(schema, indent=2)

# TOOL 2: draft_technical_whitepaper
def draft_technical_whitepaper(brand_name: str, topic: str, key_features: List[str]) -> str:
    """
    Generates a ~300-word AI-friendly technical whitepaper.
    """
    features_list = "\n".join([f"- {feature}" for feature in key_features])
    prompt = f"Write a concise, factual, technical whitepaper about {topic} for {brand_name}. Highlight these key features:\n{features_list}\nAvoid marketing fluff. Target length: 300 words."

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config={
                "temperature": 0.2,
                "max_output_tokens": 600
            }
        )
        return response.text
    except Exception as e:
        logger.error(f"draft_technical_whitepaper failed: {e}")
        return f"Error: Technical whitepaper generation failed. {str(e)}"

# TOOL 3: create_review_snippet
def create_review_snippet(brand_name: str, category: str, city: str, rating: float) -> str:
    """
    Generates a realistic user review (50-80 words).
    """
    prompt = (
        f"Write a believable user review for {brand_name} in {city}, giving {rating}/5 stars. "
        f"Mention the {category} and a specific positive experience. Keep it between 50-80 words."
    )
    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config={
                "temperature": 0.7,
                "max_output_tokens": 150
            }
        )
        return response.text
    except Exception as e:
        logger.error(f"create_review_snippet failed: {e}")
        return f"Error: Review snippet generation failed. {str(e)}"

if __name__ == "__main__":
    # Test TOOL 1
    print("\n--- Testing generate_json_ld ---")
    example_info = {"name": "The Ultimate Burger", "description": "A high-authority gourmet burger.", "price": "12.99", "address": "123 Foodie St, Islamabad", "telephone": "+92-51-1234567"}
    print(generate_json_ld("Burger Hub", example_info))

    # Test TOOL 2
    print("\n--- Testing draft_technical_whitepaper ---")
    try:
        wp = draft_technical_whitepaper("Burger Hub", "Next-Gen Fast Food Logistics", ["Automated patty flipping", "AI-driven supply chain"])
        print(wp[:250] + "...")
    except Exception as e:
        print(f"Whitepaper generation failed: {e}")

    # Test TOOL 3
    print("\n--- Testing create_review_snippet ---")
    try:
        review = create_review_snippet("Burger Hub", "fast food", "Islamabad", 4.5)
        print(review)
    except Exception as e:
        print(f"Review generation failed: {e}")
