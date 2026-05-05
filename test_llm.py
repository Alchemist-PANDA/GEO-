import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
try:
    response = client.models.generate_content(
        model="gemini-2.0-flash-lite",
        contents="What is the capital of Pakistan? Answer in one word."
    )
    print(response.text)
except Exception as e:
    error_str = str(e)
    if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
        print(f"Quota Error: API quota exceeded. Check billing at https://ai.google.dev/gemini-api/docs/rate-limits")
    elif "401" in error_str or "403" in error_str or "PERMISSION_DENIED" in error_str:
        print(f"Auth Error: Invalid API key or permissions issue")
    else:
        print(f"Error: {e}")
