"""python fix_team_names.py --base <pesdb dir> [--ref <Team.bin> ...] [--check] [--dry]

Repair the three-letter code at +0x372 of Team.bin after the club-name writers clobbered it.

Why the code breaks
  A team row keeps its localised names in a grid of 70-byte slots that starts at 0x90 (the text of
  each slot is at +0x0E, so slot 3 is the canonical name at 0x170).  Slot 10 (0x34C) is the odd one:
  its text is only 24 bytes, and right after it come the three-letter code at +0x26 (0x372) and a
  long name at +0x30 (0x37C).

  A writer that pours a 30-character name into every one of the twenty slots therefore writes the
  name's own tail over the code ("Other European Leagues Club 01" leaves "lub 01" there).  The game
  copies that field with strcpy_s(dst, 4, src) when the world is loaded, and a source of four or
  more characters aborts the process with 0xc0000409 (FAST_FAIL_INVALID_ARG).  That is the crash at
  ~28 s with _FL26MyWorld; a world whose codes are three characters never reaches it.

What it does
  For every row whose code is not a sane three-character code -- empty, longer than three, or equal
  to the tail of its own name at that offset -- it puts a three-character code back:

    1. the code of the same team id in a reference Team.bin (`--ref`, any number, first hit wins)
    2. the row's own code, when it is already sane
    3. a code derived from the name ("Other Clubs (Africa) Club 07" -> "OCA", then a free one)

  Nothing else of the row is touched: the name at 0x170 and the localised slots stay as they are.

Exit status is 0 when the file was (or already is) sane, 1 when `--check` finds a broken code.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pesdb

T_REC, T_ID = 1532, 0x08
T_NAME, T_NAME_LEN = 0x170, 70
T_ABBR, T_ABBR_LEN = 0x372, 3
SLOT10_TEXT = 0x35A  # the 24 bytes of slot 10 that come before the code
SLOT10_NAME = 0x37C  # the long name that follows the code


def cstr(b):
    return b.split(b"\0")[0]


def row_code(raw, o):
    return bytes(raw[o + T_ABBR : o + T_ABBR + 4])


def sane(code):
    """at most three printable ASCII characters, then a NUL -- the game copies it into 4 bytes"""
    z = code.find(b"\0")
    if z < 0 or z > 3:
        return False
    return all(0x21 <= c <= 0x7E for c in code[:z])


def is_name_tail(name, code):
    """the code is the piece of the name that fell on 0x372 (0x18 bytes into slot 10)"""
    if not code:
        return False
    return name[0x18 : 0x18 + len(code)] == code


def derive(name):
    """a three-character code from the name: the initials of its words, then the first letters"""
    words = [w for w in name.replace("(", " ").replace(")", " ").split() if w]
    letters = [w[0] for w in words if w[0].isalnum()]
    out = "".join(letters[:3]).upper()
    if len(out) < 3:
        out += "".join(c for c in name.upper() if c.isalnum())[: 3 - len(out)]
    return (out + "XXX")[:3]


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    a = sys.argv[1:]
    get = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    base = get("--base")
    if not base:
        print(__doc__)
        return 2
    check = "--check" in a
    dry = "--dry" in a
    refs = [a[i + 1] for i, v in enumerate(a) if v == "--ref"]

    path = os.path.join(base, "Team.bin")
    raw = bytearray(pesdb.wesys_unpack(open(path, "rb").read()))

    ref_code = {}
    for r in refs:
        table = pesdb.wesys_unpack(open(r, "rb").read())
        for i in range(0, len(table), T_REC):
            tid = int.from_bytes(table[i + T_ID : i + T_ID + 4], "little")
            code = row_code(table, i)
            if tid not in ref_code and sane(code):
                ref_code[tid] = code.split(b"\0")[0]
        print("reference %s: %d codes" % (os.path.basename(r), len(ref_code)))

    taken = {
        row_code(raw, i).split(b"\0")[0]
        for i in range(0, len(raw), T_REC)
        if sane(row_code(raw, i))
    }

    broken, fixed = [], 0
    for i in range(0, len(raw), T_REC):
        tid = int.from_bytes(raw[i + T_ID : i + T_ID + 4], "little")
        raw_name = cstr(raw[i + T_NAME : i + T_NAME + T_NAME_LEN])
        name = raw_name.decode("utf-8", "replace")
        code = row_code(raw, i)
        text = code.split(b"\0")[0]
        bad = (not sane(code)) or (bool(text) and is_name_tail(raw_name, text))
        if not bad:
            continue
        broken.append((tid, name, text))

        new = ref_code.get(tid)
        if new is None or is_name_tail(raw_name, new):
            new = None
            candidate = derive(name).encode("ascii")
            for k in range(1000):
                c = (
                    candidate
                    if k == 0
                    else ("%s%02d" % (candidate[:1], k % 100))[:3].encode("ascii")
                )
                if c not in taken:
                    new = c
                    break
            if new is None:
                new = b"ZZZ"
        taken.add(new)
        if not dry:
            raw[i + T_ABBR : i + T_ABBR + 4] = new.ljust(4, b"\0")
        fixed += 1

    print("rows: %d, broken codes: %d" % (len(raw) // T_REC, len(broken)))
    for tid, name, code in broken[:20]:
        print("  team %-6d %-38s was %r" % (tid, name[:38], code.decode("latin-1")))
    if len(broken) > 20:
        print("  ... and %d more" % (len(broken) - 20))

    if check:
        return 1 if broken else 0

    if dry:
        print("dry run: nothing written")
        return 0

    tmp = path + ".tmp"
    open(tmp, "wb").write(pesdb.wesys_pack(bytes(raw)))
    os.replace(tmp, path)
    print("repaired %d codes in %s" % (fixed, path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
