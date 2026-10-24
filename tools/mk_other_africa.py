"""python mk_other_africa.py --base <world pesdb> --worldfile <fl26world.txt>
                           [--clubs 9030,9033] [--slot 75] [--dry]

Make the "Other Clubs (Africa)" group of Select Team show the African clubs that play no
competition at all.

Why it needs a competition: slot 75 is named by the switch at 0x140ea08e0, but its team list is
built by the game at boot from a filler the repository has measured as "never filled" for a
foreign club (docs/developers/fork, fl26clubs.c). `fl26clubs.dll` does replace the two readers
of those lists (count 0x1414d62c0, get 0x1414d6290) and serves the slots the world file names
from the regulation of the league on them -- slot 75 is one of them (fl26clubs.lua, SERVED).

So the group is a competition of its own on slot 75: a league whose clubs are exactly the
clubs in no competition, named like the heading it fills. `fl26slotnames` frees the slot's
shipped heading because a league of the world sits there, and the menus then read the name
from the regulation -- "Other Clubs (Africa)".

A league of two clubs is small but valid: two rounds, no calendar to speak of. Nothing else in
the world changes.
"""

import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pesdb
import mkleague as M

NAME = "Other Clubs (Africa)"
CODE = "FL_OAFR"


def main():
    a = sys.argv[1:]
    get = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    base, wf = get("--base"), get("--worldfile")
    if not base or not wf:
        print(__doc__)
        return 1
    slot = int(get("--slot", "75"))
    want = [int(x) for x in get("--clubs", "9030,9033").split(",") if x.strip()]
    dry = "--dry" in a

    comp = M.load(base, "Competition.bin")
    regs = M.load(base, "CompetitionRegulation.bin")
    ents = M.load(base, "CompetitionEntry.bin")
    raw = pesdb.wesys_unpack(open(os.path.join(base, "Team.bin"), "rb").read())
    T = 1532
    have = {
        int.from_bytes(raw[i + 8 : i + 12], "little") for i in range(0, len(raw), T)
    }
    teams = [t for t in want if t in have]
    if not teams:
        print("none of %s is in Team.bin" % want)
        return 1

    used_c = {comp[i + M.CID_OFF] for i in range(0, len(comp), M.COMP)}
    used_r = {
        int.from_bytes(regs[i + M.R_ID : i + M.R_ID + 2], "little")
        for i in range(0, len(regs), M.REG)
    }
    cid = next(c for c in range(88, 256) if c not in used_c)
    reg = next(r for r in range(176, 1024) if r not in used_r)
    print(
        "competition %d, regulation %d, %d club(s): %s" % (cid, reg, len(teams), teams)
    )

    if dry:
        print("dry run: nothing written")
        return 0

    comp, regs, ents = bytearray(comp), bytearray(regs), bytearray(ents)
    M.add_league(
        comp, regs, ents, cid, reg, M.enc_region(25), NAME, CODE, teams, tier=1
    )
    open(os.path.join(base, "Competition.bin"), "wb").write(
        pesdb.wesys_pack(bytes(comp))
    )
    open(os.path.join(base, "CompetitionRegulation.bin"), "wb").write(
        pesdb.wesys_pack(bytes(regs))
    )
    open(os.path.join(base, "CompetitionEntry.bin"), "wb").write(
        pesdb.wesys_pack(bytes(ents))
    )

    lines = io.open(wf, encoding="utf-8", errors="replace").read().splitlines()
    new = (
        "league %d cid=%d region=25 country=200 conf=5 slot=%d tier=1 promote=0 demote=0 "
        "clubs=%d legs=2 kickoff=99 name=%s" % (reg, cid, slot, len(teams), NAME)
    )
    if not any(l.startswith("league %d " % reg) for l in lines):
        lines.append(new)
    io.open(wf, "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
    print("world file: %s" % new)
    return 0


if __name__ == "__main__":
    sys.exit(main())
