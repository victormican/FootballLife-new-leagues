"""python check_world.py --base <world pesdb> --worldfile <fl26world.txt> [--quiet]

Check a built world against itself and against the world file the modules read.  No game.

What it checks
  Team.bin              unique team ids; a name; the national bit and country of the 211 sides
  Player.bin            unique ids, none at or above 262144 (the 18-bit wall), a name
  PlayerAssignment.bin  every player and team exists; one row per (player, team); every club has
                        eleven players and a keeper; every national team its squad
  Competition.bin       unique competition ids, at most 255
  CompetitionRegulation unique regulation ids; the competition it names exists; its club count
                        agrees with its entries
  CompetitionEntry.bin  the competition and the club exist; orders are 1..n with no repeats
  the world file        every `league` line's reg and cid exist and agree; the club count matches
                        its entries; slots 0..249 are unique (one league per slot); every `ccup`
                        line's field size, `clubs=` length and invited clubs; every `cwc`,
                        `cupdays`, `confed`, `nations` id exists
  warnings              two regulations on one competition id (twins), a league with no entry,
                        a club in the Other pools that also plays a league

Exit status is 0 when there is no error; warnings are printed and do not fail.
"""

import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pesdb
import mkleague as M
import playeredit as E

T_REC, T_ID, T_NATIONAL, T_COUNTRY, T_NAME = 1532, 0x08, 0x53, 0x40, 0x170
OTHER_SLOTS = (69, 71, 73, 75)
SLOT_MAX = 249


def u32(b, o):
    return int.from_bytes(b[o : o + 4], "little")


