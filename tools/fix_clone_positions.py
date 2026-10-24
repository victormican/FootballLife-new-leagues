"""python fix_clone_positions.py --base <world pesdb> [--dry]

The players the growth tools added to a club were copies of the squad's first player, the
goalkeeper: a club of thirty ended with nineteen goalkeepers and the rest "PT" in the menus.

This looks for a **reference squad** (the first club with 25 or more players and at least four
different positions) and, for every club with more than two goalkeepers, rewrites the extra
goalkeepers from that squad in rotation -- record by record, keeping each player's id and name,
so assignments, squads and the Edit data stay as they are.

It only moves positions and ratings, which is what the menus show.
"""

import os
import sys

HERE = os.path.dirname(__file__)
sys.path.insert(0, HERE)
import pesdb
import playeredit as E

A_REC, A_PID, A_TID = 16, 0x04, 0x08
GK = 0


def main():
    a = sys.argv[1:]
    get = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    base = get("--base")
    if not base:
        print(__doc__)
        return 1
    dry = "--dry" in a

    players = bytearray(
        pesdb.wesys_unpack(open(os.path.join(base, "Player.bin"), "rb").read())
    )
    assigns = pesdb.wesys_unpack(
        open(os.path.join(base, "PlayerAssignment.bin"), "rb").read()
    )
    off = {
        int.from_bytes(players[i + E.P_ID : i + E.P_ID + 4], "little"): i
        for i in range(0, len(players), E.P_REC)
    }
    by = {}
    for i in range(0, len(assigns), A_REC):
        by.setdefault(
            int.from_bytes(assigns[i + A_TID : i + A_TID + 4], "little"), []
        ).append(int.from_bytes(assigns[i + A_PID : i + A_PID + 4], "little"))

    def pos(pid):
        o = off[pid]
        return E.getf(players[o : o + E.P_REC], "Registered Position")

    ref = None
    for tid, pids in by.items():
        pids = [p for p in pids if p in off]
        if len(pids) >= 25 and len({pos(p) for p in pids}) >= 4:
            ref = pids
            break
    if ref is None:
        print("no reference squad (25 players, four positions) -- nothing done")
        return 1
    print(
        "reference squad: %d players, positions %s"
        % (len(ref), sorted({pos(p) for p in ref}))
    )

    fixed = 0
    for tid, pids in by.items():
        pids = [p for p in pids if p in off]
        gks = [p for p in pids if pos(p) == GK]
        if len(gks) <= 2:
            continue
        for k, pid in enumerate(gks[2:]):
            src = off[ref[k % len(ref)]]
            dst = off[pid]
            rec = bytearray(players[src : src + E.P_REC])
            rec[E.P_ID : E.P_ID + 4] = pid.to_bytes(4, "little")
            nm = players[
                dst + E.P_NAME : dst + E.P_NAME + E.P_NAME_LEN * E.P_NAME_SLOTS
            ]
            rec[E.P_NAME : E.P_NAME + E.P_NAME_LEN * E.P_NAME_SLOTS] = nm
            players[dst : dst + E.P_REC] = rec
            fixed += 1

    print("%d extra goalkeeper(s) rewritten from the reference squad" % fixed)
    if dry:
        print("dry run: nothing written")
        return 0
    open(os.path.join(base, "Player.bin"), "wb").write(pesdb.wesys_pack(bytes(players)))
    print("written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
