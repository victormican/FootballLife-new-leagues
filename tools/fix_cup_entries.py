"""python fix_cup_entries.py --base <pesdb> --worldfile <fl26world.txt>

A cup with no `CompetitionEntry` rows makes the game drop the whole Kick Off > Cup list (menu in
blank).  Earlier repairs removed the entries of some cups; this writes them again from the world
line's own `clubs=` (team ids) or `entry=` list (`<league regulation>:<position>`, resolved through
the league's entry list; `0:<team id>` is the team itself).
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pesdb
import mkleague as M


def main():
    a = sys.argv[1:]
    get = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    base, wf = get("--base"), get("--worldfile")
    if not base or not wf:
        print(__doc__)
        return 1

    regs = M.load(base, "CompetitionRegulation.bin")
    ents = bytearray(M.load(base, "CompetitionEntry.bin"))
    cid_of_reg = {
        regs[i + M.R_ID]: regs[i + M.R_CID] for i in range(0, len(regs), M.REG)
    }
    listed = {}
    for i in range(0, len(ents), M.ENT):
        listed.setdefault(ents[i + M.E_CID], []).append(
            (
                ents[i + M.E_ORDER],
                int.from_bytes(ents[i + M.E_TEAM : i + M.E_TEAM + 4], "little"),
            )
        )
    eid = max(
        int.from_bytes(ents[i + M.E_EID : i + M.E_EID + 4], "little")
        for i in range(0, len(ents), M.ENT)
    )

    fixed = 0
    for line in open(wf, encoding="utf-8", errors="replace").read().splitlines():
        if not line.startswith("ccup "):
            continue
        kv = dict(x.split("=", 1) for x in line.split()[2:] if "=" in x)
        if "cid" not in kv:
            continue
        cid = int(kv["cid"])
        if listed.get(cid):
            continue
        clubs = []
        if kv.get("clubs"):
            clubs = [int(x) for x in kv["clubs"].split(",") if x.strip()]
        else:
            for e in kv.get("entry", "").split(","):
                if ":" not in e:
                    continue
                r, _, p = e.partition(":")
                r, p = int(r), int(p)
                if r == 0:
                    clubs.append(p)
                elif p >= 1:
                    lst = [t for _o, t in sorted(listed.get(cid_of_reg.get(r, -1), []))]
                    if len(lst) >= p:
                        clubs.append(lst[p - 1])
        clubs = [c for c in dict.fromkeys(clubs) if c]
        for k, t in enumerate(clubs):
            e = bytearray(M.ENT)
            e[M.E_TEAM : M.E_TEAM + 4] = t.to_bytes(4, "little")
            eid += 1
            e[M.E_EID : M.E_EID + 4] = eid.to_bytes(4, "little")
            e[M.E_CID] = cid & 0xFF
            e[M.E_ORDER] = k + 1
            ents += e
        listed[cid] = [(0, t) for t in clubs]
        fixed += 1
        print("cid %-3d: %2d entradas  %s" % (cid, len(clubs), kv.get("name", "?")))

    print("%d copa(s) con entradas nuevas" % fixed)
    if fixed:
        open(os.path.join(base, "CompetitionEntry.bin"), "wb").write(
            pesdb.wesys_pack(bytes(ents))
        )
        print("written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
