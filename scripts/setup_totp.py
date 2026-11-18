import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import auth

secret = auth.new_secret()

print()
print("1) In Google Authenticator: tap +, then 'Enter a setup key'")
print("   Account name : einvoice-admin")
print(f"   Your key     : {secret}")
print("   Type of key  : Time based")
print()
print("2) Add this line to your local .env file:")
print(f"   TOTP_SECRET={secret}")
print()
print("3) Add this line to the Streamlit Cloud Secrets (it uses quote marks):")
print(f'   TOTP_SECRET = "{secret}"')
print()
print("Keep this key private. Do not paste it into chats, screenshots or GitHub.")