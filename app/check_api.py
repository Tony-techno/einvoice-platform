import os
import requests
from dotenv import load_dotenv

load_dotenv()
key = os.environ["GEMINI_API_KEY"]

try:
    r = requests.get(
        "https://generativelanguage.googleapis.com/v1beta/models",
        headers={"x-goog-api-key": key},
        timeout=20,
    )
except requests.exceptions.RequestException as e:
    print("Connection problem:", type(e).__name__)
    raise SystemExit(1)

print("Status:", r.status_code)
if r.ok:
    for m in r.json().get("models", []):
        if "generateContent" in m.get("supportedGenerationMethods", []):
            print(m["name"])
else:
    print(r.text[:300])