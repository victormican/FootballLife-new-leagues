"""python cup_entry_swap.py --base <pesdb> --cid <competition> --from "<team>" --to "<team>" [--dry]

Change one club of a competition's entry list for another one, by name (Team.bin +0x170), keeping
its position. Used for the Leagues Cup: the field came from the first sixteen MLS clubs, and one of
them (CF Montréal) is Canadian -- the cup must show only United States and Liga MX clubs.
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
    base, cid = get("--base"), get("--cid")
    old, new = get("--from"), get("--to")
    if not all((base, cid, old, new)):
        print(__doc__)
        return 2
    dry = "--dry" in a
    cid = int(cid)

    teams = pesdb.wesys_unpack(open(os.path.join(base, "Team.bin"), "rb").read())
    ents = bytearray(
        pesdb.wesys_unpack(
            open(os.path.join(base, "CompetitionEntry.bin"), "rb").read()
        )
    )

    tid_of, name_of = {}, {}
    for o in range(0, len(teams), 1532):
        r = teams[o : o + 1532]
        tid = int.from_bytes(r[8:12], "little")
        name = pesdb.cstr(r[0x170 : 0x170 + 70]).strip()
        name_of[tid] = name
        tid_of.setdefault(name.lower(), []).append(tid)

    def tid(name):
        hits = tid_of.get(name.lower(), [])
        if len(hits) != 1:
            raise SystemExit("%r matches %d teams" % (name, len(hits)))
        return hits[0]

    src, dst = tid(old), tid(new)
    rows = [
        k
        for k in range(0, len(ents), M.ENT)
        if ents[k + M.E_CID] == cid and int.from_bytes(ents[k : k + 4], "little") == src
    ]
    if len(rows) != 1:
        raise SystemExit(
            "%s is in %d entries of competition %d" % (old, len(rows), cid)
        )
    if any(
        ents[k + M.E_CID] == cid and int.from_bytes(ents[k : k + 4], "little") == dst
        for k in range(0, len(ents), M.ENT)
    ):
        raise SystemExit("%s is already in competition %d" % (new, cid))

    k = rows[0]
    print(
        "cid %d, position %d: %s (%d) -> %s (%d)"
        % (cid, ents[k + M.E_ORDER], old, src, new, dst)
    )
    ents[k : k + 4] = dst.to_bytes(4, "little")
    if dry:
        print("dry run: nothing written")
        return 0
    open(os.path.join(base, "CompetitionEntry.bin"), "wb").write(
        pesdb.wesys_pack(bytes(ents))
    )
    print("written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
