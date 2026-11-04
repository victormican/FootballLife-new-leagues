"""python generic_clubs.py --base <pesdb> --worldfile <fl26world.txt> --reg 900[,901,..] [--dry]

Give the clubs of a league of ours their generic identity back: "<league> Club NN" and
"<club> Player NN", the naming `fill_group.py` uses for every club it clones.

The eight leagues of 2026-11-04 were built out of rows nobody owned and those rows were then
renamed after real clubs (add_eight_leagues.py). The rows, the squads and the ids were ours, so
nothing of the game was lost -- but the menu showed the names of clubs that belong to other
divisions, which is not what a world of generic clubs is supposed to read as. This rewrites the
name only: no id, no entry, no assignment, no squad and no crest is touched, so it is safe to
run on a world that already plays (the crest of a club is keyed by its id, not by its name).

The league name comes from the world line, because mkleague.add_league clears the regulation's
copy (the same bug that left the eight leagues nameless in the menu, 2026-11-04).
"""

import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pesdb
import playeredit as E
import mkleague as M
from make_country_leagues import put_team_name

T_REC, T_ID, T_ABBR, T_ABBR_LEN = 1532, 0x08, 0x372, 4
A_REC, A_PID, A_TID = 16, 0x04, 0x08


def world_lines(wf):
    """{reg: (name, country)} of the `league` lines."""
    out = {}
    for line in io.open(wf, encoding="utf-8", errors="replace").read().splitlines():
        w = line.split()
        if len(w) > 1 and w[0] == "league" and w[1].isdigit():
            kv = dict(x.split("=", 1) for x in w[2:] if "=" in x)
            if "name=" in line:
                kv["name"] = line.split("name=", 1)[1]
            out[int(w[1])] = (kv.get("name", ""), int(kv.get("country", "200")))
    return out


def rows(raw, off):
    for o in range(0, len(raw), T_REC):
        if int.from_bytes(raw[o + T_ID : o + T_ID + 4], "little") == off:
            return o
    return None


def main():
    a = sys.argv[1:]
    get = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    base, wf, regs = get("--base"), get("--worldfile"), get("--reg")
    if not base or not wf or not regs:
        print(__doc__)
        return 1
    want = [int(x) for x in regs.replace(",", " ").split()]
    dry = "--dry" in a

    raw = bytearray(
        pesdb.wesys_unpack(open(os.path.join(base, "Team.bin"), "rb").read())
    )
    players = bytearray(
        pesdb.wesys_unpack(open(os.path.join(base, "Player.bin"), "rb").read())
    )
    assigns = bytearray(
        pesdb.wesys_unpack(
            open(os.path.join(base, "PlayerAssignment.bin"), "rb").read()
        )
    )
    ents = pesdb.wesys_unpack(
        open(os.path.join(base, "CompetitionEntry.bin"), "rb").read()
    )
    regs_raw = pesdb.wesys_unpack(
        open(os.path.join(base, "CompetitionRegulation.bin"), "rb").read()
    )
    world = world_lines(wf)

    cid_of = {}
    for i in range(0, len(regs_raw), M.REG):
        r = regs_raw[i : i + M.REG]
        cid_of[int.from_bytes(r[M.R_ID : M.R_ID + 2], "little")] = r[M.R_CID] | (
            r[M.R_CID_HI] << 8
        )

    squad = {}
    for i in range(0, len(assigns), A_REC):
        squad.setdefault(
            int.from_bytes(assigns[i + A_TID : i + A_TID + 4], "little"), []
        ).append(int.from_bytes(assigns[i + A_PID : i + A_PID + 4], "little"))
    p_off = {}
    for o in range(0, len(players), E.P_REC):
        p_off[int.from_bytes(players[o + E.P_ID : o + E.P_ID + 4], "little")] = o

    changed = 0
    for reg in want:
        cid = cid_of.get(reg)
        if cid is None:
            print("reg %d: not in CompetitionRegulation.bin" % reg)
            return 2
        league = world.get(reg, ("", 200))[0]
        if not league:
            print("reg %d: no `league` line with a name in %s" % (reg, wf))
            return 2
        idx = [
            i
            for i in range(0, len(ents), M.ENT)
            if (ents[i + M.E_CID] | (ents[i + M.E_CID_HI] << 8)) == cid
        ]
        idx.sort(key=lambda i: ents[i + M.E_ORDER])
        print("reg %d cid %d %s: %d club(s)" % (reg, cid, league, len(idx)))
        for k, i in enumerate(idx, 1):
            tid = int.from_bytes(ents[i + M.E_TEAM : i + M.E_TEAM + 4], "little")
            o = rows(raw, tid)
            if o is None:
                print("  club %d: no Team.bin row" % tid)
                return 2
            club = "%s Club %02d" % (league, k)
            code = ("G%02d" % k)[: T_ABBR_LEN - 1]
            if dry:
                print("  %6d %-38s %s" % (tid, club, code))
            else:
                row = bytearray(raw[o : o + T_REC])
                put_team_name(row, club)
                row[T_ABBR : T_ABBR + T_ABBR_LEN] = code.encode("ascii").ljust(
                    T_ABBR_LEN, b"\0"
                )
                raw[o : o + T_REC] = row
            for n, pid in enumerate(sorted(squad.get(tid, [])), 1):
                po = p_off.get(pid)
                if po is None:
                    print("  player %d: no Player.bin row" % pid)
                    return 2
                if dry:
                    if n <= 2:
                        print("        %6d %s Player %02d" % (pid, club, n))
                    continue
                players[
                    po + E.P_NAME : po + E.P_NAME + E.P_NAME_LEN * E.P_NAME_SLOTS
                ] = E.name_slots("%s Player %02d" % (club, n))
            changed += 1

    if dry:
        print("dry run: %d club(s), nothing written" % changed)
        return 0

    open(os.path.join(base, "Team.bin"), "wb").write(pesdb.wesys_pack(bytes(raw)))
    open(os.path.join(base, "Player.bin"), "wb").write(pesdb.wesys_pack(bytes(players)))
    print("renamed %d club(s) and their squads" % changed)
    return 0


if __name__ == "__main__":
    sys.exit(main())
