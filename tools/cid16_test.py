"""python cid16_test.py --base <world pesdb> --worldfile <fl26world.txt>
                        --from 91 [--to 256] [--dry] [--revert]

Move one competition to an id above 255, the way the engine reads it after `fl26cid16.lua`:
`Competition.bin` keeps the id as a word at `+0x20`, the entries at `+8` (low) and `+0x0b`
(high), the regulation at `+8` (low) and `+0x910` (high).  The world file's `cid=` follows.

`--revert` puts it back below 256 (the low byte at +5, high bytes zero), so the same tool undoes
the test.

This is a test, not a migration: with the module installed and the tables written this way the
game must show and play that competition exactly as before.  Without the module the ids read as
0 (`+5`), which is why the two go together.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pesdb
import mkleague as M

CID_OFF = M.C_CID_HI
E_CID_HI = M.E_CID_HI
R_CID_HI = M.R_CID_HI


def main():
    a = sys.argv[1:]
    get = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    base, wf = get("--base"), get("--worldfile")
    if not base or not wf:
        print(__doc__)
        return 1
    src = int(get("--from", "0"))
    dst = int(get("--to", "0"))
    revert = "--revert" in a
    dry = "--dry" in a
    comp = bytearray(M.load(base, "Competition.bin"))
    ents = bytearray(M.load(base, "CompetitionEntry.bin"))
    regs = bytearray(M.load(base, "CompetitionRegulation.bin"))

    # the row we move: by the 16-bit id (low + high byte), else by the low byte
    row = None
    for i in range(0, len(comp), M.COMP):
        cid = M.comp_cid(comp, i)
        if cid == src or (comp[i + CID_OFF] == 0 and comp[i + M.CID_OFF] == src):
            row = i
            break
    if row is None:
        print("no competition with id %d" % src)
        return 1
    if not dst:
        print("--to is required")
        return 1
    target = dst
    print(
        "competition row %d: %d -> %d%s"
        % (row // M.COMP, src, target, " (revert)" if revert else "")
    )

    comp[row + M.CID_OFF] = target & 0xFF
    comp[row + CID_OFF] = (target >> 8) & 0xFF
    n = 0
    for i in range(0, len(ents), M.ENT):
        if (ents[i + M.E_CID] | (ents[i + E_CID_HI] << 8)) == src or (
            ents[i + E_CID_HI] == 0 and ents[i + M.E_CID] == src
        ):
            ents[i + M.E_CID] = target & 0xFF
            ents[i + E_CID_HI] = (target >> 8) & 0xFF
            n += 1
    for i in range(0, len(regs), M.REG):
        if (regs[i + M.R_CID] | (regs[i + R_CID_HI] << 8)) == src:
            regs[i + M.R_CID] = target & 0xFF
            regs[i + R_CID_HI] = (target >> 8) & 0xFF
    print("entries moved: %d" % n)
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
    lines = []
    for l in open(wf, encoding="utf-8", errors="replace").read().splitlines():
        if l.startswith("league ") or l.startswith("ccup "):
            i = l.index("cid=")
            j = l.index(" ", i)
            here = int(l[i + 4 : j])
            if here == src:
                l = l[:i] + "cid=%d" % target + l[j:]
        lines.append(l)
    open(wf, "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
    print("world file updated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
