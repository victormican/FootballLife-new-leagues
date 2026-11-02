r"""mkcountryflag.py -- a country's flag in the game's own format, for the countries the game has no
texture for.

How the game finds a flag
  The flag id of a country is the value in bits 10-18 of the first dword of its Country.bin row
  (`(u32(row) >> 10) & 0x1FF`).  The engine builds the path the same way for every country:

      common/render/symbol/flag/flag_%03d.png       128 square, lists and small headings
      common/render/symbol/flag/flag_%03d_l.png    256 square, the usual picture
      common/render/symbol/flag/flag_%03d_ll.png   512 square, the big one

  read from the livecpk roots, then from `Data/dt15_x64.cpk`, whose 214 flags are named exactly
  that way (`flag_001.png`, `flag_096.png`).  The format of the three digits is not cosmetic: a
  file called `flag_96.png` is never asked for, so a country below 100 whose art is stored that
  way shows nothing.  (The exe keeps the pieces of that path side by side at 0x027c0a70:
  `cpk_dat/common/render/`, `symbol/flag/`, `flag_`, `e_`, `_l`, `_ll`, `_w_l`, ...)

What a flag file looks like
  Measured off the shipped ones: a white square with a grey (222,222,222) frame from (2,40) to
  (253,215) and the flag filling (10,48)-(245,207) -- 236 x 160, stretched to that box, not
  letterboxed.  All three sizes are the same drawing at 128, 256 and 512.

What it does
  Takes plain flag pictures (`<from>/flag_<id>.png`, any size, the id only tells which country)
  and writes the three files of the game's format for each id into
  `<root>/common/render/symbol/flag/`.  With `--check` it only reports: which country of the
  world's Country.bin has no texture in the roots (`--root`, `--also`) nor in the game's CPKs
  (`--game`), and which files are named in a way the engine will never ask for.

    python mkcountryflag.py --root <world livecpk root> --from sider/flags --ids 96,97,99
    python mkcountryflag.py --root <world livecpk root> --check --game <game folder>
"""

import glob
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pesdb

FLAGS = "common/render/symbol/flag"
SIZES = ((128, ""), (256, "_l"), (512, "_ll"))
COUNTRY_REC, COUNTRY_EN = 1420, 288
COUNTRY_COLS = list(range(148, COUNTRY_REC - 69, 70))

# the drawing of a shipped flag, in the 256 square: frame box, then the flag inside it
FRAME = (2, 40, 252, 176)
INSET = (10, 48, 236, 160)
WHITE, GREY = (255, 255, 255), (222, 222, 222)


