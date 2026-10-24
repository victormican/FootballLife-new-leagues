"""python add_generic_leagues.py --base <world pesdb> --worldfile <fl26world.txt>
                              [--count 19] [--start-slot 189] [--start-cid 237] [--start-reg 317]
                              [--clubs 10] [--dry]

Insert generic leagues to test the Select Team slots.  Read/write on Team.bin, Player.bin,
PlayerAssignment.bin, Competition.bin, CompetitionRegulation.bin and CompetitionEntry.bin; it
also appends the world file's `league` lines.

Each league is ten clubs of a cloned generic club (22 players each), in region 29 and country 200
(Croatia) so no new region is needed, on a slot from 189 up.  The competition ids start at 237
(the free high ids of the 91-league test world) and the regulation ids at 317 (above the date
stub's table; `datecave.py` dates them with the big-league calendar shifted by id & 7).

The slots 69/71/73/75 are never used, so "Other Clubs (Africa)" and the other groups stay.  The
competition cap is 255: the test world has 193 competitions, so 62 are the theoretical maximum;
the high-id free range is 19 (237..255), the rest would need the low safe ids.
"""

import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pesdb
import playeredit as E
import mkleague as M

T_REC, T_ID, T_ALT = 1532, 0x08, 0x0C
T_COUNTRY, T_NAME, T_NAME_LEN, T_NAME_SLOTS, T_NAME_STEP = 0x46, 0x9E, 70, 20, 70
T_ABBR, T_ABBR_LEN = 0x372, 4
A_REC, A_EID, A_PID, A_TID, A_PACK = 16, 0x00, 0x04, 0x08, 0x0C
REGION = 29
COUNTRY = 200  # Croatia: an existing region, no new country
CONF = 2


def text(b):
    return b.split(b"\0")[0].decode("utf-8", "replace")


