import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

MODELS = [
    "gemini-3.1-flash-lite",
    "gemini-3.5-flash-lite",
    "gemini-3.6-flash",
    "gemini-3.7-flash",
    "gemini-flash-lite-latest",
    "gemini-flash-latest",
    "gemini-2.5-flash-lite",
]

client = genai.Client(
    api_key=os.environ["GEMINI_API_KEY"],
    http_options=types.HttpOptions(api_version="v1beta", timeout=20000),
)

working = []
for name in MODELS:
    try:
        r = client.models.generate_content(
            model=name,
            contents="Reply with one short sentence confirming you are working.",
        )
        print("OK  ", name, "->", (r.text or "").strip()[:60], flush=True)
        working.append(name)
    except Exception as e:
        print("FAIL", name, "->", type(e).__name__, str(e)[:70].replace("\n", " "), flush=True)

print()
print("Working models:", working)