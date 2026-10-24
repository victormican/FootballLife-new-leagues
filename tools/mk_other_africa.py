"""python mk_other_africa.py --base <world pesdb> --worldfile <fl26world.txt>
                           [--count 60] [--squad 11] [--slot 75] [--dry]

Fill the "Other Clubs (Africa)" group with `--count` clubs of its own.

Why it needs a competition: slot 75 is named by the switch at 0x140ea08e0, but its team list is
built by a filler the repository measured as "never filled", so the group has never shown a
club. `fl26clubs.dll` replaces the two readers of those lists (0x1414d62c0, 0x1414d6290) and
serves a slot from the regulation of the league the world names for it -- slot 75 is one of the
served ones. A league cannot *sit* on 75 (the exe ships a competition there and fl26comptab
aborts the whole table), so the line uses `slot=123` (hidden) plus **`serve=75`**: the row goes
to the hidden slot and fl26clubs answers 75 from this regulation. fl26slotnames leaves the
shipped heading alone, so the group keeps the game's own name.

The clubs are clones of the last club of the world with a full squad, the same rule
`add_generic_leagues.py` and `grow_leagues.py` use: a Team.bin row, `--squad` assignments and
their players with ids from `playeredit.free_ids`. Country: Morocco (id 200 is Croatia, so the
African id is read from Country.bin: `--country`, default 58 = Tunisia's block in the test world
is not used; the tool takes the first CAF country it finds in Team.bin's own clubs).
"""

import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pesdb
import playeredit as E
import mkleague as M

DEFAULT_NAME = "Other Clubs (Africa)"
DEFAULT_CODE = "FL_OAFR"

T_REC, T_ID, T_ALT = 1532, 0x08, 0x0C
T_COUNTRY, T_NAME, T_NAME_LEN, T_NAME_SLOTS, T_NAME_STEP = 0x46, 0x9E, 70, 20, 70
T_ABBR, T_ABBR_LEN = 0x372, 4
A_REC, A_EID, A_PID, A_TID = 16, 0x00, 0x04, 0x08


def main():
    a = sys.argv[1:]
    get = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    base, wf = get("--base"), get("--worldfile")
    if not base or not wf:
        print(__doc__)
        return 1
    count = int(get("--count", "60"))
    squad_n = int(get("--squad", "11"))
    slot = int(get("--slot", "75"))
    country = int(get("--country", "58"))
    NAME = get("--name", DEFAULT_NAME)
    CODE = get("--code", DEFAULT_CODE)
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
    comp = M.load(base, "Competition.bin")
    regs = M.load(base, "CompetitionRegulation.bin")
    ents = M.load(base, "CompetitionEntry.bin")

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
        if len(by_team.get(tid, [])) >= squad_n:
            clubs.append((tid, o))
    if not clubs:
        print("no club with %d players to copy" % squad_n)
        return 1
    tt, toff = clubs[-1]
    squad = by_team[tt][:squad_n]
    top = max(
        int.from_bytes(raw[o + T_ID : o + T_ID + 4], "little")
        for o in range(0, len(raw), T_REC)
    )
    top_alt = max(
        int.from_bytes(raw[o + T_ALT : o + T_ALT + 4], "little")
        for o in range(0, len(raw), T_REC)
    )
    eid_top = max(
        int.from_bytes(assigns[i + A_EID : i + A_EID + 4], "little")
        for i in range(0, len(assigns), A_REC)
    )
    more = E.free_ids(players, count * squad_n)
    if len(more) < count * squad_n:
        print("only %d free player ids" % len(more))
        return 1
    pid_off = {
        int.from_bytes(players[i + E.P_ID : i + E.P_ID + 4], "little"): i
        for i in range(0, len(players), E.P_REC)
    }

    used_c = {comp[i + M.CID_OFF] for i in range(0, len(comp), M.COMP)}
    used_r = {
        int.from_bytes(regs[i + M.R_ID : i + M.R_ID + 2], "little")
        for i in range(0, len(regs), M.REG)
    }
    cid = next(c for c in range(48, 256) if c not in used_c)
    reg = next(r for r in range(176, 1024) if r not in used_r)
    print(
        "competition %d, regulation %d, %d clubs of %d players, country %d"
        % (cid, reg, count, squad_n, country)
    )
    if dry:
        print("dry run: nothing written")
        return 0

    comp, regs, ents = bytearray(comp), bytearray(regs), bytearray(ents)
    teams = []
    for j in range(count):
        tid = top + 1 + j
        row = bytearray(raw[toff : toff + T_REC])
        row[T_ID : T_ID + 4] = tid.to_bytes(4, "little")
        row[T_ALT : T_ALT + 4] = (top_alt + 1 + j).to_bytes(4, "little")
        cname = "%s Club %02d" % (NAME, j + 1)
        for s in range(T_NAME_SLOTS):
            off = T_NAME + s * T_NAME_STEP
            if off + T_NAME_LEN <= T_REC:
                b = cname.encode("utf-8")[: T_NAME_LEN - 1]
                row[off : off + T_NAME_LEN] = b + bytes(T_NAME_LEN - len(b))
        code = ("A%02d" % (j + 1))[:3]
        row[T_ABBR : T_ABBR + T_ABBR_LEN] = code.encode("ascii")[
            : T_ABBR_LEN - 1
        ].ljust(T_ABBR_LEN, b"\0")
        old_c = int.from_bytes(row[T_COUNTRY : T_COUNTRY + 2], "little")
        row[T_COUNTRY : T_COUNTRY + 2] = (
            (old_c & ~(0x1FF << 2)) | ((country & 0x1FF) << 2)
        ).to_bytes(2, "little")
        raw += row
        for n, ai in enumerate(squad):
            pid = more[j * squad_n + n]
            e = bytearray(assigns[ai : ai + A_REC])
            e[A_EID : A_EID + 4] = (eid_top + 1 + j * squad_n + n).to_bytes(4, "little")
            e[A_PID : A_PID + 4] = pid.to_bytes(4, "little")
            e[A_TID : A_TID + 4] = tid.to_bytes(4, "little")
            assigns += e
            tpid = int.from_bytes(assigns[ai + A_PID : ai + A_PID + 4], "little")
            po = pid_off[tpid]
            pr = bytearray(players[po : po + E.P_REC])
            pr[E.P_ID : E.P_ID + 4] = pid.to_bytes(4, "little")
            pr[E.P_NAME : E.P_NAME + E.P_NAME_LEN * E.P_NAME_SLOTS] = E.name_slots(
                "%s Club %02d Player %02d" % (NAME, j + 1, n + 1)
            )
            E.setf(pr, "Nationality", country)
            players += pr
        teams.append(tid)
    M.add_league(
        comp, regs, ents, cid, reg, M.enc_region(25), NAME, CODE, teams, tier=1
    )

    open(os.path.join(base, "Team.bin"), "wb").write(pesdb.wesys_pack(bytes(raw)))
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

    lines = io.open(wf, encoding="utf-8", errors="replace").read().splitlines()
    new = (
        "league %d cid=%d region=25 country=200 conf=5 slot=123 serve=%d tier=1 promote=0 "
        "demote=0 clubs=%d legs=2 kickoff=99 name=%s" % (reg, cid, slot, count, NAME)
    )
    lines = [l for l in lines if not l.startswith("league %d " % reg)]
    lines.append(new)
    io.open(wf, "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
    print("world file: %s" % new)
    return 0


if __name__ == "__main__":
    sys.exit(main())
