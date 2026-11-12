import os

from PIL import Image, ImageDraw, ImageFont

OUT = r"D:\SP Football Life 2026 - copia\SiderAddons\livecpk\_FL26Sud\common\render\symbol\flag"
os.makedirs(OUT, exist_ok=True)

# (flag id, initials, background RGB)
PLACEHOLDERS = [
    (185, "AGR", (0x1E, 0x6B, 0x38)),  # AGRO PONTINO  green
    (187, "CHA", (0x00, 0x7F, 0x7F)),  # CHAMERIA      teal
    (188, "CUM", (0x1F, 0x3A, 0x8C)),  # CUMANN        blue
    (255, "GIR", (0xC2, 0x18, 0x5B)),  # GIRL POWER    magenta
    (270, "INA", (0xE6, 0x6E, 0x00)),  # INDIGENOUS    orange
]

try:
    FONT = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 78)
except Exception:
    FONT = ImageFont.load_default()

for cid, code, rgb in PLACEHOLDERS:
    img = Image.new("RGBA", (256, 256), rgb + (255,))
    d = ImageDraw.Draw(img)
    bbox = d.textbbox((0, 0), code, font=FONT)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    d.text(
        ((256 - w) / 2 - bbox[0], (256 - h) / 2 - bbox[1]),
        code,
        font=FONT,
        fill=(255, 255, 255, 255),
    )
    path = os.path.join(OUT, "flag_%d.png" % cid)
    img.save(path)
    print("flag_%d.png" % cid, code)