def main():
    a = sys.argv[1:]
    get = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    base, wf = get("--base"), get("--worldfile")
    if not base or not wf:
        print(__doc__)
        return 1
    count = int(get("--count", "19"))
    slot0 = int(get("--start-slot", "189"))
    cid0 = int(get("--start-cid", "237"))
    reg0 = int(get("--start-reg", "317"))
    slots = [int(x) for x in get("--slots", "").split(",") if x.strip()]
    cids = [int(x) for x in get("--cids", "").split(",") if x.strip()]
    regs_in = [int(x) for x in get("--regs", "").split(",") if x.strip()]
    if cids:
        count = len(cids)
    nclub = int(get("--clubs", "10"))
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
    comp, regs, ents = (
        M.load(base, n)
        for n in (
            "Competition.bin",
            "CompetitionRegulation.bin",
            "CompetitionEntry.bin",
        )
    )
    # a template club with enough assignments: the last club row
    by_team = {}
    for i in range(0, len(assigns), A_REC):
        by_team.setdefault(
            int.from_bytes(assigns[i + A_TID : i + A_TID + 4], "little"), []
        ).append(i)
    clubs = []
    for i in range(len(raw) // T_REC):
        o = i * T_REC
        if raw[o + 0x53] & 0x80:
            continue
        tid = int.from_bytes(raw[o + T_ID : o + T_ID + 4], "little")
        if len(by_team.get(tid, [])) >= 22:
            clubs.append((tid, o))
    if not clubs:
        print("no club with 22 players to copy")
        return 1
    tt, toff = clubs[-1]
    squad = by_team[tt][:22]
    top = max(
        int.from_bytes(raw[o + T_ID : o + T_ID + 4], "little")
        for o in range(0, len(raw), T_REC)
    )
    top_alt = max(
        int.from_bytes(raw[o + T_ALT : o + T_ALT + 4], "little")
        for o in range(0, len(raw), T_REC)
    )
    pid_top = max(
        int.from_bytes(players[i + E.P_ID : i + E.P_ID + 4], "little")
        for i in range(0, len(players), E.P_REC)
    )
    pid_off = {
        int.from_bytes(players[i + E.P_ID : i + E.P_ID + 4], "little"): i
        for i in range(0, len(players), E.P_REC)
    }
    eid_top = max(
        int.from_bytes(assigns[i + A_EID : i + A_EID + 4], "little")
        for i in range(0, len(assigns), A_REC)
    )
    print(
        "template club %d, %d players; adding %d leagues of %d clubs"
        % (tt, len(squad), count, nclub)
    )
    lines, made_clubs, made_players = [], 0, 0
    for k in range(count):
        slot = slots[k] if slots else slot0 + k
        cid = cids[k] if cids else cid0 + k
        reg = regs_in[k] if regs_in else reg0 + k
        name = "Generic League %02d" % (k + 1)
        teams = []
        for j in range(nclub):
            tid = top + 1 + made_clubs
            row = bytearray(raw[toff : toff + T_REC])
            row[T_ID : T_ID + 4] = tid.to_bytes(4, "little")
            row[T_ALT : T_ALT + 4] = (top_alt + 1 + made_clubs).to_bytes(4, "little")
            cname = "%s Club %02d" % (name, j + 1)
            for s in range(T_NAME_SLOTS):
                off = T_NAME + s * T_NAME_STEP
                if off + T_NAME_LEN <= T_REC:
                    b = cname.encode("utf-8")[: T_NAME_LEN - 1]
                    row[off : off + T_NAME_LEN] = b + bytes(T_NAME_LEN - len(b))
            code = ("G%02d%02d" % (k + 1, j + 1))[:3]
            row[T_ABBR : T_ABBR + T_ABBR_LEN] = code.encode("ascii")[
                : T_ABBR_LEN - 1
            ].ljust(T_ABBR_LEN, b"\0")
            old = int.from_bytes(row[T_COUNTRY : T_COUNTRY + 2], "little")
            row[T_COUNTRY : T_COUNTRY + 2] = (
                (old & ~(0x1FF << 2)) | ((COUNTRY & 0x1FF) << 2)
            ).to_bytes(2, "little")
            raw += row
            for n, ai in enumerate(squad, 1):
                pid = pid_top + 1 + made_players
                e = bytearray(assigns[ai : ai + A_REC])
                e[A_EID : A_EID + 4] = (eid_top + 1 + made_players).to_bytes(
                    4, "little"
                )
                e[A_PID : A_PID + 4] = pid.to_bytes(4, "little")
                e[A_TID : A_TID + 4] = tid.to_bytes(4, "little")
                assigns += e
                tpid = int.from_bytes(assigns[ai + A_PID : ai + A_PID + 4], "little")
                po = pid_off[tpid]
                pr = bytearray(players[po : po + E.P_REC])
                pr[E.P_ID : E.P_ID + 4] = pid.to_bytes(4, "little")
                pr[E.P_NAME : E.P_NAME + E.P_NAME_LEN * E.P_NAME_SLOTS] = E.name_slots(
                    "%s Club %02d Player %02d" % (name, j + 1, n)
                )
                E.setf(pr, "Nationality", COUNTRY)
                players += pr
                made_players += 1
            teams.append(tid)
            made_clubs += 1
        M.add_league(
            comp,
            regs,
            ents,
            cid,
            reg,
            M.enc_region(REGION),
            name,
            "FL_GEN%02d" % (k + 1),
            teams,
            quiet=True,
            tier=1,
        )
        lines.append(
            "league %d cid=%d region=%d country=%d conf=%d slot=%d tier=1 promote=0 demote=0 clubs=%d legs=2 kickoff=99 name=%s"
            % (reg, cid, REGION, COUNTRY, CONF, slot, nclub, name)
        )
        print("  %s: cid %d reg %d slot %d" % (name, cid, reg, slot))
    if dry:
        print("dry run: nothing written")
        return 0
    open(os.path.join(base, "Team.bin"), "wb").write(pesdb.wesys_pack(bytes(raw)))
    open(os.path.join(base, "Player.bin"), "wb").write(pesdb.wesys_pack(bytes(players)))
    open(os.path.join(base, "PlayerAssignment.bin"), "wb").write(
        pesdb.wesys_pack(bytes(assigns))
    )
    for n, b in (("Competition.bin", comp), ("CompetitionRegulation.bin", regs),
                 ("CompetitionEntry.bin", ents)):
        open(os.path.join(base, n), "wb").write(pesdb.wesys_pack(bytes(b)))
    s = io.open(wf, encoding="utf-8", errors="replace").read()
    s = s.rstrip("\n") + "\n" + "\n".join(lines) + "\n"
    io.open(wf, "w", encoding="utf-8", newline="\n").write(s)
    print(
        "added %d leagues, %d clubs, %d players; ids %d..%d"
        % (count, made_clubs, made_players, top + 1, top + made_clubs)
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
