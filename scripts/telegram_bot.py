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

args = sys.argv[1:]
minutes = None
if "--minutes" in args:
    try:
        minutes = float(args[args.index("--minutes") + 1])
    except (IndexError, ValueError):
        raise SystemExit("Usage: python scripts/telegram_bot.py --minutes 10")


def run_loop(deadline):
    offset = None
    while deadline is None or time.time() < deadline:
        try:
            offset = poll(token, offset, wait=10)
        except KeyboardInterrupt:
            break
        except Exception as e:
            print("Temporary error:", type(e).__name__, flush=True)
            time.sleep(5)
    try:
        confirm(token, offset)
    except Exception:
        pass


if "--once" in args:
    print(f"Connected as @{username}. Handling waiting messages once.", flush=True)
    confirm(token, poll(token))
    print("Done.")
elif minutes is not None:
    print(f"Connected as @{username}. Live for {minutes:g} minutes.", flush=True)
    run_loop(time.time() + minutes * 60)
    print("Done.")
else:
    print(f"Connected as @{username}. Send an invoice photo to the bot. Press Ctrl+C to stop.", flush=True)
    run_loop(None)
    print("Stopped.")