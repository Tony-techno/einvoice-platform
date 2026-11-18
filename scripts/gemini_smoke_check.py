import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

model = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
print("Using model:", model)

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

response = client.models.generate_content(
    model=model,
    contents="Reply with one short sentence confirming you are working.",
)

print("Text:", repr(response.text))
if response.candidates:
    print("Finish reason:", response.candidates[0].finish_reason)
print("Usage:", response.usage_metadata)
