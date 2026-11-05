r"""python arg_d1.py --world <pesdb dir> --worldfile <fl26world.txt> [--slot N] [--dry]

List Argentina's first division in the world and put its clubs there.

What is wrong (measured 2026-11-04)
    The tables have it: competition 22 (ARGENTINA_D1_LEAGUE, region 17), regulation 30,
    type 4, 30 teams, and 26 real clubs in CompetitionEntry (Boca, River, Racing...).  The
    world file has no `league` line for it, so it has no Select Team slot, the modules do not
    date it, and its clubs are not listed under Argentina -- they fall to the game's
    "other clubs" groups.  Argentina's listed league is regulation 11 (cid 130), which is the
    Primera Nacional (Almagro, All Boys, Atlanta...) but carries tier=1.

What it does
    1. the regulation's team count is set to the number of entries it really has;
    2. a `league 30 cid=22 ...` line is written for the first division, on the first free
       slot, region 29 / country 144 (the world's Argentina), tier 1;
    3. the Primera Nacional's line becomes tier 2, so the two divisions are ordered;
    4. both copies of the world file (livecpk and modules) are written.

    --dry prints what it would write.
"""

import argparse
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pesdb

R_REC = 2352
R_ID, R_TEAMS, R_ROUNDS = 0x02, 0x0B, 0x10
NAME = "Liga Profesional de F\u00fatbol"


def load(d, n):
    with open(os.path.join(d, n), "rb") as f:
        return bytearray(pesdb.wesys_unpack(f.read()))


def entries(world, cid):
    raw = load(world, "CompetitionEntry.bin")
    return [
        (raw[o + 9], int.from_bytes(raw[o : o + 4], "little"), o)
        for o in range(0, len(raw) - 11, 12)
        if (raw[o + 8] | (raw[o + 0x0B] << 8)) == cid
    ]


def free_slot(worldfile):
    used = set()
    with open(worldfile, encoding="utf-8", errors="replace") as f:
        for line in f:
            if line.startswith("league "):
                for tok in line.split():
                    if tok.startswith("slot="):
                        v = int(tok[5:])
                        if v > 0:
                            used.add(v)
    # above the game's own 123 slots first: those are certainly ours
    for s in range(250, 199, -1):
        if s not in used and s != 123:
            return s
    for s in range(22, 251):
        if s not in used and s != 123:
            return s
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--world", required=True)
    ap.add_argument("--worldfile", required=True)
    ap.add_argument("--slot", type=int, default=0)
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()

    ents = entries(a.world, 22)
    n = len(ents)
    print("cid 22 (Argentina D1): %d clubs in CompetitionEntry" % n)
    if n < 2:
        raise SystemExit("no entries for cid 22: nothing to list")

    slot = a.slot or free_slot(a.worldfile)
    print("slot: %d" % slot)

    regs = load(a.world, "CompetitionRegulation.bin")
    at = None
    for o in range(0, len(regs) - R_REC + 1, R_REC):
        if int.from_bytes(regs[o + R_ID : o + R_ID + 2], "little") == 30:
            at = o
            break
    if at is None:
        raise SystemExit("regulation 30 not found")
    was = regs[at + R_TEAMS] & 0x3F
    regs[at + R_TEAMS] = (regs[at + R_TEAMS] & 0xC0) | (n & 0x3F)
    print("regulation 30: teams %d -> %d" % (was, n))

    d1 = (
        "league 30 cid=22 region=29 country=144 conf=4 slot=%d tier=1 promote=0 demote=2 "
        "clubs=%d legs=2 kickoff=99 name=%s" % (slot, n, NAME)
    )

    lines = open(a.worldfile, encoding="utf-8", errors="replace").read().splitlines()
    out, put, fixed = [], False, False
    for line in lines:
        if line.startswith("league 11 "):
            out.append(
                "league 11 cid=130 region=29 country=144 conf=4 slot=28 tier=2 "
                "promote=2 demote=2 clubs=24 legs=2 kickoff=99 "
                "name=Argentine Second Division"
            )
            if line != out[-1]:
                fixed = True
            out.append(d1)
            put = True
            continue
        if line.startswith("league 30 "):
            continue
        out.append(line)
    if not put:
        out.append(d1)
    text = "\n".join(out) + "\n"
    print(
        "world file: first division %s, Primera Nacional tier 2 %s"
        % ("added" if put else "appended", "updated" if fixed else "already")
    )
    print(d1)

    if a.dry:
        print("dry run: nothing written")
        return

    for n_file in ("CompetitionRegulation.bin",):
        src = os.path.join(a.world, n_file)
        dst = src + ".before-argd1"
        if not os.path.exists(dst):
            shutil.copy2(src, dst)
    with open(os.path.join(a.world, "CompetitionRegulation.bin"), "wb") as f:
        f.write(pesdb.wesys_pack(bytes(regs)))
    dst = a.worldfile + ".before-argd1"
    if not os.path.exists(dst):
        shutil.copy2(a.worldfile, dst)
    with open(a.worldfile, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    live = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(a.world)))),
        "fl26world.txt",
    )
    if os.path.isdir(os.path.dirname(live)) and os.path.abspath(
        live
    ) != os.path.abspath(a.worldfile):
        with open(live, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        print("written to livecpk and modules")
    print("done")


if __name__ == "__main__":
    main()
