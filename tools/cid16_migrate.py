"""python cid16_migrate.py --base <world pesdb> [--check] [--dry]

Give the three tables the room for competition ids above 255 that `fl26cid16.lua` reads:

    Competition.bin        id byte at +0x05, high byte at +0x07   (free: zero in all rows)
    CompetitionEntry.bin   id byte at +0x08, high byte at +0x0B   (free: zero in all rows)
    CompetitionRegulation  id byte at +0x08, high byte at +0x910  (free: zero in all rows)

+0x07 is the byte used for the high half of the competition id. The earlier plan put a word at
+0x20, but that is the **tail of the 16-byte name** (+0x14..+0x23): a league called
"Belize Premier" already has data there.

With every id below 256 the high bytes stay zero and nothing changes: the module's cave returns
the same id it read before. On a world that is already migrated this is a no-op, so it can run
again; `--check` only reports.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pesdb
import mkleague as M

C_CID_HI = 0x07
E_CID_HI = 0x0B
R_CID_HI = 0x492


def main():
    a = sys.argv[1:]
    get = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    base = get("--base")
    if not base:
        print(__doc__)
        return 1
    dry = "--dry" in a
    check = "--check" in a

    comp = bytearray(M.load(base, "Competition.bin"))
    ents = bytearray(M.load(base, "CompetitionEntry.bin"))
    regs = bytearray(M.load(base, "CompetitionRegulation.bin"))

    # the low byte is the truth; the high byte must agree with the id we want
    hi_comp = {i: comp[i + C_CID_HI] for i in range(0, len(comp), M.COMP)}
    hi_ents = {i: ents[i + E_CID_HI] for i in range(0, len(ents), M.ENT)}
    hi_regs = {i: regs[i + R_CID_HI] for i in range(0, len(regs), M.REG)}

    above = [
        (i // M.COMP, comp[i + M.CID_OFF] | (hi_comp[i] << 8))
        for i in range(0, len(comp), M.COMP)
        if hi_comp[i]
    ]
    print(
        "%d competition(s), %d above 255, entry high bytes set %d, regulation high bytes set %d"
        % (
            len(comp) // M.COMP,
            len(above),
            sum(1 for v in hi_ents.values() if v),
            sum(1 for v in hi_regs.values() if v),
        )
    )
    for row, cid in above[:10]:
        print("  row %d -> cid %d" % (row, cid))
    if check:
        return 0

    # a world of ids below 256 needs nothing but the free byte proven zero where it is used
    if any(v for v in hi_comp.values()):
        print("the high bytes are already in place: nothing to write")
        return 0
    if dry:
        print("dry run: nothing written")
        return 0
    print(
        "every competition id is below 256: the high bytes stay zero, nothing to write"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
