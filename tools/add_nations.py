"""python add_nations.py --base <world pesdb> --countries <pesdb with Country.bin>
                      [--count 67] [--oceania] [--dry]

Add generic national teams until the world has 211.  Read/write on Team.bin, Player.bin and
PlayerAssignment.bin; no other table.

The game ships 144 national teams (Team.bin rows with the top bit of +0x53 set).  This picks the
countries of Country.bin that have no national team, **Oceania first** (confederation 7), then the
rest by id, and gives each one:

- a Team.bin row cloned from a template national team, with a new team id, the country's name in
  every name slot, a three-letter code, the country id at +0x46 and the national bit kept;
- a squad of the template's players, cloned with new player ids, generic names
  ("<Country> Player 01" ...), the country as nationality and a PlayerAssignment row for the new
  team.  The template is a national team with at least eleven assignments (New Zealand when it is
  there).

The generic teams are inserted so the count reaches 211.  They use the team and player caps of
the current patch set (4,800 teams, 123,825 players in this branch); --dry prints the plan and
writes nothing.

The national-team *menu* is the part to test: the game may build its list from the national bit
and the country (then these appear), or from a static list (then a module must serve them).  The
tool logs the country ids it added so the test can say which group they landed in.
"""

import csv
import io
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pesdb
import mkflags
import playeredit as E
import leaguebuilder as B

T_REC, T_ID, T_ALT = 1532, 0x08, 0x0C
T_NATIONAL = 0x53
T_COUNTRY = 0x46
T_NAME, T_NAME_LEN, T_NAME_SLOTS, T_NAME_STEP = 0x9E, 70, 20, 70
T_ABBR, T_ABBR_LEN = 0x372, 4
A_REC, A_EID, A_PID, A_TID, A_PACK = 16, 0x00, 0x04, 0x08, 0x0C


def text(b):
    return b.split(b"\0")[0].decode("utf-8", "replace")


