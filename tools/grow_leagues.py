"""python grow_leagues.py --base <world pesdb> --worldfile <fl26world.txt>
                        [--clubs 20] [--big 5] [--big-clubs 30] [--dry]

Give the leagues of a world more clubs than they were built with: 10 -> 20 (or 30).

Why it can, without a Build: the number of clubs a league plays is the **six low bits of
`CompetitionRegulation.bin` +0x0b** (`mkleague.R_TEAMS`), and the clubs themselves are
`CompetitionEntry.bin` rows whose `order` is 1..n. The calendar is not stored per league; the
game lays the season out from that count and the regulation's dates, so a league grown here
plays the extra rounds. The world file's `clubs=` must say the same number (`check_world`
compares it with the entries).

The extra clubs are clones of one club of the world that already has a full squad (the same
rule `add_generic_leagues.py` uses): a Team.bin row with a new id and name, one
PlayerAssignment + Player per squad place with ids `playeredit.free_ids` hands out. Nothing
is regenerated: ids, names, kits and the other leagues stay exactly as they are.

`--big N` grows the first N leagues of the world file (the ones the recipe built, which are
the playable test leagues) to `--big-clubs`; every other league goes to `--clubs`.
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
A_REC, A_EID, A_PID, A_TID = 16, 0x00, 0x04, 0x08


def main():
    a = sys.argv[1:]
    get = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    base, wf = get("--base"), get("--worldfile")
    if not base or not wf:
        print(__doc__)
        return 1
    want = int(get("--clubs", "20"))
    nbig = int(get("--big", "5"))
    big = int(get("--big-clubs", "30"))
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
        if len(by_team.get(tid, [])) >= 22:
            clubs.append((tid, o))
    if not clubs:
        print("no club with 22 players to copy")
        return 1
    tt, toff = clubs[-1]
    squad = by_team[tt][:22]

    reg_of_cid = {}
    for i in range(0, len(regs), M.REG):
        reg_of_cid.setdefault(regs[i + M.R_CID], i)
    ent_of_cid = {}
    for i in range(0, len(ents), M.ENT):
        ent_of_cid.setdefault(ents[i + M.E_CID], []).append(i)

    lines = io.open(wf, encoding="utf-8", errors="replace").read().splitlines()
    leagues = []
    for n, line in enumerate(lines):
        w = line.split()
        if not w or w[0] != "league" or not w[1].isdigit():
            continue
        kv = dict(x.split("=", 1) for x in w[2:] if "=" in x)
        leagues.append((n, int(w[1]), kv))
    print(
        "%d league line(s); %d to %d clubs, the first %d to %d"
        % (len(leagues), len(leagues) - nbig, want, nbig, big)
    )

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

    plan = []
    need_clubs = need_players = 0
    for k, (n, reg, kv) in enumerate(leagues):
        cid = int(kv.get("cid", "-1"))
        have = int(kv.get("clubs", "0") or 0)
        target = big if k < nbig else want
        if kv.get("name") == "Oceania":
            continue
        if cid < 0 or have <= 0 or target <= have:
            continue
        if cid not in reg_of_cid:
            print("  league %d: cid %d has no regulation -- left alone" % (reg, cid))
            continue
        plan.append((n, reg, cid, have, target, kv.get("name", "")))
        need_clubs += target - have
        need_players += (target - have) * len(squad)
    print(
        "%d league(s) to grow: %d clubs and %d players"
        % (len(plan), need_clubs, need_players)
    )


    # the (region, country, conf) triples the world's own test leagues already use: known good
    # in the menus (flag, heading, category), so a generic league wears one of them in turn
    # instead of all of them being Croatia
    pool = []
    for _n, _reg, kv in leagues:
        if "Generic" in kv.get("name", "") or kv.get("name") == "Oceania":
            continue
        if all(k in kv for k in ("region", "country", "conf")):
            t = (int(kv["region"]), int(kv["country"]), int(kv["conf"]))
            if t not in pool:
                pool.append(t)
    if not pool:
        pool = [(29, 200, 2)]
    print("  country pool: %s" % ", ".join("%d/%d/%d" % t for t in pool))

    used = {
        int.from_bytes(players[i + E.P_ID : i + E.P_ID + 4], "little")
        for i in range(0, len(players), E.P_REC)
    }
    more = E.free_ids(players, need_players)
    if len(more) < need_players:
        print("only %d free player ids for %d players" % (len(more), need_players))
        return 1
    made_clubs = made_players = 0
    pid_off = {
        int.from_bytes(players[i + E.P_ID : i + E.P_ID + 4], "little"): i
        for i in range(0, len(players), E.P_REC)
    }

    for gi, (n, reg, cid, have, target, name) in enumerate(plan):
        region, country, conf = pool[gi % len(pool)]
        ri = reg_of_cid[cid]
        rname = regs[ri + M.R_NAME:ri + M.R_NAME + 40].split(b"\0")[0].decode(
            "utf-8", "replace"
        )
        regs[ri + M.R_TEAMS] = (regs[ri + M.R_TEAMS] & 0xC0) | (target & 0x3F)
        ci = next(
            (i for i in range(0, len(comp), M.COMP) if comp[i + M.CID_OFF] == cid), None
        )
        if ci is not None:
            comp[ci + M.REGION_OFF] = M.enc_region(region)
        for field, val in (("region", region), ("country", country), ("conf", conf)):
            key = "%s=" % field
            if key in lines[n]:
                a0 = lines[n].index(key)
                a1 = lines[n].index(" ", a0)
                lines[n] = lines[n][:a0] + "%s=%d" % (field, val) + lines[n][a1:]
        for ei in ent_of_cid.get(cid, []):
            tid0 = int.from_bytes(ents[ei + M.E_TEAM:ei + M.E_TEAM + 4], "little")
            for ti in range(0, len(raw), T_REC):
                if int.from_bytes(raw[ti + T_ID:ti + T_ID + 4], "little") == tid0:
                    old_c = int.from_bytes(raw[ti + T_COUNTRY:ti + T_COUNTRY + 2], "little")
                    raw[ti + T_COUNTRY:ti + T_COUNTRY + 2] = (
                        (old_c & ~(0x1FF << 2)) | ((country & 0x1FF) << 2)
                    ).to_bytes(2, "little")
                    break
        order = (
            max(
                int.from_bytes(ents[i + M.E_ORDER : i + M.E_ORDER + 1], "little")
                for i in ent_of_cid[cid]
            )
            if ent_of_cid[cid]
            else have
        )
        for j in range(have, target):
            tid = top + 1 + made_clubs
            row = bytearray(raw[toff : toff + T_REC])
            row[T_ID : T_ID + 4] = tid.to_bytes(4, "little")
            row[T_ALT : T_ALT + 4] = (top_alt + 1 + made_clubs).to_bytes(4, "little")
            cname = "%s Club %02d" % (rname, j + 1)
            for s in range(T_NAME_SLOTS):
                off = T_NAME + s * T_NAME_STEP
                if off + T_NAME_LEN <= T_REC:
                    b = cname.encode("utf-8")[: T_NAME_LEN - 1]
                    row[off : off + T_NAME_LEN] = b + bytes(T_NAME_LEN - len(b))
            code = ("G%02d%02d" % (made_clubs // 100, made_clubs % 100))[:3]
            row[T_ABBR : T_ABBR + T_ABBR_LEN] = code.encode("ascii")[
                : T_ABBR_LEN - 1
            ].ljust(T_ABBR_LEN, b"\0")
            old_c = int.from_bytes(row[T_COUNTRY:T_COUNTRY + 2], "little")
            row[T_COUNTRY:T_COUNTRY + 2] = (
                (old_c & ~(0x1FF << 2)) | ((country & 0x1FF) << 2)
            ).to_bytes(2, "little")
            raw += row
            for ai in squad:
                pid = more[made_players]
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
                    "%s Club %02d Player %02d"
                    % (rname, j + 1, (made_players % len(squad)) + 1)
                )
                E.setf(pr, "Nationality", country)
                players += pr
                made_players += 1
            e = bytearray(M.ENT)
            e[M.E_TEAM : M.E_TEAM + 4] = tid.to_bytes(4, "little")
            e[M.E_EID : M.E_EID + 4] = (eid_top + 1 + made_players).to_bytes(
                4, "little"
            )
            e[M.E_CID], e[M.E_ORDER] = cid, order + 1
            order += 1
            ents += e
            made_clubs += 1
        if "name=" in lines[n]:
            a0 = lines[n].index("name=")
            lines[n] = lines[n][:a0] + "name=" + rname
        i = lines[n].index("clubs=")
        j = lines[n].index(" ", i)
        lines[n] = lines[n][:i] + "clubs=%d" % target + lines[n][j:]
        print("  league %d (%s): %d -> %d clubs, country %d" % (reg, rname, have, target, country))

    print("made %d clubs, %d players" % (made_clubs, made_players))
    if dry:
        print("dry run: nothing written")
        return 0
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
    print("written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
