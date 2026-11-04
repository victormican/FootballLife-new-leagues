"""python move_cids.py --base <pesdb> --worldfile <fl26world.txt> --map 258:301,259:302 [--dry]

Move a competition of ours to another id, in all four places that carry it.

Why: the Select Team census and the emblem lookup of the exe read the competition id as a
**byte** (fl26cid16 only widens the list builder). A league with cid 265 therefore lands in the
node of competition 9 -- the Premier League -- and its slot lists the 20 clubs of the Premier
League. Measured 2026-11-04: Yokary (265) showed the Premier League, Austria (266) Serie A,
Russian First (261) the Libertadores, and so on.

A cid above 255 can only own its club list when no shipped competition with clubs shares its low
byte. `--free` prints those bytes from the world that is being read; the twelve of 2026-11-04 are
1, 37, 45, 46, 47, 70, 71, 72, 86, 97, 103, 227.

What is rewritten: Competition.bin +0x05/+0x07, CompetitionRegulation.bin +0x08/+0x492,
CompetitionEntry.bin +0x08/+0x0b and the `cid=` of the league's line in the world file. Slot,
regulation id, region, entries and clubs stay as they are.
"""

import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pesdb

COMP, REG, ENT = 36, 2352, 12
C_CID, C_CID_HI = 0x05, 0x07
R_CID, R_CID_HI = 0x08, 0x492
E_CID, E_CID_HI = 0x08, 0x0B


def load(base, name):
    return bytearray(pesdb.wesys_unpack(open(os.path.join(base, name), "rb").read()))


def save(base, name, raw):
    open(os.path.join(base, name), "wb").write(pesdb.wesys_pack(bytes(raw)))


def free_bytes(base):
    ents = load(base, "CompetitionEntry.bin")
    comp = load(base, "Competition.bin")
    with_clubs = {
        ents[i + E_CID] | (ents[i + E_CID_HI] << 8) for i in range(0, len(ents), ENT)
    }
    taken = {
        (comp[i + C_CID] | (comp[i + C_CID_HI] << 8)) & 0xFF
        for i in range(0, len(comp), COMP)
    }
    return [b for b in range(1, 256) if b not in with_clubs and b in taken]


def main():
    a = sys.argv[1:]
    get = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    base, wf = get("--base"), get("--worldfile")
    if not base or not wf:
        print(__doc__)
        return 1
    if "--free" in a:
        print("bytes bajos sin clubes: " + ", ".join(str(b) for b in free_bytes(base)))
        return 0
    mp = get("--map")
    if not mp:
        print(__doc__)
        return 1
    dry = "--dry" in a
    pairs = []
    for item in mp.replace(",", " ").split():
        old, new = (int(x) for x in item.split(":"))
        if old in (256,) or new >= 512:
            print("cid %d: 256 is forbidden and ids must stay under 512" % old)
            return 2
        pairs.append((old, new))

    comp = load(base, "Competition.bin")
    regs = load(base, "CompetitionRegulation.bin")
    ents = load(base, "CompetitionEntry.bin")
    lines = io.open(wf, encoding="utf-8", errors="replace").read().splitlines()

    have = {
        regs[i + R_CID] | (regs[i + R_CID_HI] << 8) for i in range(0, len(regs), REG)
    }
    for old, new in pairs:
        if old not in have:
            print("cid %d is not in CompetitionRegulation.bin" % old)
            return 2
        if new in have:
            print("cid %d is taken" % new)
            return 2

    for old, new in pairs:
        lo, hi = new & 0xFF, (new >> 8) & 0xFF
        n_c = n_r = n_e = 0
        for i in range(0, len(comp), COMP):
            if comp[i + C_CID] | (comp[i + C_CID_HI] << 8) == old:
                comp[i + C_CID], comp[i + C_CID_HI] = lo, hi
                n_c += 1
        for i in range(0, len(regs), REG):
            if regs[i + R_CID] | (regs[i + R_CID_HI] << 8) == old:
                regs[i + R_CID], regs[i + R_CID_HI] = lo, hi
                n_r += 1
        for i in range(0, len(ents), ENT):
            if ents[i + E_CID] | (ents[i + E_CID_HI] << 8) == old:
                ents[i + E_CID], ents[i + E_CID_HI] = lo, hi
                n_e += 1
        hit = 0
        for i, l in enumerate(lines):
            if not l.startswith("league "):
                continue
            kv = l.split()
            if "cid=%d" % old in kv:
                lines[i] = l.replace("cid=%d" % old, "cid=%d" % new, 1)
                hit += 1
        print(
            "cid %d -> %d: %d competencia(s), %d regulacion(es), %d entrada(s), %d linea(s)"
            % (old, new, n_c, n_r, n_e, hit)
        )
        if n_c != 1 or n_r < 1 or hit < 1:
            print(
                "  unexpected: a league needs exactly one competition row and one world line"
            )
            return 2

    if dry:
        print("dry run: nothing written")
        return 0
    save(base, "Competition.bin", comp)
    save(base, "CompetitionRegulation.bin", regs)
    save(base, "CompetitionEntry.bin", ents)
    io.open(wf, "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
    print("written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
