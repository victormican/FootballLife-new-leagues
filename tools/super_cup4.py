"""python super_cup4.py --base <world pesdb> --worldfile <fl26world.txt>
                       --league <reg> --cup <reg> --super <reg> [--cid N] [--name TEXT]
                       [--days 7,11] [--fill 190] [--dry]

Turn a shipped two-club super cup into the four-club version the competition has in real
life: two semi-finals and a final (the Supercopa de España since 2020, the Supercoppa
Italiana since 2024).  No competition id and no regulation id is spent: the super cup keeps
its own row and its own cid, and only its bracket grows from two to four.

What it writes
  CompetitionRegulation.bin   the super cup's regulation: its club/bracket count becomes 4
                              (the row is a knockout already, type 3); nothing else changed
  the world file              a `ccup` line that fills it with
                                <league> 1st, <league> 2nd,
                                <cup> winner (falling back to <league> 3rd, 4th, ...),
                                <league> 3rd (falling back to the 4th when the cup winner
                                took the 3rd),
                              played on `--days` and filled on `--fill`, plus the `cupdays`
                              line that keeps the league's rounds clear of those days

Why the fill day is in July: the four places come from the season that has just ended (league
table and cup final), and those records are still the finished ones at the start of the new
season.  Filled in January, the cup record would be the one of the cup being played, not its
winner.  The rounds still play in January, where the real super cup does.

The module needs to run the cup (`fl26swiss`, ccup_fill + ccup_day) and the competition row
must be a knockout with a bracket of four, which is what the regulation change is for.  Check
the first game for the shipped super cup's own fill fighting this one: if it fills two clubs
again at its old date, the shipped date has to be moved too (`cupdays` is what tells the
league calendars, not the cup).
"""

import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pesdb
import mkleague as M

KNOCKOUT = 3


def rows(regs):
    return {
        int.from_bytes(regs[i + M.R_ID : i + M.R_ID + 2], "little"): i
        for i in range(0, len(regs), M.REG)
    }


def main():
    a = sys.argv[1:]
    get = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    base, wf = get("--base"), get("--worldfile")
    if not base or not wf or not get("--super"):
        print(__doc__)
        return 1
    super_reg = int(get("--super"))
    league = int(get("--league", "0"))
    cup = int(get("--cup", "0"))
    days = [int(x) for x in get("--days", "7,11").split(",") if x.strip()]
    fill = int(get("--fill", "190"))
    dry = "--dry" in a
    regs = bytearray(M.load(base, "CompetitionRegulation.bin"))
    by_id = rows(regs)
    if super_reg not in by_id:
        print("regulation %d is not in the tables" % super_reg)
        return 1
    if league and league not in by_id:
        print("league regulation %d is not in the tables" % league)
        return 1
    if cup and cup not in by_id:
        print("cup regulation %d is not in the tables" % cup)
        return 1
    i = by_id[super_reg]
    g = regs[i : i + M.REG]
    cid = g[M.R_CID]
    name = get("--name") or g[M.R_NAME : M.R_NAME + 60].split(b"\0")[0].decode(
        "utf-8", "replace"
    )
    if g[M.R_TYPE] != KNOCKOUT:
        print(
            "regulation %d is type %d, not a knockout -- this is for super cups"
            % (super_reg, g[M.R_TYPE])
        )
        return 1
    if len(days) != 2:
        print("a four-club super cup has two rounds: --days wants two days")
        return 1
    before = g[M.R_TEAMS] & 0x3F
    if before > 4:
        print(
            "regulation %d already has a bracket of %d; four is smaller"
            % (super_reg, before)
        )
        return 1
    entry = "%d:1,%d:2,%d:0,%d:3" % (league, league, cup, league)
    alt = "2:%d:3,3:%d:4" % (league, league)
    line = (
        "ccup %d ko=%d groups=0 entry=%s cid=%d fill=%d national=1 days=%s alt=%s name=%s"
        % (super_reg, super_reg, entry, cid, fill, ",".join(map(str, days)), alt, name)
    )
    cupdays = "cupdays %d %s" % (super_reg, " ".join(map(str, days)))
    print(
        "%s (cid %d, regulation %d): bracket %d -> 4" % (name, cid, super_reg, before)
    )
    print("  " + line)
    print("  " + cupdays)
    if dry:
        print("dry run: nothing written")
        return 0
    regs[i + M.R_TEAMS] = (regs[i + M.R_TEAMS] & 0xC0) | 4
    open(os.path.join(base, "CompetitionRegulation.bin"), "wb").write(
        pesdb.wesys_pack(bytes(regs))
    )
    lines = io.open(wf, encoding="utf-8", errors="replace").read().splitlines()
    out = []
    for l in lines:
        w = l.split()
        if w and w[0] == "ccup" and len(w) > 1 and w[1] == str(super_reg):
            continue  # the old line for this cup, if any
        if w and w[0] == "cupdays" and len(w) > 1 and w[1] == str(super_reg):
            continue
        out.append(l)
    out += [line, cupdays]
    io.open(wf, "w", encoding="utf-8", newline="\n").write("\n".join(out) + "\n")
    print("written: %s" % wf)
    return 0


if __name__ == "__main__":
    sys.exit(main())
