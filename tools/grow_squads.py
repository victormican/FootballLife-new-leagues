"""python grow_squads.py --base <world pesdb> --worldfile <fl26world.txt>
                        [--squad 30] [--limit 0] [--dry]

Give every club of the world's leagues `--squad` players, if it has fewer.

Why it can: a club's squad is its PlayerAssignment rows, and every player is a Player.bin
record with an id `playeredit.free_ids` hands out. Nothing about the competition or the
calendar depends on the number of players a club has, so this is data only; the wall that
matters is the player cap (the block's array, 123,825, and the menu indexes that
`fl26playercap.lua` guards).

The added players are clones of the club's own first player, named "<club> Player NN", with the
club's nationality, so a squad reads as one side.
"""

import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pesdb
import playeredit as E
import mkleague as M

A_REC, A_EID, A_PID, A_TID = 16, 0x00, 0x04, 0x08
T_REC, T_ID, T_COUNTRY = 1532, 0x08, 0x46


def main():
    a = sys.argv[1:]
    get = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    base, wf = get("--base"), get("--worldfile")
    if not base or not wf:
        print(__doc__)
        return 1
    want = int(get("--squad", "30"))
    limit = int(get("--limit", "0"))
    dry = "--dry" in a

    raw = pesdb.wesys_unpack(open(os.path.join(base, "Team.bin"), "rb").read())
    players = bytearray(
        pesdb.wesys_unpack(open(os.path.join(base, "Player.bin"), "rb").read())
    )
    assigns = bytearray(
        pesdb.wesys_unpack(
            open(os.path.join(base, "PlayerAssignment.bin"), "rb").read()
        )
    )
    ents = M.load(base, "CompetitionEntry.bin")

    # every club the world's leagues play with, and how many players each has
    league_cids = set()
    for line in io.open(wf, encoding="utf-8", errors="replace").read().splitlines():
        w = line.split()
        if w and w[0] == "league":
            kv = dict(x.split("=", 1) for x in w[2:] if "=" in x)
            if kv.get("cid"):
                league_cids.add(int(kv["cid"]))
    clubs = {
        int.from_bytes(ents[i : i + 4], "little")
        for i in range(0, len(ents), M.ENT)
        if ents[i + M.E_CID] in league_cids
    }
    clubs = {c for c in clubs if c}

    per_team = {}
    for i in range(0, len(assigns), A_REC):
        per_team.setdefault(
            int.from_bytes(assigns[i + A_TID : i + A_TID + 4], "little"), []
        ).append(i)

    country, name = {}, {}
    for i in range(0, len(raw), T_REC):
        tid = int.from_bytes(raw[i + T_ID : i + T_ID + 4], "little")
        country[tid] = (
            int.from_bytes(raw[i + T_COUNTRY : i + T_COUNTRY + 2], "little") >> 2
        ) & 0x1FF
        name[tid] = (
            raw[i + 0x170 : i + 0x170 + 40].split(b"\0")[0].decode("utf-8", "replace")
        )

    grow = [
        (t, want - len(per_team.get(t, [])))
        for t in sorted(clubs)
        if len(per_team.get(t, [])) < want
    ]
    if limit:
        grow = grow[:limit]
    need = sum(g[1] for g in grow)
    print("%d club(s) short of %d players: %d players to add" % (len(grow), want, need))
    if dry or not need:
        print("dry run: nothing written" if dry else "nothing to do")
        return 0

    more = E.free_ids(players, need)
    if len(more) < need:
        print("only %d free player ids" % len(more))
        return 1
    eid_top = max(
        int.from_bytes(assigns[i + A_EID : i + A_EID + 4], "little")
        for i in range(0, len(assigns), A_REC)
    )
    pid_off = {
        int.from_bytes(players[i + E.P_ID : i + E.P_ID + 4], "little"): i
        for i in range(0, len(players), E.P_REC)
    }

    made = 0
    for tid, add in grow:
        first = per_team[tid][0]
        tpid = int.from_bytes(assigns[first + A_PID : first + A_PID + 4], "little")
        po = pid_off[tpid]
        have = len(per_team[tid])
        for k in range(add):
            pid = more[made]
            e = bytearray(assigns[first : first + A_REC])
            e[A_EID : A_EID + 4] = (eid_top + 1 + made).to_bytes(4, "little")
            e[A_PID : A_PID + 4] = pid.to_bytes(4, "little")
            e[A_TID : A_TID + 4] = tid.to_bytes(4, "little")
            assigns += e
            pr = bytearray(players[po : po + E.P_REC])
            pr[E.P_ID : E.P_ID + 4] = pid.to_bytes(4, "little")
            pr[E.P_NAME : E.P_NAME + E.P_NAME_LEN * E.P_NAME_SLOTS] = E.name_slots(
                "%s Player %02d" % (name.get(tid, "Club"), have + k + 1)
            )
            E.setf(pr, "Nationality", country.get(tid, 200))
            players += pr
            made += 1

    open(os.path.join(base, "Player.bin"), "wb").write(pesdb.wesys_pack(bytes(players)))
    open(os.path.join(base, "PlayerAssignment.bin"), "wb").write(
        pesdb.wesys_pack(bytes(assigns))
    )
    print("added %d player(s) to %d club(s)" % (made, len(grow)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
