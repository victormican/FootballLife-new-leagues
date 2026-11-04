"""python add_league_generic.py --base <pesdb> --worldfile <fl26world.txt> --name "..." \\
       --cid 266 --reg 908 --region 123 --country 194 --conf 2 --slot 208 \\
       [--kickoff 25] [--code FL_AT_D2] [--tier 1] [--dry]

Add one league of generic clubs: the competition row, the regulation and the `league` line, and
nothing else. The clubs are created afterwards by `fill_group.py --reg <id> --reset --to <n>`,
which clones a squad for each of them -- the same path every other generic league of the world
takes, so no row of the game is renamed and no competition loses a club.

Why a tool instead of a table: `add_eight_leagues.py` recycles Team.bin rows nobody owns and
renames them, which is how the eight leagues of 2026-11-04 ended up showing the names of real
clubs. A league of ours is a competition with its own clubs, created from scratch.

The name is written twice on purpose: `mkleague.add_league` writes a long code that clears the
16-byte menu name at Competition.bin +0x14 (the bug of 2026-11-04 that left the eight leagues
nameless), so it is written again there.
"""

import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pesdb
import mkleague as M


def main():
    a = sys.argv[1:]
    get = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    base, wf, name = get("--base"), get("--worldfile"), get("--name")
    need = ("--cid", "--reg", "--region", "--country", "--slot")
    if not base or not wf or not name or any(k not in a for k in need):
        print(__doc__)
        return 1
    cid, reg = int(get("--cid")), int(get("--reg"))
    region, country = int(get("--region")), int(get("--country"))
    slot, conf = int(get("--slot")), int(get("--conf", "2"))
    kickoff = int(get("--kickoff", "25"))
    tier = int(get("--tier", "1"))
    code = get("--code") or ("FL_%d_D%d" % (region, tier))
    dry = "--dry" in a

    comp = bytearray(M.load(base, "Competition.bin"))
    regs = bytearray(M.load(base, "CompetitionRegulation.bin"))
    ents = bytearray(M.load(base, "CompetitionEntry.bin"))

    M.add_league(
        comp,
        regs,
        ents,
        cid,
        reg,
        M.enc_region(region),
        name,
        code,
        [],
        proto_code="FL_223_D1",
        quiet=True,
        tier=tier,
    )
    # add_league wrote a 28-byte code over the row, which also clears the 16-byte menu name
    M.put(comp, (len(comp) // M.COMP - 1) * M.COMP + 0x14, name, 16)

    lines = io.open(wf, encoding="utf-8", errors="replace").read().splitlines()
    have = {l.split()[1] for l in lines if l.startswith("league ")}
    if str(reg) in have:
        print("reg %d already has a `league` line in %s" % (reg, wf))
        return 2
    line = (
        "league %d cid=%d region=%d country=%d conf=%d slot=%d tier=%d promote=0 demote=0 "
        "clubs=0 legs=2 kickoff=%d name=%s"
        % (reg, cid, region, country, conf, slot, tier, kickoff, name)
    )
    at = max(i for i, l in enumerate(lines) if l.startswith("league "))
    lines.insert(at + 1, line)
    print("line:", line)

    if dry:
        print("dry run: nothing written")
        return 0

    open(os.path.join(base, "Competition.bin"), "wb").write(
        pesdb.wesys_pack(bytes(comp))
    )
    open(os.path.join(base, "CompetitionRegulation.bin"), "wb").write(
        pesdb.wesys_pack(bytes(regs))
    )
    open(os.path.join(base, "CompetitionEntry.bin"), "wb").write(
        pesdb.wesys_pack(bytes(ents))
    )
    io.open(wf, "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
    print(
        "competition %d / regulation %d added -- now: fill_group.py --base ... "
        "--worldfile ... --reg %d --reset --to <n>" % (cid, reg, reg)
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
