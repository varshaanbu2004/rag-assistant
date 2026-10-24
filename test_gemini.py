import os, time
from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

t = time.time()
response = client.models.generate_content(
    model=os.getenv("GEMINI_MODEL", "gemini-3.8-flash"),
    contents="Say hello in one sentence.",
)
print(response.text)
print(f"Took {time.time() - t:.1f}s")