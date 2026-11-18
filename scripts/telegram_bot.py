import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from app.telegram_bot import confirm, get_me, poll

token = os.getenv("TELEGRAM_BOT_TOKEN")
if not token:
    raise SystemExit("TELEGRAM_BOT_TOKEN is not set.")

try:
    username = get_me(token)
except Exception as e:
    # Print only the error type: the full message would contain the token.
    raise SystemExit(f"Telegram rejected the token or could not be reached ({type(e).__name__}).")

if "--once" in sys.argv:
    print(f"Connected as @{username}. Handling waiting messages once.")
    confirm(token, poll(token))
    print("Done.")
else:
    print(f"Connected as @{username}. Send an invoice photo to the bot. Press Ctrl+C to stop.")
    offset = None
    while True:
        try:
            offset = poll(token, offset, wait=10)
        except KeyboardInterrupt:
            break
        except Exception as e:
            print("Temporary error:", type(e).__name__)
            time.sleep(5)
    print("Stopped.")