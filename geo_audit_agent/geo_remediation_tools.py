import json
import logging
from typing import Dict, List
from dotenv import load_dotenv

# Import shared LLM client (Issue #6: single source of truth)
from .llm_client import call_proxy_llm

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# TOOL 1: generate_json_ld
def generate_json_ld(brand_name: str, product_info: Dict) -> str:
    """
    Generates valid JSON-LD for LocalBusiness or Product using schema.org.
    No LLM required.

    Args:
        brand_name: The brand name.
        product_info: Dict with keys: name, description, address, telephone, price, currency.

    Returns:
        A JSON-LD formatted string.
    """
    if not brand_name or not isinstance(brand_name, str):
        raise ValueError("brand_name must be a non-empty string")
    if not isinstance(product_info, dict):
        raise ValueError("product_info must be a dictionary")

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

    Args:
        brand_name: The brand name.
        topic: The whitepaper topic.
        key_features: List of features to highlight.

    Returns:
        The whitepaper content string.
    """
    if not brand_name or not topic:
        raise ValueError("brand_name and topic must be non-empty strings")
    if not key_features:
        raise ValueError("key_features must be a non-empty list")

    features_list = "\n".join([f"- {feature}" for feature in key_features])
    prompt = f"Write a concise, factual, technical whitepaper about {topic} for {brand_name}. Highlight these key features:\n{features_list}\nAvoid marketing fluff. Target length: 300 words."

    return call_proxy_llm("gc/gemini-3-flash-preview", [{"role": "user", "content": prompt}], max_tokens=600)

# TOOL 3: generate_review_template (Issue #18: renamed from create_review_snippet)
def generate_review_template(brand_name: str, category: str, city: str, rating: float) -> str:
    """
    Generates a TEMPLATE review for solicitation purposes (50-80 words).

    IMPORTANT: This content is a template/example ONLY. It must NOT be posted
    directly to review platforms (Google, Yelp, Facebook) as a real customer review.
    Use it as inspiration for legitimate customer outreach and review solicitation.

    Args:
        brand_name: The brand name.
        category: The business category.
        city: The city name.
        rating: The target rating (1.0-5.0).

    Returns:
        A template review string with disclaimer.
    """
    if not brand_name or not category or not city:
        raise ValueError("brand_name, category, and city must be non-empty strings")
    if not (1.0 <= rating <= 5.0):
        raise ValueError("rating must be between 1.0 and 5.0")

    prompt = (
        f"Write an example review template for {brand_name} in {city}, reflecting a {rating}/5 rating. "
        f"Mention the {category} and a specific positive experience. Keep it between 50-80 words. "
        f"This is a template for review solicitation, not a real customer review."
    )
    review = call_proxy_llm("gc/gemini-3-flash-preview", [{"role": "user", "content": prompt}], max_tokens=150, temperature=0.7)

    disclaimer = "\n\n[DISCLAIMER: This is an AI-generated template for review solicitation purposes only. Do not post as a genuine customer review.]"
    return review + disclaimer


# Backward compatibility alias
create_review_snippet = generate_review_template


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
    print("\n--- Testing generate_review_template ---")
    try:
        review = generate_review_template("Burger Hub", "fast food", "Islamabad", 4.5)
        print(review)
    except Exception as e:
        print(f"Review template generation failed: {e}")
