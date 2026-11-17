from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def font(size, bold=False):
    name = "arialbd.ttf" if bold else "arial.ttf"
    try:
        return ImageFont.truetype(name, size)
    except OSError:
        return ImageFont.load_default()


img = Image.new("RGB", (900, 1000), "white")
d = ImageDraw.Draw(img)

d.text((50, 40), "TAX INVOICE", font=font(38, True), fill="black")
d.text((50, 110), "Desert Palm Trading LLC", font=font(24, True), fill="black")
d.text((50, 145), "Business Bay, Dubai, UAE", font=font(20), fill="black")
d.text((50, 175), "TRN: 100123456700003", font=font(20), fill="black")

d.text((540, 110), "Invoice No: INV-2026-0042", font=font(20), fill="black")
d.text((540, 145), "Issue Date: 2026-11-10", font=font(20), fill="black")
d.text((540, 175), "Due Date: 2026-12-10", font=font(20), fill="black")
d.text((540, 205), "Currency: AED", font=font(20), fill="black")

d.text((50, 270), "Bill To:", font=font(22, True), fill="black")
d.text((50, 305), "Gulf Horizon Services FZCO", font=font(20), fill="black")
d.text((50, 335), "Dubai Silicon Oasis, UAE", font=font(20), fill="black")
d.text((50, 365), "TRN: 100987654300003", font=font(20), fill="black")

y = 440
d.line([(50, y), (850, y)], fill="black", width=2)
d.text((50, y + 10), "Description", font=font(20, True), fill="black")
d.text((450, y + 10), "Qty", font=font(20, True), fill="black")
d.text((540, y + 10), "Unit Price", font=font(20, True), fill="black")
d.text((700, y + 10), "Total", font=font(20, True), fill="black")
d.line([(50, y + 45), (850, y + 45)], fill="black", width=2)

rows = [
    ("Office chairs", 4, 450.00),
    ("Standing desks", 2, 1200.00),
    ("Delivery and installation", 1, 150.00),
]
y += 60
subtotal = 0.0
for desc, qty, price in rows:
    total = qty * price
    subtotal += total
    d.text((50, y), desc, font=font(20), fill="black")
    d.text((450, y), str(qty), font=font(20), fill="black")
    d.text((540, y), f"{price:,.2f}", font=font(20), fill="black")
    d.text((700, y), f"{total:,.2f}", font=font(20), fill="black")
    y += 40

d.line([(50, y), (850, y)], fill="black", width=2)
vat = round(subtotal * 0.05, 2)
grand = subtotal + vat
d.text((540, y + 20), f"Subtotal: {subtotal:,.2f}", font=font(20), fill="black")
d.text((540, y + 55), f"VAT (5%): {vat:,.2f}", font=font(20), fill="black")
d.text((540, y + 90), f"Total Due: {grand:,.2f} AED", font=font(22, True), fill="black")

d.text((50, 940), "SAMPLE INVOICE - FAKE DATA FOR DEMO ONLY", font=font(18), fill="gray")

out = Path("sample_invoices") / "invoice_001.png"
out.parent.mkdir(exist_ok=True)
img.save(out)
print("Saved", out, "| subtotal", subtotal, "| vat", vat, "| total", grand)