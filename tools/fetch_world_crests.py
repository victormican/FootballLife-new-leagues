r"""python fetch_world_crests.py --world <pesdb dir> --crest-dir <symbol/flag>
                               [--go] [--limit N] [--only TEXT] [--catalog-dir <dir>]

Real club crests for the world, from footylogos.com, using the catalogue the user's NewLife
toolkit already keeps in `newlife-classics\data\cache\footylogos_<country>.json`.

The catalogue is one list of (club name, slug) per country; this tool indexes all of them by
normalised name and, for every club of `Team.bin` whose name is in it exactly once, downloads
`https://www.footylogos.com/dls/logo/<slug>.png` and writes the three sizes the game reads:

    e_<id6>_r.png      128x128 RGBA
    e_<id6>_r_l.png    256x256 RGBA
    e_<id6>_r_ll.png   512x512 RGBA

Cut to the alpha box, 4 % margin, LANCZOS, RGBA (the shape `mkcrests.py` writes).

    --dry (default) counts the matches; --go downloads and writes.
"""

import argparse
import json
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.request

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pesdb

T_REC, T_ID, T_NAME, T_NAME_LEN = 1532, 0x08, 0x170, 70
BASE = "https://www.footylogos.com/dls/logo/%s.png"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
CATALOG = r"C:\Users\viarm\test-carpeta\newlife-classics\data\cache"


def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()
    return " ".join("".join(c if c.isalnum() else " " for c in s.lower()).split())


def catalogs(folder):
    idx, clash = {}, set()
    for f in os.listdir(folder):
        if not (f.startswith("footylogos_") and f.endswith(".json")):
            continue
        with open(os.path.join(folder, f), encoding="utf-8") as fh:
            for item in json.load(fh):
                try:
                    name, slug = item
                except (TypeError, ValueError):
                    continue
                k = norm(name)
                if not k:
                    continue
                if k in idx and idx[k] != slug:
                    clash.add(k)
                idx[k] = slug
    for k in clash:
        idx.pop(k, None)
    return idx


def fetch(slug, timeout=30):
    req = urllib.request.Request(BASE % slug, headers=UA)
    return urllib.request.urlopen(req, timeout=timeout).read()


def prepare(data, side):
    im = Image.open(__import__("io").BytesIO(data)).convert("RGBA")
    box = im.getbbox()
    if box:
        im = im.crop(box)
    w, h = im.size
    m = int(max(w, h) * 0.04)
    canvas = Image.new("RGBA", (max(w, h) + 2 * m, max(w, h) + 2 * m), (0, 0, 0, 0))
    canvas.paste(im, ((canvas.width - w) // 2, (canvas.height - h) // 2), im)
    return canvas.resize((side, side), Image.LANCZOS)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--world", required=True)
    ap.add_argument("--crest-dir", required=True)
    ap.add_argument("--catalog-dir", default=CATALOG)
    ap.add_argument("--only", default="")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--min-id", type=int, default=71578)
    ap.add_argument("--go", action="store_true")
    a = ap.parse_args()

    idx = catalogs(a.catalog_dir)
    print("catalogue: %d names" % len(idx))

    with open(os.path.join(a.world, "Team.bin"), "rb") as f:
        raw = pesdb.wesys_unpack(f.read())
    clubs = []
    for o in range(0, len(raw) - T_REC + 1, T_REC):
        if raw[o + 0x53] & 0x80:
            continue
        tid = int.from_bytes(raw[o + T_ID : o + T_ID + 4], "little")
        name = (
            bytes(raw[o + T_NAME : o + T_NAME + T_NAME_LEN])
            .split(b"\0")[0]
            .decode("utf-8", "replace")
        )
        clubs.append((tid, name))

    hits = [(t, n, idx[norm(n)]) for t, n in clubs if t >= a.min_id and norm(n) in idx]
    if a.only:
        hits = [h for h in hits if a.only.lower() in h[1].lower()]
    if a.limit:
        hits = hits[: a.limit]
    print("clubs: %d, with a real crest in the catalogue: %d" % (len(clubs), len(hits)))
    for t, n, s in hits[:10]:
        print("   %6d %-40s %s" % (t, n[:40], s))
    if not a.go:
        print("dry run: nothing downloaded (pass --go)")
        return

    ok = failed = 0
    for k, (tid, name, slug) in enumerate(hits, 1):
        try:
            data = fetch(slug)
        except (urllib.error.HTTPError, urllib.error.URLError, OSError) as e:
            failed += 1
            print("   %6d %-38s FALLO %s" % (tid, name[:38], e))
            continue
        for side, suffix in ((128, "_r"), (256, "_r_l"), (512, "_r_ll")):
            prepare(data, side).save(
                os.path.join(a.crest_dir, "e_%06d%s.png" % (tid, suffix))
            )
        ok += 1
        if k % 50 == 0:
            print("   %d/%d" % (k, len(hits)))
        time.sleep(0.15)
    print("crests written: %d, failed: %d" % (ok, failed))


if __name__ == "__main__":
    main()