def country_ids(pesdb_dir):
    """[(row, flag id, name)] for every named row of Country.bin"""
    path = os.path.join(pesdb_dir, "Country.bin")
    if not os.path.exists(path):
        return None
    raw = pesdb.wesys_unpack(open(path, "rb").read())
    out = []
    for i in range(0, len(raw), COUNTRY_REC):
        row = raw[i : i + COUNTRY_REC]
        fid = (int.from_bytes(row[:4], "little") >> 10) & 0x1FF
        names = [pesdb.cstr(row[o : o + 70]).strip() for o in COUNTRY_COLS]
        names = [n for n in names if n]
        en = pesdb.cstr(row[COUNTRY_EN : COUNTRY_EN + 70]).strip()
        if names or en:
            out.append((i // COUNTRY_REC, fid, names[0] if names else en))
    return out


def tile(flag, size):
    """the game's square: white field, grey frame, the flag stretched inside"""
    from PIL import Image, ImageDraw

    s = size / 256.0
    x, y, w, h = (round(v * s) for v in FRAME)
    fx, fy, fw, fh = (round(v * s) for v in INSET)
    out = Image.new("RGB", (size, size), WHITE)
    ImageDraw.Draw(out).rectangle([x, y, x + w - 1, y + h - 1], fill=GREY)
    body = flag.convert("RGB").resize((fw, fh), Image.LANCZOS)
    out.paste(body, (fx, fy))
    return out


def write_flag(flag_path, root, fid):
    from PIL import Image

    flag = Image.open(flag_path)
    out_dir = os.path.join(root, *FLAGS.split("/"))
    os.makedirs(out_dir, exist_ok=True)
    written = []
    for size, suffix in SIZES:
        name = "flag_%03d%s.png" % (fid, suffix)
        im = tile(flag, size).quantize(colors=255, dither=Image.NONE)
        im.save(os.path.join(out_dir, name), optimize=True)
        written.append(name)
    return written


def find_flags(root):
    """{flag id: [file names]} in a root's flag folder"""
    d = os.path.join(root, *FLAGS.split("/"))
    out = {}
    if not os.path.isdir(d):
        return out
    for f in sorted(os.listdir(d)):
        if not f.startswith("flag_") or not f.endswith(".png"):
            continue
        stem = f[len("flag_") : -len(".png")]
        for suf in ("_ll", "_l"):
            if stem.endswith(suf):
                stem = stem[: -len(suf)]
                break
        if stem.isdigit():
            out.setdefault(int(stem), []).append(f)
    return out


def cpk_flags(game):
    """{flag id} the game ships: `common/render/symbol/flag/flag_%03d*.png` inside its CPKs"""
    import cpkread

    cpks = sorted(glob.glob(os.path.join(game, "download", "dt15*.cpk")))
    cpks += sorted(glob.glob(os.path.join(game, "Data", "dt15*.cpk")))
    ids = set()
    for c in cpks:
        try:
            names = cpkread.names(c)
        except (OSError, ValueError, KeyError, IndexError):
            continue
        for n in names:
            m = re.search(
                r"symbol/flag/flag_(\d+?)(?:_l{1,2})?\.png$", n.replace("\\", "/")
            )
            if m:
                ids.add(int(m.group(1)))
    return ids


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    a = sys.argv[1:]
    get = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    root = get("--root")
    if not root:
        print(__doc__)
        return 2
    check = "--check" in a
    src_dir = get("--from")
    ids = (
        [int(v) for v in get("--ids").split(",") if v.strip()] if get("--ids") else None
    )
    also = [a[i + 1] for i, v in enumerate(a) if v == "--also"]
    base = get("--base") or os.path.join(root, "common", "etc", "pesdb")

    if check:
        rows = country_ids(base)
        if rows is None:
            raise SystemExit("no Country.bin in %s" % base)
        roots = [root] + also
        have = {}
        for i, r in enumerate(roots):
            for fid, names in find_flags(r).items():
                have.setdefault(fid, (i, names))
        game = get("--game")
        shipped = cpk_flags(game) if game else set()
        if game:
            print("the game's CPKs ship %d flags" % len(shipped))
        missing, unpadded = [], []
        for row, fid, name in rows:
            if fid not in have:
                if fid in shipped:
                    continue
                missing.append((row, fid, name))
                continue
            i, names = have[fid]
            if i == 0 and "flag_%03d.png" % fid not in names:
                unpadded.append((fid, names))
        print("countries: %d, without texture: %d" % (len(rows), len(missing)))
        for row, fid, name in missing:
            print("  NO TEXTURE  row %-4d flag %-4d %s" % (row, fid, name))
        for fid, names in unpadded:
            print(
                "  WRONG NAME  flag %-4d %s -- the engine asks for flag_%03d.png"
                % (fid, ",".join(names), fid)
            )
        return 1 if (missing or unpadded) else 0

    if not src_dir or not ids:
        print("--from and --ids are needed to write flags")
        return 2
    for fid in ids:
        src = os.path.join(src_dir, "flag_%03d.png" % fid)
        if not os.path.exists(src):
            src = os.path.join(src_dir, "flag_%d.png" % fid)
        if not os.path.exists(src):
            print("  no source for flag %d in %s" % (fid, src_dir))
            continue
        print(
            "  flag %-4d <- %s: %s"
            % (fid, os.path.basename(src), ", ".join(write_flag(src, root, fid)))
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
