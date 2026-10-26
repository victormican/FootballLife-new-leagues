"""python real_league.py --base <pesdb> --worldfile <fl26world.txt> --country 58
                     --name "Premier League (Egipto)" --teams 10 [--reg 60] [--dry]

Turn one of our generic leagues into the real league of a country: the game's own clubs of that
country first, then our generic clubs, until --teams. The league keeps its regulation and slot
(nothing new is created); only its name, its club list and the regulation's team count change.

Rules (2026-10-25):
  * a league is `nombre real (Pais) N`, N = its teams;
  * real clubs of the game (team id < 71578) always come before our generics (71578+);
  * the rest of the country's real clubs are left for a second division.

--country is the Country.bin id; --reg picks the league when the country has more than one
(the one with the most clubs of that country is used by default).
"""

import io
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pesdb
import mkleague as M

T_REC, T_ID, T_COUNTRY, T_NATIONAL = 1532, 0x08, 0x46, 0x53
GAME_CLUB_MAX = 71578


def main():
    a = sys.argv[1:]
    get = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    base, wf = get("--base"), get("--worldfile")
    cid_country, name = get("--country"), get("--name")
    if not base or not wf or not cid_country or not name:
        print(__doc__)
        return 1
    country, want = int(cid_country), int(get("--teams", "10"))
    dry = "--dry" in a

    shipped = os.path.join(os.environ.get("APPDATA", ""), "FL26ModStudio", "tables", "common", "etc", "pesdb")
    try:
        E0 = pesdb.wesys_unpack(open(os.path.join(shipped, "CompetitionEntry.bin"), "rb").read())
        placed = {int.from_bytes(E0[i + 4:i + 8], "little") for i in range(0, len(E0), 16)}
    except Exception:
        placed = set()
    teams_raw = pesdb.wesys_unpack(open(os.path.join(base, "Team.bin"), "rb").read())
    real, generic = [], []
    for i in range(0, len(teams_raw), T_REC):
        r = teams_raw[i : i + T_REC]
        tid = int.from_bytes(r[T_ID : T_ID + 4], "little")
        if not tid or (r[T_NATIONAL] & 0x80):
            continue
        if (
            (int.from_bytes(r[T_COUNTRY : T_COUNTRY + 2], "little") >> 2) & 0x1FF
        ) != country:
            continue
        if tid < GAME_CLUB_MAX:
            if tid not in placed:
                real.append(tid)
        else:
            generic.append(tid)
    real.sort(), generic.sort()
    pick = (real + generic)[:want]
    if len(pick) < want:
        print("only %d club(s) for country %d" % (len(pick), country))
        return 1

    ents = bytearray(M.load(base, "CompetitionEntry.bin"))
    regs = bytearray(M.load(base, "CompetitionRegulation.bin"))
    by_cid = {}
    for i in range(0, len(ents), M.ENT):
        by_cid.setdefault(ents[i + M.E_CID], []).append(i)
    lines = io.open(wf, encoding="utf-8", errors="replace").read().splitlines()

    target = None
    reg = get("--reg")
    for l in lines:
        if not l.startswith("league "):
            continue
        w = l.split()
        kv = dict(x.split("=", 1) for x in w[2:] if "=" in x)
        rid, cid = int(w[1]), int(kv.get("cid", "-1"))
        if reg and rid != int(reg):
            continue
        if reg:
            target = (rid, cid)
            break
        if target is None and "(" in kv.get("name", ""):
            continue
        teams = [
            int.from_bytes(ents[i + M.E_TEAM : i + M.E_TEAM + 4], "little")
            for i in by_cid.get(cid, [])
        ]
        score = sum(1 for t in teams if t in real)
        if teams and (target is None or score > target[2]):
            target = (rid, cid, score)
    if target is None:
        print("no league for that country in the world")
        return 1
    rid, cid = target[0], target[1]
    print(
        "league reg %d cid %d -> %s, %d clubs (%d real, %d generic)"
        % (
            rid,
            cid,
            name,
            want,
            len([t for t in pick if t < GAME_CLUB_MAX]),
            len([t for t in pick if t >= GAME_CLUB_MAX]),
        )
    )
    if dry:
        print("dry run")
        return 0

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
    for k, t in enumerate(pick):
        e = bytearray(M.ENT)
        e[M.E_TEAM : M.E_TEAM + 4] = t.to_bytes(4, "little")
        eid += 1
        e[M.E_EID : M.E_EID + 4] = eid.to_bytes(4, "little")
        e[M.E_CID] = cid & 0xFF
        e[M.E_ORDER] = k + 1
        ents += e

    for i in range(0, len(regs), M.REG):
        if int.from_bytes(regs[i + M.R_ID : i + M.R_ID + 2], "little") != rid:
            continue
        regs[i + M.R_TEAMS] = (regs[i + M.R_TEAMS] & ~0x3F) | want
        rc = bytearray(regs[i : i + M.REG])
        M.put_names(rc, 0, name)
        regs[i : i + M.REG] = rc

    open(os.path.join(base, "CompetitionEntry.bin"), "wb").write(
        pesdb.wesys_pack(bytes(ents))
    )
    open(os.path.join(base, "CompetitionRegulation.bin"), "wb").write(
        pesdb.wesys_pack(bytes(regs))
    )

    out = []
    for l in lines:
        if l.startswith("league %d " % rid):
            kv = dict(x.split("=", 1) for x in l.split()[2:] if "=" in x)
            l = (
                "league %d cid=%s region=%s country=%s conf=%s slot=%s tier=%s promote=%s demote=%s "
                "clubs=%d legs=%s kickoff=%s name=%s"
                % (
                    rid,
                    cid,
                    kv.get("region", "25"),
                    kv.get("country", "200"),
                    kv.get("conf", "2"),
                    kv.get("slot", "-1"),
                    kv.get("tier", "1"),
                    kv.get("promote", "0"),
                    kv.get("demote", "0"),
                    want,
                    kv.get("legs", "2"),
                    kv.get("kickoff", "99"),
                    name,
                )
            )
        out.append(l)
    io.open(wf, "w", encoding="utf-8", newline="\n").write("\n".join(out) + "\n")
    print("world: league %d name=%s clubs=%d" % (rid, name, want))
    return 0


if __name__ == "__main__":
    sys.exit(main())
