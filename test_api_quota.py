import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
try:
    response = client.models.generate_content(
        model="gemini-2.0-flash-lite",
        contents="Say OK"
    )
    print(f"API Response: {response.text}")
except Exception as e:
    print(f"API Error: {e}")
