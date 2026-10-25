"""python repair_cups.py --base <pesdb> --worldfile <fl26world.txt> [--dry]

Make the tables agree with the `ccup` lines of the world: a line whose competition id is not in
`Competition.bin` makes the game drop the whole Cup mode list (menu in blank), which is what
happened with `ccup 319 ... cid=146` and a table without 146.

For every line with a missing competition it copies the Libertadores' row (the shape every cup
here is built from), gives it the line's cid and a code, and writes its `CompetitionEntry` rows
from the line's `entry=` list (or its `clubs=` list when it has one). Leagues stay untouched.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pesdb
import mkleague as M

LIB_CID = 5


def entries_of(spec):
    return [e for e in spec.split(",") if e]


def main():
    a = sys.argv[1:]
    get = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    base, wf = get("--base"), get("--worldfile")
    if not base or not wf:
        print(__doc__)
        return 1
    dry = "--dry" in a

    comp = bytearray(M.load(base, "Competition.bin"))
    regs = bytearray(M.load(base, "CompetitionRegulation.bin"))
    ents = bytearray(M.load(base, "CompetitionEntry.bin"))
    rows = [comp[i : i + M.COMP] for i in range(0, len(comp), M.COMP)]
    lib = next(
        (
            r
            for r in rows
            if r[M.CID_OFF] == LIB_CID
        ),
        None,
    )
    if lib is None:
        print("no Libertadores row to copy")
        return 1
    have = {r[M.CID_OFF] for r in rows}
    cid_of_reg = {
        int.from_bytes(regs[i + M.R_ID : i + M.R_ID + 2], "little"): int.from_bytes(
            regs[i + M.R_CID : i + M.R_CID + 2], "little"
        )
        for i in range(0, len(regs), M.REG)
    }
    listed = {}
    for i in range(0, len(ents), M.ENT):
        cid = ents[i + M.E_CID]
        listed.setdefault(cid, []).append(
            (
                ents[i + M.E_ORDER],
                int.from_bytes(ents[i + M.E_TEAM : i + M.E_TEAM + 4], "little"),
            )
        )
    eid = max(
        int.from_bytes(ents[i + M.E_EID : i + M.E_EID + 4], "little")
        for i in range(0, len(ents), M.ENT)
    )

    lines = open(wf, encoding="utf-8", errors="replace").read().splitlines()
    fixed = 0
    for line in lines:
        if not line.startswith("ccup "):
            continue
        kv = dict(x.split("=", 1) for x in line.split()[2:] if "=" in x)
        if "cid" not in kv:
            continue
        cid = int(kv["cid"])
        if cid in have:
            continue
        row = bytearray(lib)
        row[M.CID_OFF] = cid & 0xff
        row[M.CID_OFF + 1] = (cid >> 8) & 0xff
        M.put(row, M.CODE_OFF, "FL_C%03d" % cid, M.COMP - M.CODE_OFF)
        if "conf" in line:
            conf = int(
                [x.split("=", 1)[1] for x in line.split() if x.startswith("conf=")][0]
            )
            row[M.FLAG_OFF] = (row[M.FLAG_OFF] & ~7) | conf
        rows.append(row)
        have.add(cid)
        clubs = []
        if kv.get("clubs"):
            clubs = [int(x) for x in kv["clubs"].split(",")]
        else:
            for e in entries_of(kv.get("entry", "")):
                r, _, p = e.partition(":")
                r, p = int(r), int(p)
                if r == 0:
                    clubs.append(p)
                elif p >= 1:
                    lst = [t for _o, t in sorted(listed.get(cid_of_reg.get(r, -1), []))]
                    if len(lst) >= p:
                        clubs.append(lst[p - 1])
        for k, t in enumerate(dict.fromkeys(clubs)):
            e = bytearray(M.ENT)
            e[M.E_TEAM : M.E_TEAM + 4] = t.to_bytes(4, "little")
            eid += 1
            e[M.E_EID : M.E_EID + 4] = eid.to_bytes(4, "little")
            e[M.E_CID] = cid & 0xff
            e[M.E_ORDER] = k + 1
            ents += e
        fixed += 1
        print("cid %d rebuilt: %d club(s), %s" % (cid, len(clubs), kv.get("name", "?")))

    print("%d competition(s) rebuilt" % fixed)
    if dry or not fixed:
        print("nothing written" if dry else "tables already agree")
        return 0
    open(os.path.join(base, "Competition.bin"), "wb").write(
        pesdb.wesys_pack(bytes(b"".join(rows)))
    )
    open(os.path.join(base, "CompetitionEntry.bin"), "wb").write(
        pesdb.wesys_pack(bytes(ents))
    )
    print("written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