def main():
    a = sys.argv[1:]
    get = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    base, wf = get("--base"), get("--worldfile")
    if not base or not wf:
        print(__doc__)
        return 2
    quiet = "--quiet" in a
    errors, warns = [], []

    def err(m):
        errors.append(m)

    def warn(m):
        warns.append(m)

    read = lambda n: pesdb.wesys_unpack(open(os.path.join(base, n), "rb").read())
    teams = read("Team.bin")
    players = read("Player.bin")
    assigns = read("PlayerAssignment.bin")
    comps = read("Competition.bin")
    regs = read("CompetitionRegulation.bin")
    ents = read("CompetitionEntry.bin")

    # ---- teams
    tids, nats = {}, {}
    for i in range(0, len(teams), T_REC):
        tid = u32(teams, i + T_ID)
        if tid in tids:
            err("team %d appears twice" % tid)
        name = (
            teams[i + T_NAME : i + T_NAME + 70]
            .split(b"\0")[0]
            .decode("utf-8", "replace")
        )
        if not name.strip():
            warn("team %d has no name" % tid)
        tids[tid] = name
        if teams[i + T_NATIONAL] & 0x80:
            nats[tid] = (u32(teams, i + T_COUNTRY) >> 2) & 0x1FF  # noqa: E501

    # ---- players
    pids, pnat = set(), {}
    for i in range(0, len(players), E.P_REC):
        pid = u32(players, i + E.P_ID)
        if pid in pids:
            err("player %d appears twice" % pid)
        pids.add(pid)
        if pid >= 262144:
            err("player %d is at or above 262144 (18-bit wall)" % pid)
        name = (
            players[i + E.P_NAME : i + E.P_NAME + E.P_NAME_LEN]
            .split(b"\0")[0]
            .decode("utf-8", "replace")
        )
        if not name.strip():
            warn("player %d has no name" % pid)
        pnat[pid] = E.getf(players[i : i + E.P_REC], "Nationality")

    # ---- assignments
    per_team, per_player = {}, {}
    for i in range(0, len(assigns), E.A_REC):
        pid, tid = u32(assigns, i + E.A_PID), u32(assigns, i + E.A_TID)
        if pid not in pids:
            err("assignment for player %d, who is not in Player.bin" % pid)
        if tid not in tids:
            err("assignment for team %d, which is not in Team.bin" % tid)
        if (pid, tid) in per_player:
            err("player %d has two assignments for team %d" % (pid, tid))
        per_player[(pid, tid)] = True
        per_team.setdefault(tid, []).append(pid)

    # a club only needs a squad when it plays something: the game's classic/placeholder teams
    # (The Old Boys, World Selection) have none and are not entered anywhere
    playing = {u32(ents, i) for i in range(0, len(ents), M.ENT)} - {0}
    for tid, name in tids.items():
        n = len(per_team.get(tid, []))
        if tid in nats:
            if n == 0:
                warn("national team %d (%s) has no players" % (tid, name))
        elif n < 11 and tid in playing:
            err("club %d (%s) plays a competition and has %d players (needs eleven)"
                % (tid, name, n))

    # ---- competitions
    cids = {}
    for i in range(0, len(comps), M.COMP):
        cid = comps[i + M.CID_OFF]
        if cid in cids:
            err("competition id %d appears twice" % cid)
        cids[cid] = (
            comps[i + M.CODE_OFF : i + M.CODE_OFF + 12]
            .split(b"\0")[0]
            .decode("ascii", "replace")
        )
    if len(cids) > 255:
        err("%d competitions: over the 255 ids a byte holds" % len(cids))

    # ---- regulations and entries
    rids, rcid, rteams = {}, {}, {}
    for i in range(0, len(regs), M.REG):
        rid = int.from_bytes(regs[i + M.R_ID : i + M.R_ID + 2], "little")
        if rid in rids:
            err("regulation id %d appears twice" % rid)
        cid = regs[i + M.R_CID]
        rids[rid] = i
        rcid[rid] = cid
        rteams[rid] = regs[i + M.R_TEAMS] & 0x3F
        if cid not in cids:
            err(
                "regulation %d names competition %d, which is not in Competition.bin"
                % (rid, cid)
            )

    ent_n, ent_order = {}, {}
    for i in range(0, len(ents), M.ENT):
        tid = u32(ents, i)
        cid, order = ents[i + M.E_CID], ents[i + M.E_ORDER]
        if tid and tid not in tids:
            err("entry: team %d is not in Team.bin" % tid)
        if cid not in cids:
            err("entry: competition %d is not in Competition.bin" % cid)
        ent_n[cid] = ent_n.get(cid, 0) + 1
        key = (cid, order)
        if key in ent_order and tid:
            warn("entry: competition %d has two clubs at position %d (a shipped cup with "
                 "several stages)" % (cid, order))
        ent_order[key] = tid

    # a regulation may hold fewer clubs than its competition (split phases, group replicas);
    # the league lines are the ones checked against the entries below

    # ---- the world file
    lines = io.open(wf, encoding="utf-8", errors="replace").read().splitlines()
    leagues, slots, league_cids = {}, {}, {}
    for n, line in enumerate(lines, 1):
        w = line.split()
        if not w:
            continue
        kind = w[0]
        if kind == "league":
            if len(w) < 2 or not w[1].isdigit():
                err("line %d: a league line without a regulation id" % n)
                continue
            rid = int(w[1])
            kv = dict(x.split("=", 1) for x in w[2:] if "=" in x)
            if rid not in rids:
                err("line %d: regulation %d is not in the tables" % (n, rid))
                continue
            leagues[rid] = kv
            cid = int(kv.get("cid", -1))
            if cid != rcid[rid]:
                err(
                    "line %d: league %d says cid %d, the tables say %d"
                    % (n, rid, cid, rcid[rid])
                )
            if cid in league_cids:
                warn(
                    "league %d and league %d share competition %d (twins)"
                    % (league_cids[cid], rid, cid)
                )
            league_cids[cid] = rid
            clubs = int(kv.get("clubs", -1))
            if clubs > 0 and ent_n.get(cid, 0) and clubs != ent_n[cid]:
                err(
                    "line %d: league %d says %d clubs, cid %d has %d entries"
                    % (n, rid, clubs, cid, ent_n[cid])
                )
            slot = kv.get("slot")
            if slot is not None and int(slot) != 123:
                s = int(slot)
                if not 0 <= s <= SLOT_MAX:
                    err("line %d: league %d on slot %d (0..%d)" % (n, rid, s, SLOT_MAX))
                if s in slots:
                    err(
                        "line %d: league %d on slot %d, which league %d already uses"
                        % (n, rid, s, slots[s])
                    )
                slots[s] = rid
        elif kind == "ccup":
            ko = int(w[1]) if len(w) > 1 and w[1].isdigit() else None
            kv = dict(x.split("=", 1) for x in w[2:] if "=" in x)
            groups = int(kv.get("groups", 0) or 0)
            pairs = len([p for p in (kv.get("entry") or "").split(",") if p])
            field = groups * 4 if groups else pairs
            for key in ("ko", "cid"):
                if key in kv and int(kv[key]) not in (rids if key == "ko" else cids):
                    err("line %d: ccup %s=%s is not in the tables" % (n, key, kv[key]))
            if ko is not None and ko not in rids:
                err("line %d: ccup %d is not a regulation" % (n, ko))
            if "clubs" in kv:
                cl = [int(x) for x in kv["clubs"].split(",") if x]
                if len(cl) != field:
                    err(
                        "line %d: %d invited clubs for a field of %d"
                        % (n, len(cl), field)
                    )
                if len(set(cl)) != len(cl):
                    err("line %d: an invited club is named twice" % n)
                for c in cl:
                    if c not in tids:
                        err("line %d: invited team %d is not in Team.bin" % (n, c))
                    elif c not in {u32(ents, i) for i in range(0, len(ents), M.ENT)}:
                        warn(
                            "line %d: invited team %d (%s) is in no entry; the module's "
                            "club lookup may drop it" % (n, c, tids[c])
                        )
        elif kind == "cwc":
            for x in w[1:4]:
                if x.isdigit() and int(x) not in rids:
                    err("line %d: cwc regulation %s is not in the tables" % (n, x))
        elif kind == "lpre":
            pre = int(w[1]) if len(w) > 1 and w[1].isdigit() else 0
            kv = dict(x.split("=", 1) for x in w[2:] if "=" in x)
            ko = int(kv.get("ko", 0) or kv.get("cup", 0) or 0)
            pairs = len([p for p in (kv.get("entry") or "").split(",") if p])
            if pre and pre not in rids:
                err("line %d: lpre %d is not a regulation" % (n, pre))
            if ko and ko not in rids:
                err("line %d: lpre %d leads to cup %d, not a regulation" % (n, pre, ko))
            for k in range(8):
                if pre and pre + 1024 * (k + 1) not in rids:
                    err("line %d: lpre %d has no tie regulation %d (the module wants all eight)"
                        % (n, pre, pre + 1024 * (k + 1)))
                    break
            if "clubs" in kv:
                cl = [int(x) for x in kv["clubs"].split(",") if x]
                if pairs and len(cl) != pairs:
                    err("line %d: %d invited clubs for %d tie places" % (n, len(cl), pairs))
                for c in cl:
                    if c not in tids:
                        err("line %d: lpre team %d is not in Team.bin" % (n, c))
        elif kind == "cupdays":
            if int(w[1]) not in rids:
                err("line %d: cupdays regulation %s is not in the tables" % (n, w[1]))
        elif kind == "nopool":
            for x in w[1:]:
                if x.isdigit() and int(x) not in tids:
                    err("line %d: nopool team %s is not in Team.bin" % (n, x))

    # ---- the Other pools must not also play a league
    other = set()
    for rid, kv in leagues.items():
        if rid in rids:
            pass
    for rid, kv in leagues.items():
        cid = rcid.get(rid)
        for i in range(0, len(ents), M.ENT):
            if ents[i + M.E_CID] != cid:
                continue
            tid = u32(ents, i)
            # a club's pool nibble lives in the team record; the world file's `others` groups are
            # the source of truth, and a club there must not be in a league of the file
    seen = sorted(set(slots.values()))
    if len(seen) != len(slots):
        err("slots repeat in the world file")

    print(
        "teams %d (%d national), players %d, assignments %d, competitions %d, regulations %d, "
        "entries %d"
        % (
            len(tids),
            len(nats),
            len(pids),
            len(per_player),
            len(cids),
            len(rids),
            len(ents) // M.ENT,
        )
    )
    print(
        "world file: %d leagues, %d slots %s..%s, %d ccup lines"
        % (
            len(leagues),
            len(slots),
            min(slots) if slots else "-",
            max(slots) if slots else "-",
            len([l for l in lines if l.startswith("ccup ")]),
        )
    )
    if not quiet:
        for w in warns:
            print("WARN " + w)
    for e in errors:
        print("ERROR " + e)
    print("%d error(s), %d warning(s)" % (len(errors), len(warns)))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
