"""python cid16_migrate.py --base <world pesdb> [--dry]

Write every competition's id as a 16-bit word at `Competition.bin` +0x20.

Why: the engine keeps a competition id in 16 bits, but the table stores it as a byte at +5.
The byte at +4 is **not** free (competitions 23..27 carry 27 there, their parent phase), so the
word goes at +0x20, four bytes that are zero in all 249 rows of the test world. The census read
in `fl26cid16.lua` is `movzx ecx, word [rdi+0x20]`.

`CompetitionEntry.bin` already has a free byte at +0x0b for the high half and
`CompetitionRegulation.bin` at +0x910; this tool fills those too, leaving every id below 256
exactly as it was (high byte 0).

Idempotent: running it again rewrites the same words. Without `--dry` it writes the three
tables back.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pesdb
import mkleague as M

CID_WORD_OFF = 0x20
E_CID_HI = 0x0B
R_CID_HI = 0x910


def main():
    a = sys.argv[1:]
    get = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    base = get("--base")
    if not base:
        print(__doc__)
        return 1
    dry = "--dry" in a
    comp = bytearray(M.load(base, "Competition.bin"))
    ents = bytearray(M.load(base, "CompetitionEntry.bin"))
    regs = bytearray(M.load(base, "CompetitionRegulation.bin"))

    n = 0
    for i in range(0, len(comp), M.COMP):
        cid = comp[i + M.CID_OFF]
        assert comp[i + CID_WORD_OFF : i + CID_WORD_OFF + 4] == b"\0\0\0\0", (
            "row %d already carries something at +0x20" % (i // M.COMP)
        )
        comp[i + CID_WORD_OFF : i + CID_WORD_OFF + 2] = cid.to_bytes(2, "little")
        n += 1
    for i in range(0, len(ents), M.ENT):
        cid = ents[i + M.E_CID]
        ents[i + E_CID_HI] = (cid >> 8) & 0xFF
    for i in range(0, len(regs), M.REG):
        cid = regs[i + M.R_CID]
        regs[i + R_CID_HI] = (cid >> 8) & 0xFF

    print("%d competition(s) with their id as a word at +0x%x" % (n, CID_WORD_OFF))
    if dry:
        print("dry run: nothing written")
        return 0
    open(os.path.join(base, "Competition.bin"), "wb").write(
        pesdb.wesys_pack(bytes(comp))
    )
    open(os.path.join(base, "CompetitionEntry.bin"), "wb").write(
        pesdb.wesys_pack(bytes(ents))
    )
    open(os.path.join(base, "CompetitionRegulation.bin"), "wb").write(
        pesdb.wesys_pack(bytes(regs))
    )
    print("written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
