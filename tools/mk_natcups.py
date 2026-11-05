r"""python mk_natcups.py --world <pesdb dir> --worldfile <fl26world.txt> [--go] [--dry]

Put the national-team competitions that only exist as rows into Kick Off > Cup.

Two competitions of the world have their entries (national teams) and their regulation but no
`ccup` line, so the Cup menu never shows them:

    cid 91   reg 196  type 3 (knockout)  12 national teams   "Oceania"
    cid 255  reg 255  type 3 (knockout)   8 national teams   "Selecciones No FIFA"

They are the same kind of thing as Europe's national competitions, so they are not leagues and
must not be listed as one: this tool only writes the cup lines (it refuses if a `league` line
names either competition).  The clubs of a national team are its national team ids, passed as
`entry=0:<team>,...` like the World Cup line does.

    --dry (default) prints the lines; --go writes both copies of the world file, after copying
    it to fl26world.txt.before-natcups.
"""

import argparse
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pesdb

WANT = {
    91: "Oceania",
    255: "Selecciones No FIFA",
}
DAYS = "20,27,34,41"
LIKE = 23  # the FA Cup's shape: one match a round, byes for any size


def load(d, n):
    with open(os.path.join(d, n), "rb") as f:
        return bytearray(pesdb.wesys_unpack(f.read()))


def cstr(b):
    return bytes(b).split(b"\0")[0].decode("utf-8", "replace").strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--world", required=True)
    ap.add_argument("--worldfile", required=True)
    ap.add_argument("--go", action="store_true")
    a = ap.parse_args()

    ents = load(a.world, "CompetitionEntry.bin")
    regs = load(a.world, "CompetitionRegulation.bin")
    reg_of = {}
    for o in range(0, len(regs) - 2351, 2352):
        cid = regs[o + 8] | (regs[o + 0x492] << 8)
        if regs[o + 9] == 3 and cid in WANT:
            reg_of[cid] = int.from_bytes(regs[o + 2 : o + 4], "little")
    teams, order = {}, {}
    for o in range(0, len(ents) - 11, 12):
        cid = ents[o + 8] | (ents[o + 0x0B] << 8)
        if cid in WANT:
            teams.setdefault(cid, {})[ents[o + 9]] = int.from_bytes(
                ents[o : o + 4], "little"
            )
            order.setdefault(cid, []).append(
                (ents[o + 9], int.from_bytes(ents[o : o + 4], "little"))
            )

    lines = open(a.worldfile, encoding="utf-8", errors="replace").read().splitlines()
    leagues = {
        int(m.group(1))
        for l in lines
        if l.startswith("league ")
        for m in [re.search(r"\bcid=(\d+)", l)]
        if m
    }
    have = set()
    for l in lines:
        if l.startswith("ccup "):
            m = re.search(r"\bcid=(\d+)", l)
            if m:
                have.add(int(m.group(1)))

    new = []
    for cid, name in WANT.items():
        if cid in leagues:
            raise SystemExit(
                "competition %d is a league in the world file: it must not be" % cid
            )
        if cid in have:
            print("  %-22s already in the Cup menu" % name)
            continue
        if cid not in reg_of:
            raise SystemExit("no knockout regulation for competition %d" % cid)
        ids = [t for _p, t in sorted(order.get(cid, []))]
        if len(ids) < 2:
            raise SystemExit("competition %d has %d entries" % (cid, len(ids)))
        entry = ",".join("0:%d" % t for t in ids)
        line = (
            "ccup %d ko=%d groups=0 entry=%s cid=%d fill=%d national=1 days=%s like=%d "
            "name=%s"
            % (reg_of[cid], reg_of[cid], entry, cid, len(ids), DAYS, LIKE, name)
        )
        new.append(line)
        print(
            "  %-22s cid %-4d reg %-4d %2d national teams"
            % (name, cid, reg_of[cid], len(ids))
        )

    if not new:
        print("nothing to do")
        return
    body = [l for l in lines if l.startswith("ccup ") and re.search(r"\bname=", l)]
    body += new
    body.sort(key=lambda l: (l.split("name=", 1)[-1].strip().lower(), l))
    rest = [l for l in lines if not l.startswith("ccup ")]
    first = next((i for i, l in enumerate(lines) if l.startswith("ccup ")), len(lines))
    out = rest[:first] + body + rest[first:]
    text = "\n".join(out) + "\n"
    print("cups after: %d" % len(body))
    if not a.go:
        print("dry run: nothing written (pass --go)")
        return
    dst = a.worldfile + ".before-natcups"
    if not os.path.exists(dst):
        shutil.copy2(a.worldfile, dst)
    with open(a.worldfile, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    live = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(a.world)))),
        "fl26world.txt",
    )
    if os.path.abspath(live) != os.path.abspath(a.worldfile):
        with open(live, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
    print("written (livecpk and modules)")


if __name__ == "__main__":
    main()
