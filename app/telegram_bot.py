import requests

from app.extract_invoice import extract_from_bytes
from app.validator import validate

API = "https://api.telegram.org"
APP_URL = "https://einvoice-platform-gqkssavfmmblqxacg8ydpd.streamlit.app/"

HELP = (
    "Hi! Send me a photo of an invoice and I will read it and check it against the "
    "validation rules.\n\n"
    "Demo only: please send fake or sample invoices, not real ones."
)


def _call(token, method, **params):
    response = requests.post(
        f"{API}/bot{token}/{method}",
        json=params,
        timeout=params.get("timeout", 0) + 20,
    )
    response.raise_for_status()
    return response.json()["result"]


def get_me(token):
    return _call(token, "getMe")["username"]


def send(token, chat_id, text):
    _call(token, "sendMessage", chat_id=chat_id, text=text)


def download_file(token, file_id):
    info = _call(token, "getFile", file_id=file_id)
    response = requests.get(f"{API}/file/bot{token}/{info['file_path']}", timeout=30)
    response.raise_for_status()
    return response.content


def format_reply(invoice, issues, model):
    head = (
        f"Invoice {invoice.invoice_number}\n"
        f"Supplier: {invoice.supplier_name}\n"
        f"Total: {invoice.total_amount:,.2f} {invoice.currency}"
    )
    if not issues:
        return head + f"\n\nPASS: all validation rules passed.\n\n(Read by {model}. Demo only.)"
    lines = [head, "", f"FAIL: {len(issues)} problem(s) found:"]
    lines += [f"- [{i.rule}] {i.message}" for i in issues]
    lines += ["", f"For an AI-suggested fix, open the web app: {APP_URL}"]
    return "\n".join(lines)


def handle_update(token, update):
    message = update.get("message")
    if not message:
        return
    chat_id = message["chat"]["id"]

    file_id, mime = None, "image/jpeg"
    if message.get("photo"):
        file_id = message["photo"][-1]["file_id"]
    elif str((message.get("document") or {}).get("mime_type", "")).startswith("image/"):
        file_id = message["document"]["file_id"]
        mime = message["document"]["mime_type"]

    if file_id is None:
        send(token, chat_id, HELP)
        return

    send(token, chat_id, "Reading your invoice...")
    try:
        data = download_file(token, file_id)
        invoice, model = extract_from_bytes(data, mime)
        reply = format_reply(invoice, validate(invoice), model)
    except RuntimeError:
        reply = "The AI service is busy or unavailable right now. Please try again in a minute."
    except Exception:
        reply = "Sorry, I could not process that file. Please send a clear photo of an invoice."
    send(token, chat_id, reply)


def poll(token, offset=None, wait=0):
    """Fetch and handle waiting messages. Returns the offset for the next call."""
    params = {"timeout": wait, "allowed_updates": ["message"]}
    if offset is not None:
        params["offset"] = offset
    for update in _call(token, "getUpdates", **params):
        try:
            handle_update(token, update)
        except Exception:
            pass
        offset = update["update_id"] + 1
    return offset


def confirm(token, offset):
    """Tell Telegram the handled messages are done, so they are not delivered again."""
    if offset is not None:
        _call(token, "getUpdates", offset=offset, limit=1, timeout=0)