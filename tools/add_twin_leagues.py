"""python add_twin_leagues.py --base <world pesdb> --worldfile <fl26world.txt>
                            [--from-reg 336] [--reg 379] [--slot 183] [--count 5] [--dry]

Fill the last Select Team slots with *twin* leagues: a new regulation row that copies an
existing generic league (its competition id and its clubs) and only changes the regulation id,
the name and the Select Team slot.  No competition row, no entry row, no club and no player is
added, so the world stays inside the 255 competition ids.

Use it while the competition id is still one byte: the Select Team list is built per regulation
id (fl26comptab appends a parameter row for it) and fl26clubs answers the slot's clubs from the
world line, so a twin shows up and plays exactly like the league it copies.  In Master League
the two regulations share one competition object; that is the thing to watch in the first game.
"""

import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pesdb
import mkleague as M


def main():
    a = sys.argv[1:]
    get = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    base, wf = get("--base"), get("--worldfile")
    if not base or not wf:
        print(__doc__)
        return 1
    reg0 = int(get("--reg", "379"))
    src0 = int(get("--from-reg", "336"))
    slot0 = int(get("--slot", "183"))
    count = int(get("--count", "5"))
    dry = "--dry" in a

    regs = bytearray(M.load(base, "CompetitionRegulation.bin"))
    by_id = {
        int.from_bytes(regs[i + M.R_ID : i + M.R_ID + 2], "little"): i
        for i in range(0, len(regs), M.REG)
    }
    taken = [reg0 + k for k in range(count) if reg0 + k in by_id]
    if taken:
        print("regulation id(s) already used: %s" % taken)
        return 1

    lines = []
    for k in range(count):
        rid, src = reg0 + k, src0 + k
        if src not in by_id:
            print("no regulation %d to copy" % src)
            return 1
        g = bytearray(regs[by_id[src] : by_id[src] + M.REG])
        cid = g[M.R_CID]
        name = "Generic League %02d" % (63 + k)
        g[M.R_ID : M.R_ID + 2] = rid.to_bytes(2, "little")
        M.put_names(g, 0, name)
        M.set_tier(g, 1)
        regs += g
        slot = slot0 + k
        line = (
            "league %d cid=%d region=29 country=200 conf=2 slot=%d tier=1 promote=0 "
            "demote=0 clubs=10 legs=2 kickoff=99 name=%s" % (rid, cid, slot, name)
        )
        lines.append(line)
        print(
            "  %s: reg %d copies %d (cid %d) on slot %d" % (name, rid, src, cid, slot)
        )

    if dry:
        print("dry run: nothing written")
        return 0
    open(os.path.join(base, "CompetitionRegulation.bin"), "wb").write(
        pesdb.wesys_pack(bytes(regs))
    )
    s = io.open(wf, encoding="utf-8", errors="replace").read()
    s = s.rstrip("\n") + "\n" + "\n".join(lines) + "\n"
    io.open(wf, "w", encoding="utf-8", newline="\n").write(s)
    print("added %d twin regulations %d..%d" % (count, reg0, reg0 + count - 1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
