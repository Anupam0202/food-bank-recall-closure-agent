from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "app/static/fixtures"
OUT.mkdir(parents=True, exist_ok=True)

def font(size, bold=False):
    candidates = [
        "/usr/share/fonts/msttcorefonts/Arial_Bold.ttf" if bold else "/usr/share/fonts/msttcorefonts/Arial.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    for p in candidates:
        if Path(p).exists(): return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def make(name, brand, product, upc, lot, color):
    img = Image.new("RGB", (900, 560), "#f9f8f7")
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((55,45,845,515), 28, fill="white", outline="#d8d5d1", width=4)
    d.rectangle((55,45,845,150), fill=color)
    d.text((92,76), brand, fill="white", font=font(40, True))
    d.text((92,190), product, fill="#2c2c2b", font=font(36, True))
    d.text((92,260), "DEMONSTRATION PACKAGE — NOT FOR SALE", fill="#7d7a75", font=font(20))
    d.text((92,335), f"UPC  {upc}", fill="#2c2c2b", font=font(27))
    d.text((92,390), f"LOT  {lot}", fill="#2c2c2b", font=font(27, True))
    d.text((92,455), "Synthetic data", fill="#7d7a75", font=font(18))
    img.save(OUT/name)

make("exact-package.png", "HARVEST TABLE", "Oat Bites · 12 oz", "012345678905", "HT2409A", "#2783de")
make("ambiguous-package.png", "HARVEST TABLE", "Snack Bites · assorted", "012345678905", "SMUDGED / MISSING", "#d5803b")
make("control-package.png", "MEADOW PANTRY", "Rice Crackers · 8 oz", "099999111112", "MP0512", "#46a171")
print(f"Generated fixtures in {OUT}")
