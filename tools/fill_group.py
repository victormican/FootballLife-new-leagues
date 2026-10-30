"""python fill_group.py --base <world pesdb> --worldfile <fl26world.txt> --reg <id>
                      [--slot N] [--pool N] [--seed-country N] [--to 48] [--country N] [--dry]

Grow one league of the world to `--to` clubs and, optionally, put it on a menu slot and seed it
with the game's own "other clubs" pool of a group.

Why: the "Other ..." groups of Select Team (slots 69 Other European Leagues, 70 Other Clubs
(Asia), 71 Other, 73 Other Latin American Teams, 75 Other Clubs (Africa)) are drawn by the exe
from the `Team.bin` pool nibble (+0x4f high nibble). A world that wants "the game's clubs plus
generics up to 48" in one of them gives that group a league of its own: the pool's clubs become
its first entries and generic clones fill it to 48. The slot is the group's, so the name on
screen is the group's own (fl26comptab moves the exe's row out of the way).

`--pool N` reads the nibble from Team.bin: 1 Classics, 2 Other European, 3 Other Asia,
5 Other (ML defaults), 6 Other Latin American, 7 Other Clubs (Africa).

`--seed-country N` seeds with the clubs the game already has for that country (Team.bin rows
whose country is N, with a squad, and in no competition yet) before it clones anything: the
world keeps what the game shipped and only the shortfall is generic.

The clubs are the same clone `grow_leagues.py` makes: a Team.bin row copied from one club of the
world that already has a squad, with new ids (`playeredit.free_ids` for the players), the
league's name, one PlayerAssignment per squad place. Nothing else of the world is touched.
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
T_POOL = 0x4F
A_REC, A_EID, A_PID, A_TID = 16, 0x00, 0x04, 0x08
P_REC = 312


def main():
    a = sys.argv[1:]
    get = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    base, wf = get("--base"), get("--worldfile")
    if not base or not wf or "--reg" not in a:
        print(__doc__)
        return 1
    reg = int(get("--reg"))
    want = int(get("--to", "48"))
    new_slot = int(get("--slot")) if "--slot" in a else None
    pool_nib = int(get("--pool")) if "--pool" in a else None
    seed_country = int(get("--seed-country")) if "--seed-country" in a else None
    country = int(get("--country")) if "--country" in a else None
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

    ri = next(
        i
        for i in range(0, len(regs), M.REG)
        if int.from_bytes(regs[i + M.R_ID : i + M.R_ID + 2], "little") == reg
    )
    cid = regs[ri + M.R_CID]
    rname = (
        regs[ri + M.R_NAME : ri + M.R_NAME + 0x73]
        .split(b"\0")[0]
        .decode("utf-8", "replace")
    )
    print("regulation %d: cid %d, name %r" % (reg, cid, rname))

    reset = "--reset" in a
    ent_idx = [i for i in range(0, len(ents), M.ENT) if ents[i + M.E_CID] == cid]
    ent_idx.sort(key=lambda i: ents[i + M.E_ORDER])
    have = (
        []
        if reset
        else [
            int.from_bytes(ents[i + M.E_TEAM : i + M.E_TEAM + 4], "little")
            for i in ent_idx
        ]
    )

    pool_ids = []
    if pool_nib is not None:
        for o in range(0, len(raw), T_REC):
            if raw[o + 0x53] & 0x80:
                continue
            if (raw[o + T_POOL] >> 4) & 0xF == pool_nib:
                tid = int.from_bytes(raw[o + T_ID : o + T_ID + 4], "little")
                if tid not in have:
                    pool_ids.append(tid)
        print("pool nibble %d: %d club(s) to seed" % (pool_nib, len(pool_ids)))

    country_ids = []
    if seed_country is not None:
        squad = {}
        for i in range(0, len(assigns), A_REC):
            t = int.from_bytes(assigns[i + A_TID : i + A_TID + 4], "little")
            squad[t] = squad.get(t, 0) + 1
        in_league = {
            int.from_bytes(ents[i + M.E_TEAM : i + M.E_TEAM + 4], "little")
            for i in range(0, len(ents), M.ENT)
        }
        for o in range(0, len(raw), T_REC):
            if raw[o + 0x53] & 0x80:
                continue
            tid = int.from_bytes(raw[o + T_ID : o + T_ID + 4], "little")
            cid0 = (
                int.from_bytes(raw[o + T_COUNTRY : o + T_COUNTRY + 2], "little") >> 2
            ) & 0x1FF
            if (
                cid0 == seed_country
                and tid not in in_league
                and squad.get(tid, 0) >= 11
            ):
                country_ids.append(tid)
        print(
            "country %d: %d shipped club(s) with a squad to seed"
            % (seed_country, len(country_ids))
        )

    seed = have + pool_ids + country_ids
    n_clone = max(0, want - len(seed))
    print(
        "have %d, pool %d, country %d -> seed %d, clones %d, target %d"
        % (len(have), len(pool_ids), len(country_ids), len(seed), n_clone, want)
    )

    # country for the clones: --country or the world line's
    line_n = None
    lines = io.open(wf, encoding="utf-8", errors="replace").read().splitlines()
    for n, line in enumerate(lines):
        w = line.split()
        if len(w) > 1 and w[0] == "league" and w[1].isdigit() and int(w[1]) == reg:
            line_n = n
            break
    kv = {}
    if line_n is not None:
        kv = dict(x.split("=", 1) for x in lines[line_n].split()[2:] if "=" in x)
    if country is None:
        country = int(kv.get("country", "200"))

    if dry:
        print("line:", lines[line_n] if line_n is not None else "(none)")
        print("dry run: nothing written")
        return 0

    # template squad
    by_team = {}
    for i in range(0, len(assigns), A_REC):
        by_team.setdefault(
            int.from_bytes(assigns[i + A_TID : i + A_TID + 4], "little"), []
        ).append(i)
    clubs = []
    for o in range(0, len(raw), T_REC):
        if raw[o + 0x53] & 0x80:
            continue
        tid = int.from_bytes(raw[o + T_ID : o + T_ID + 4], "little")
        if len(by_team.get(tid, [])) >= 22:
            clubs.append((tid, o))
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
    eid_top = max(
        int.from_bytes(assigns[i + A_EID : i + A_EID + 4], "little")
        for i in range(0, len(assigns), A_REC)
    )
    free = E.free_ids(players, n_clone * len(squad))
    if len(free) < n_clone * len(squad):
        print("only %d free player ids for %d" % (len(free), n_clone * len(squad)))
        return 1

    made = 0
    for j in range(n_clone):
        tid = top + 1 + j
        row = bytearray(raw[toff : toff + T_REC])
        row[T_ID : T_ID + 4] = tid.to_bytes(4, "little")
        row[T_ALT : T_ALT + 4] = (top_alt + 1 + j).to_bytes(4, "little")
        cname = "%s Club %02d" % (rname, len(seed) + j + 1)
        for s in range(T_NAME_SLOTS):
            off = T_NAME + s * T_NAME_STEP
            if off + T_NAME_LEN <= T_REC:
                b = cname.encode("utf-8")[: T_NAME_LEN - 1]
                row[off : off + T_NAME_LEN] = b + bytes(T_NAME_LEN - len(b))
        code = ("G%02d%02d" % (j // 100, j % 100))[:3]
        row[T_ABBR : T_ABBR + T_ABBR_LEN] = code.encode("ascii")[
            : T_ABBR_LEN - 1
        ].ljust(T_ABBR_LEN, b"\0")
        old = int.from_bytes(row[T_COUNTRY : T_COUNTRY + 2], "little")
        row[T_COUNTRY : T_COUNTRY + 2] = (
            (old & ~(0x1FF << 2)) | ((country & 0x1FF) << 2)
        ).to_bytes(2, "little")
        raw += row
        for n, ai in enumerate(squad, 1):
            pid = free[made]
            e = bytearray(assigns[ai : ai + A_REC])
            e[A_EID : A_EID + 4] = (eid_top + 1 + made).to_bytes(4, "little")
            e[A_PID : A_PID + 4] = pid.to_bytes(4, "little")
            e[A_TID : A_TID + 4] = tid.to_bytes(4, "little")
            assigns += e
            tpid = int.from_bytes(assigns[ai + A_PID : ai + A_PID + 4], "little")
            po = next(
                o
                for o in range(0, len(players), P_REC)
                if int.from_bytes(players[o + E.P_ID : o + E.P_ID + 4], "little")
                == tpid
            )
            pr = bytearray(players[po : po + P_REC])
            pr[E.P_ID : E.P_ID + 4] = pid.to_bytes(4, "little")
            pr[E.P_NAME : E.P_NAME + E.P_NAME_LEN * E.P_NAME_SLOTS] = E.name_slots(
                "%s Player %02d" % (cname, n)
            )
            E.setf(pr, "Nationality", country)
            players += pr
            made += 1

    # entries: the game's own pool clubs first (they must all stay), then our existing clubs,
    # then the clones; trimmed to `want` keeping the game's clubs when they already fill it
    country_ids = country_ids[: max(0, want - len(pool_ids))]
    fixed = pool_ids + country_ids
    keep_ours = have[: max(0, want - len(fixed))]
    clones = list(range(top + 1, top + 1 + n_clone))
    final = (fixed + keep_ours + clones)[: max(want, len(fixed))]
    ents = bytearray(
        b"".join(
            ents[i : i + M.ENT]
            for i in range(0, len(ents), M.ENT)
            if ents[i + M.E_CID] != cid
        )
    )
    eid = max(
        int.from_bytes(ents[i + M.E_EID : i + M.E_EID + 4], "little")
        for i in range(0, len(ents), M.ENT)
    )
    for k, t in enumerate(final):
        e = bytearray(M.ENT)
        e[M.E_TEAM : M.E_TEAM + 4] = t.to_bytes(4, "little")
        e[M.E_EID : M.E_EID + 4] = (eid + 1 + k).to_bytes(4, "little")
        e[M.E_CID], e[M.E_ORDER] = cid, k + 1
        ents += e
    regs[ri + M.R_TEAMS] = (regs[ri + M.R_TEAMS] & 0xC0) | (len(final) & 0x3F)

    if new_slot is not None and line_n is not None:
        if "slot=" in lines[line_n]:
            a0 = lines[line_n].index("slot=")
            a1 = lines[line_n].index(" ", a0)
            lines[line_n] = (
                lines[line_n][:a0] + "slot=%d" % new_slot + lines[line_n][a1:]
            )
    if line_n is not None:
        a0 = lines[line_n].index("clubs=")
        a1 = lines[line_n].index(" ", a0)
        lines[line_n] = (
            lines[line_n][:a0] + "clubs=%d" % len(final) + lines[line_n][a1:]
        )

    open(os.path.join(base, "Team.bin"), "wb").write(pesdb.wesys_pack(bytes(raw)))
    open(os.path.join(base, "Player.bin"), "wb").write(pesdb.wesys_pack(bytes(players)))
    open(os.path.join(base, "PlayerAssignment.bin"), "wb").write(
        pesdb.wesys_pack(bytes(assigns))
    )
    open(os.path.join(base, "CompetitionRegulation.bin"), "wb").write(
        pesdb.wesys_pack(bytes(regs))
    )
    open(os.path.join(base, "CompetitionEntry.bin"), "wb").write(
        pesdb.wesys_pack(bytes(ents))
    )
    io.open(wf, "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
    print(
        "done: %d entries, %d new club(s), %d new player(s)"
        % (len(final), n_clone, made)
    )
    print("line:", lines[line_n])
    return 0


if __name__ == "__main__":
    sys.exit(main())