def main():
    a = sys.argv[1:]
    get = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    base = get("--base")
    countries = get("--countries") or base
    if not base:
        print(__doc__)
        return 1
    count = int(get("--count", "67"))
    dry = "--dry" in a
    ids_mode = get("--ids", "free")
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
    cty = mkflags.countries(mkflags.table("Country", [countries]))
    conf = B.confederations(countries)

    nats = []
    for i in range(len(raw) // T_REC):
        o = i * T_REC
        if raw[o + T_NATIONAL] & 0x80:
            nats.append(
                (
                    int.from_bytes(raw[o + T_ID : o + T_ID + 4], "little"),
                    (
                        int.from_bytes(raw[o + T_COUNTRY : o + T_COUNTRY + 2], "little")
                        >> 2
                    )
                    & 0x1FF,
                )
            )
    have = {c for _t, c in nats}
    top = max(
        int.from_bytes(raw[o + T_ID : o + T_ID + 4], "little")
        for o in range(0, len(raw), T_REC)
    )
    top_alt = max(
        int.from_bytes(raw[o + T_ALT : o + T_ALT + 4], "little")
        for o in range(0, len(raw), T_REC)
    )
    # a template national team with a squad of at least eleven
    by_team = {}
    for i in range(0, len(assigns), A_REC):
        by_team.setdefault(
            int.from_bytes(assigns[i + A_TID : i + A_TID + 4], "little"), []
        ).append(i)
    templ = next(
        ((t, c) for t, c in nats if t == 1141 and len(by_team.get(t, [])) >= 11),
        next(((t, c) for t, c in nats if len(by_team.get(t, [])) >= 11), None),
    )
    if templ is None:
        print("no national team with a squad to copy")
        return 1
    tt, tc = templ
    toff = next(
        o
        for o in range(0, len(raw), T_REC)
        if int.from_bytes(raw[o + T_ID : o + T_ID + 4], "little") == tt
    )
    squad = by_team[tt][:23]

    # Oceania first, then the rest by id.
    pool = [c for c in cty if c not in have]
    pool.sort(key=lambda c: (0 if conf.get(c) == 7 else 1, c))
    if "--oceania" in a:
        pool = [c for c in pool if conf.get(c) == 7] + [
            c for c in pool if conf.get(c) != 7
        ]
    pick = pool[:count]
    print(
        "national teams now: %d; adding %d (of %d missing), template %d"
        % (len(nats), len(pick), len(pool), tt)
    )
    if dry:
        for c in pick:
            print("  %3d %-30s conf %s" % (c, (cty.get(c) or ("?",))[0], conf.get(c)))
        print("dry run: nothing written")
        return 0

    pid_top = max(
        int.from_bytes(players[i + E.P_ID : i + E.P_ID + 4], "little")
        for i in range(0, len(players), E.P_REC)
    )
    free = E.free_ids(players, count * len(squad)) if ids_mode == "free" else []
    eid_top = max(
        int.from_bytes(assigns[i + A_EID : i + A_EID + 4], "little")
        for i in range(0, len(assigns), A_REC)
    )
    made = 0
    for k, c in enumerate(pick):
        name = (cty.get(c) or ("Nation %d" % c,))[0]
        tid = top + 1 + k
        row = bytearray(raw[toff : toff + T_REC])
        row[T_ID : T_ID + 4] = tid.to_bytes(4, "little")
        row[T_ALT : T_ALT + 4] = (top_alt + 1 + k).to_bytes(4, "little")
        for s in range(T_NAME_SLOTS):
            off = T_NAME + s * T_NAME_STEP
            if off + T_NAME_LEN <= T_REC:
                b = name.encode("utf-8")[: T_NAME_LEN - 1]
                row[off : off + T_NAME_LEN] = b + bytes(T_NAME_LEN - len(b))
        code = "".join(ch for ch in name.upper() if ch.isalpha())[:3].ljust(3, "X")
        row[T_ABBR : T_ABBR + T_ABBR_LEN] = code.encode("ascii")[
            : T_ABBR_LEN - 1
        ].ljust(T_ABBR_LEN, b"\0")
        old = int.from_bytes(row[T_COUNTRY : T_COUNTRY + 2], "little")
        row[T_COUNTRY : T_COUNTRY + 2] = (
            (old & ~(0x1FF << 2)) | ((c & 0x1FF) << 2)
        ).to_bytes(2, "little")
        row[T_NATIONAL] |= 0x80
        raw += row
        for n, ai in enumerate(squad, 1):
            pid = free[made] if free else pid_top + 1 + made
            e = bytearray(assigns[ai : ai + A_REC])
            e[A_EID : A_EID + 4] = (eid_top + 1 + made).to_bytes(4, "little")
            e[A_PID : A_PID + 4] = pid.to_bytes(4, "little")
            e[A_TID : A_TID + 4] = tid.to_bytes(4, "little")
            assigns += e
            pr = bytearray(
                players[(n - 1) * 0 : 0]
            )  # placeholder to keep the loop shape clear
            # clone the template player of this assignment
            tpid = int.from_bytes(assigns[ai + A_PID : ai + A_PID + 4], "little")
            po = next(
                o
                for o in range(0, len(players), E.P_REC)
                if int.from_bytes(players[o + E.P_ID : o + E.P_ID + 4], "little")
                == tpid
            )
            pr = bytearray(players[po : po + E.P_REC])
            pr[E.P_ID : E.P_ID + 4] = pid.to_bytes(4, "little")
            gname = "%s Player %02d" % (name, n)
            pr[E.P_NAME : E.P_NAME + E.P_NAME_LEN * E.P_NAME_SLOTS] = E.name_slots(
                gname
            )
            E.setf(pr, "Nationality", c)
            players += pr
            made += 1
    open(os.path.join(base, "Team.bin"), "wb").write(pesdb.wesys_pack(bytes(raw)))
    open(os.path.join(base, "Player.bin"), "wb").write(pesdb.wesys_pack(bytes(players)))
    open(os.path.join(base, "PlayerAssignment.bin"), "wb").write(
        pesdb.wesys_pack(bytes(assigns))
    )
    print(
        "added %d national teams, %d players; team ids %d..%d"
        % (len(pick), made, top + 1, top + len(pick))
    )
    for c in pick:
        print("  %3d %s" % (c, (cty.get(c) or ("?",))[0]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
