"""python add_nonfifa.py --base <world pesdb> --worldfile <fl26world.txt>
                        --countries <pesdb with Country.bin> [--dry]

A league of national teams that are not FIFA members.  The game has no room in Country.bin
(214 rows, every one named; Palau and Monaco were already reused for Chinese Taipei and South
Sudan), so this appends the rows in free flag ids and then, like add_nations.py, clones a
national team's squad for each one.

Names and confederation: the Caribbean associations CONCACAF has and FIFA does not, plus two
European stateless sides.

The flags are not in the game folder (they live in a cpk), so the new countries have no art
until someone drops flag_<id>.png in common/render/symbol/flag/.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pesdb
import playeredit as E
import mkleague as M
import mkflags

T_REC, T_ID, T_ALT = 1532, 0x08, 0x0C
T_NATIONAL, T_COUNTRY = 0x53, 0x46
T_NAME, T_NAME_LEN, T_NAME_SLOTS, T_NAME_STEP = 0x9E, 70, 20, 70
T_ABBR, T_ABBR_LEN = 0x372, 4
A_REC, A_EID, A_PID, A_TID = 16, 0x00, 0x04, 0x08
C_REC = 1420
C_FLAG = (int.from_bytes(b"\x01\x00\x00\x00", "little") >> 10) & 0x1FF
C_NAMES = range(148, C_REC - 69, 70)
C_EN = 288

# name, country id (a free flag id), confederation (6 CONCACAF, 2 UEFA)
NATIONS = [
    ("MARTINIQUE", 96, 6),
    ("GUADELOUPE", 97, 6),
    ("FRENCH GUIANA", 99, 6),
    ("SAINT MARTIN", 100, 6),
    ("SINT MAARTEN", 101, 6),
    ("BONAIRE", 102, 6),
    ("CATALONIA", 118, 2),
    ("PADANIA", 123, 2),
]


def text(b):
    return b.split(b"\0")[0].decode("utf-8", "replace")


def main():
    a = sys.argv[1:]
    get = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    base, wf = get("--base"), get("--worldfile")
    countries = get("--countries") or base
    if not base or not wf:
        print(__doc__)
        return 1
    dry = "--dry" in a

    cty_raw = bytearray(mkflags.table("Country", [countries]))
    have = {
        ((int.from_bytes(cty_raw[o : o + 4], "little") >> 10) & 0x1FF)
        for o in range(0, len(cty_raw), C_REC)
    }
    missing = [c for _n, c, _f in NATIONS if c in have]
    if missing:
        print("flag id(s) %s already in Country.bin" % missing)
        return 1

    print("Country.bin: %d rows, adding %d" % (len(cty_raw) // C_REC, len(NATIONS)))
    if dry:
        for n, c, f in NATIONS:
            print("  %-15s country %-3d conf %d" % (n, c, f))
        print("dry run: nothing written")
        return 0

    tpl = cty_raw[0:C_REC]
    for name, cid, _conf in NATIONS:
        r = bytearray(tpl)
        blob = (int.from_bytes(r[0:4], "little") & ~(0x1FF << 10)) | (cid << 10)
        r[0:4] = blob.to_bytes(4, "little")
        for o in list(C_NAMES) + [C_EN]:
            b = name.encode("utf-8")[: 70 - 1]
            r[o : o + 70] = b + bytes(70 - len(b))
        cty_raw += r

    teams_raw = bytearray(
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

    by_team = {}
    for i in range(0, len(assigns), A_REC):
        by_team.setdefault(
            int.from_bytes(assigns[i + A_TID : i + A_TID + 4], "little"), []
        ).append(i)
    nats = [
        (int.from_bytes(teams_raw[o + T_ID : o + T_ID + 4], "little"), o)
        for o in range(0, len(teams_raw), T_REC)
        if teams_raw[o + T_NATIONAL] & 0x80
    ]
    tpl_team, tpl_off = next(
        (t, o) for t, o in nats if t == 1141 and len(by_team.get(t, [])) >= 11
    )
    squad = by_team[tpl_team][:11]

    top = max(
        int.from_bytes(teams_raw[o + T_ID : o + T_ID + 4], "little")
        for o in range(0, len(teams_raw), T_REC)
    )
    top_alt = max(
        int.from_bytes(teams_raw[o + T_ALT : o + T_ALT + 4], "little")
        for o in range(0, len(teams_raw), T_REC)
    )
    pid_top = max(
        int.from_bytes(players[i + E.P_ID : i + E.P_ID + 4], "little")
        for i in range(0, len(players), E.P_REC)
    )
    eid_top = max(
        int.from_bytes(assigns[i + A_EID : i + A_EID + 4], "little")
        for i in range(0, len(assigns), A_REC)
    )
    free = E.free_ids(players, len(NATIONS) * len(squad))

    made, team_ids = 0, []
    for k, (name, cid, _conf) in enumerate(NATIONS):
        tid = top + 1 + k
        team_ids.append(tid)
        row = bytearray(teams_raw[tpl_off : tpl_off + T_REC])
        row[T_ID : T_ID + 4] = tid.to_bytes(4, "little")
        row[T_ALT : T_ALT + 4] = (top_alt + 1 + k).to_bytes(4, "little")
        for s in range(T_NAME_SLOTS):
            o = T_NAME + s * T_NAME_STEP
            if o + T_NAME_LEN <= T_REC:
                b = name.encode("utf-8")[: T_NAME_LEN - 1]
                row[o : o + T_NAME_LEN] = b + bytes(T_NAME_LEN - len(b))
        code = "".join(ch for ch in name if ch.isalpha())[:3].ljust(3, "X")
        row[T_ABBR : T_ABBR + T_ABBR_LEN] = code.encode("ascii")[
            : T_ABBR_LEN - 1
        ].ljust(T_ABBR_LEN, b"\0")
        old = int.from_bytes(row[T_COUNTRY : T_COUNTRY + 2], "little")
        row[T_COUNTRY : T_COUNTRY + 2] = ((old & ~(0x1FF << 2)) | (cid << 2)).to_bytes(
            2, "little"
        )
        row[T_NATIONAL] |= 0x80
        teams_raw += row
        for n, ai in enumerate(squad, 1):
            pid = free[made] if made < len(free) else pid_top + 1 + made
            e = bytearray(assigns[ai : ai + A_REC])
            e[A_EID : A_EID + 4] = (eid_top + 1 + made).to_bytes(4, "little")
            e[A_PID : A_PID + 4] = pid.to_bytes(4, "little")
            e[A_TID : A_TID + 4] = tid.to_bytes(4, "little")
            assigns += e
            tpid = int.from_bytes(assigns[ai + A_PID : ai + A_PID + 4], "little")
            po = next(
                o
                for o in range(0, len(players), E.P_REC)
                if int.from_bytes(players[o + E.P_ID : o + E.P_ID + 4], "little")
                == tpid
            )
            pr = bytearray(players[po : po + E.P_REC])
            pr[E.P_ID : E.P_ID + 4] = pid.to_bytes(4, "little")
            pr[E.P_NAME : E.P_NAME + E.P_NAME_LEN * E.P_NAME_SLOTS] = E.name_slots(
                "%s Player %02d" % (name, n)
            )
            E.setf(pr, "Nationality", cid)
            players += pr
            made += 1

    cid_c, reg = 110, 216
    comp = bytearray(M.load(base, "Competition.bin"))
    regs = bytearray(M.load(base, "CompetitionRegulation.bin"))
    ents = bytearray(M.load(base, "CompetitionEntry.bin"))
    M.add_league(
        comp,
        regs,
        ents,
        cid_c,
        reg,
        M.enc_region(25),
        "Non-FIFA Nations",
        "FL_NONF",
        team_ids,
        tier=1,
    )

    open(os.path.join(base, "Country.bin"), "wb").write(
        pesdb.wesys_pack(bytes(cty_raw))
    )
    open(os.path.join(base, "Team.bin"), "wb").write(pesdb.wesys_pack(bytes(teams_raw)))
    open(os.path.join(base, "Player.bin"), "wb").write(pesdb.wesys_pack(bytes(players)))
    open(os.path.join(base, "PlayerAssignment.bin"), "wb").write(
        pesdb.wesys_pack(bytes(assigns))
    )
    open(os.path.join(base, "Competition.bin"), "wb").write(
        pesdb.wesys_pack(bytes(comp))
    )
    open(os.path.join(base, "CompetitionRegulation.bin"), "wb").write(
        pesdb.wesys_pack(bytes(regs))
    )
    open(os.path.join(base, "CompetitionEntry.bin"), "wb").write(
        pesdb.wesys_pack(bytes(ents))
    )

    line = (
        "league %d cid=%d region=25 country=200 conf=6 slot=-1 tier=1 promote=0 demote=0 "
        "clubs=%d legs=1 kickoff=166 name=Non-FIFA Nations"
        % (reg, cid_c, len(team_ids))
    )
    lines = [
        l
        for l in open(wf, encoding="utf-8", errors="replace").read().splitlines()
        if not l.startswith("league %d " % reg)
    ]
    lines.append(line)
    open(wf, "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
    print(
        "%d team(s) %d..%d, %d players; league %d cid %d"
        % (len(team_ids), team_ids[0], team_ids[-1], made, reg, cid_c)
    )
    print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
