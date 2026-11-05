r"""python fix_team_codes.py --world <pesdb dir> [--go]

Give a three-letter code to the clubs that have none.

`Team.bin +0x372` holds the short name the scoreboard, the fixture list and the tables copy
(`check_world` reads it).  A club with nothing there shows a blank or a broken short name in
those screens.  This world had 73, all of them placeholders of the cups and the "Other clubs"
groups.

The code is built from the name: the first letter of each of its first three words, or the first
three letters of a single word, upper-cased and kept to A-Z.

    --go writes Team.bin (backup Team.bin.before-codes); without it, a dry run.
"""

import argparse
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pesdb

T_REC, T_ID, T_ABBR, T_ABBR_LEN, T_NAME = 1532, 0x08, 0x372, 4, 0x170


def load(d, n):
    with open(os.path.join(d, n), "rb") as f:
        return bytearray(pesdb.wesys_unpack(f.read()))


def code_of(name):
    words = [
        w
        for w in "".join(c if c.isalnum() or c == " " else " " for c in name).split()
        if w
    ]
    if not words:
        return ""
    if len(words) >= 3:
        out = "".join(w[0] for w in words[:3])
    else:
        out = "".join(words)[:3]
    return "".join(c for c in out.upper() if "A" <= c <= "Z")[:3]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--world", required=True)
    ap.add_argument("--go", action="store_true")
    a = ap.parse_args()

    teams = load(a.world, "Team.bin")
    fixed = []
    for i in range(len(teams) // T_REC):
        o = i * T_REC
        have = bytes(teams[o + T_ABBR : o + T_ABBR + T_ABBR_LEN]).split(b"\0")[0]
        if len(have) >= 2 and all(32 <= b < 127 for b in have):
            continue
        name = (
            bytes(teams[o + T_NAME : o + T_NAME + 70])
            .split(b"\0")[0]
            .decode("utf-8", "replace")
        )
        code = code_of(name)
        if len(code) < 2:
            continue
        tid = int.from_bytes(teams[o + T_ID : o + T_ID + 4], "little")
        teams[o + T_ABBR : o + T_ABBR + T_ABBR_LEN] = code.encode().ljust(
            T_ABBR_LEN, b"\0"
        )
        fixed.append((tid, name, code))

    print("clubs without a code: %d" % len(fixed))
    for tid, name, code in fixed[:12]:
        print("   %6d %-38s -> %s" % (tid, name[:38], code))
    if len(fixed) > 12:
        print("   ... y %d mas" % (len(fixed) - 12))
    if not a.go:
        print("dry run: nothing written (pass --go)")
        return
    dst = os.path.join(a.world, "Team.bin.before-codes")
    if not os.path.exists(dst):
        shutil.copy2(os.path.join(a.world, "Team.bin"), dst)
    with open(os.path.join(a.world, "Team.bin"), "wb") as f:
        f.write(pesdb.wesys_pack(bytes(teams)))
    print("written (backup Team.bin.before-codes)")


if __name__ == "__main__":
    main()
