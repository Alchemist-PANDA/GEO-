import os
import logging
from google import genai
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type(Exception),
    before=lambda retry_state: logger.info(f"Retrying create_review_snippet (Attempt {retry_state.attempt_number})..."),
)
def create_review_snippet(brand_name: str, category: str, city: str, rating: float) -> str:
    """
    TOOL 3: create_review_snippet
    Generates a realistic user review (50-80 words) using Gemma 4 31B.
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in environment.")

    client = genai.Client(api_key=api_key)

    prompt = f"""Write a realistic user review for '{brand_name}', a {category} in {city}.
    The review should reflect a rating of {rating}/5.0.
    The review must be between 50 and 80 words.
    Focus on specific details like service, quality, and atmosphere.
    Do not use placeholders. Speak from the perspective of a local customer."""

    config = types.GenerateContentConfig(
        system_instruction="You are a helpful assistant that generates realistic, high-quality local business reviews.",
        max_output_tokens=200,
        temperature=0.7,
    )

    try:
        response = client.models.generate_content(
            model="gemma-4-31b-it",
            contents=prompt,
            config=config
        )
        review = response.text.strip()
        word_count = len(review.split())
        logger.info(f"Generated review for {brand_name} ({word_count} words).")
        return review
    except Exception as e:
        logger.error(f"Error generating review snippet: {e}")
        raise

if __name__ == "__main__":
    # Test Block
    print("\n--- Testing TOOL 3: create_review_snippet ---")
    try:
        test_review = create_review_snippet(
            brand_name="The Gourmet Kitchen",
            category="Italian Restaurant",
            city="New York",
            rating=4.5
        )
        print(f"\nBrand: The Gourmet Kitchen\nCategory: Italian Restaurant\nCity: New York\nRating: 4.5\n")
        print(f"Generated Review:\n{test_review}")
        print(f"\nWord Count: {len(test_review.split())}")
    except Exception as err:
        print(f"Test failed: {err}")
