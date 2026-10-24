"""python add_nations_cups.py --base <world pesdb> --worldfile <fl26world.txt>
                             --countries <pesdb with Country.bin>
                             [--preset gold,ofc,wc-ofc,nl-uefa,nl-concacaf]
                             [--size N] [--dry]

Build the national-team competitions the game has not got, out of the world's own national
teams: the CONCACAF Gold Cup, the OFC Nations Cup, an OFC World Cup qualifying round and the two
Nations Leagues.  Each one is a straight knockout of N national teams (a multiple of four), one
match a round, dated in its own window -- the group stages of the shipped cups use the module's
fixed November-February days, so a knockout is what can be dated where these play.

How it works, and why it can
  The shipped game has the World Cup, five confederation qualifiers, the EURO, the Copa America,
  the Asian Cup and the Africa Cup as competitions whose *entries are national teams* (Spain's
  tables: competitions 27..36).  So a national team is a team a competition already holds, and
  the module's club lookup (`club_of_id`) finds it: the cup can be filled by invitation.

  Each competition is built with `mkccup.py` from the Libertadores' shapes: a competition row
  (region 25, the "international" region the shipped national cups use, and the confederation in
  the flag), one knockout regulation copied from the FA Cup (one match a round), the entries
  (the national teams, so the tables are coherent) and a `ccup` line for the world file that
  names the same teams with `clubs=` -- the module fills the cup with them.

  The teams are the world's national teams (Team.bin rows with the national bit) grouped by the
  confederation of their country (Country.bin +5), exactly as `nations.py` prints them.  A
  preset whose confederation has fewer teams than it needs is refused with the count, not built
  half-full.

The test copy cannot take them: its 255 competition ids are all used.  A fresh world can.
"""

import io
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pesdb
import mkleague as M
import nations as N

T_REC, T_ID, T_NATIONAL, T_COUNTRY = 1532, 0x08, 0x53, 0x46
LIKES = 23  # the FA Cup: one match a round, any bracket it draws
REGION = 25  # decodes to the byte 200 the shipped national cups use
PRESETS = {
    #  name                    conf  size fill  days                    code
    "gold": ("CONCACAF Gold Cup", 6, 16, 185, [190, 193, 196, 199], "FL_GOLD"),
    "ofc": ("OFC Nations Cup", 7, 8, 150, [155, 158, 161], "FL_OFCN"),
    "wc-ofc": ("OFC World Cup Qualifying", 7, 8, 60, [65, 68, 71], "FL_OFWCQ"),
    "nl-uefa": ("UEFA Nations League", 2, 16, 70, [75, 82, 96, 103], "FL_UNL"),
    "nl-concacaf": ("CONCACAF Nations League", 6, 16, 70, [75, 82, 96, 103], "FL_CNL"),
}


def free_ids(base):
    comp = M.load(base, "Competition.bin")
    regs = M.load(base, "CompetitionRegulation.bin")
    used_c = {comp[i + M.CID_OFF] for i in range(0, len(comp), M.COMP)}
    used_r = {
        int.from_bytes(regs[i + M.R_ID : i + M.R_ID + 2], "little")
        for i in range(0, len(regs), M.REG)
    }
    cids = [c for c in range(130, 256) if c not in used_c]
    rids = [r for r in range(176, 1024) if r not in used_r]
    return cids, rids


def main():
    a = sys.argv[1:]
    get = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    base, wf = get("--base"), get("--worldfile")
    if not base or not wf:
        print(__doc__)
        return 1
    countries = get("--countries") or base
    dry = "--dry" in a
    size = int(get("--size", "0"))
    want = [
        p.strip()
        for p in (get("--preset") or ",".join(PRESETS)).split(",")
        if p.strip()
    ]
    bad = [p for p in want if p not in PRESETS]
    if bad:
        print("unknown preset(s): %s -- use %s" % (", ".join(bad), ", ".join(PRESETS)))
        return 1

    nats = {}  # {conf: [(team, name, country), ...]}
    for e in N.read(base, countries):
        nats.setdefault(e["conf"], []).append((e["id"], e["name"], e["country"]))
    cids, rids = free_ids(base)
    if dry:
        pass
    lines, made = [], []
    for key in want:
        name, conf, n, fill, days, code = PRESETS[key]
        if size:
            n = size
        teams = [t for t, _n, _c in nats.get(conf, [])]
        if len(teams) < n:
            print(
                "%s: %d national teams in confederation %d, %d needed -- not built"
                % (name, len(teams), conf, n)
            )
            continue
        if n % 4 or n < 4:
            print("%s: %d clubs -- use a multiple of four" % (name, n))
            continue
        pick = teams[:n]
        if len(cids) < 1 or len(rids) < 1:
            print("%s: no free competition or regulation id left" % name)
            continue
        cid, reg = cids.pop(0), rids.pop(0)
        entry = ",".join("0:%d" % t for t in pick)
        cup = "|".join(
            [
                name,
                code,
                str(cid),
                str(reg),
                str(reg),
                "0",
                entry,
                str(conf),
                str(REGION),
                str(LIKES),
            ]
        )
        made.append((name, cid, reg, pick, fill, days, cup))
        print(
            "  %s: cid %d, reg %d, %d national teams of confederation %d"
            % (name, cid, reg, n, conf)
        )

    if dry or not made:
        print("dry run: nothing written" if made else "nothing to build")
        return 0 if made else 1

    args = [
        sys.executable,
        os.path.join(HERE, "mkccup.py"),
        "--base",
        base,
        "--out",
        os.path.dirname(os.path.dirname(os.path.dirname(base))),
    ]
    for m in made:
        args += ["--cup", m[6]]
    rc = subprocess.call(args)
    if rc:
        print("mkccup failed (%d)" % rc)
        return rc

    for name, cid, reg, pick, fill, days, _cup in made:
        line = (
            "ccup %d ko=%d groups=0 entry=%s cid=%d fill=%d national=1 days=%s clubs=%s "
            "like=%d draw=seeded name=%s"
            % (
                reg,
                reg,
                ",".join("0:%d" % t for t in pick),
                cid,
                fill,
                ",".join(map(str, days)),
                ",".join(map(str, pick)),
                LIKES,
                name,
            )
        )
        lines.append(line)
        print("  " + line)
    s = io.open(wf, encoding="utf-8", errors="replace").read().splitlines()
    have = {l.split()[1] for l in s if l.startswith("ccup ") and len(l.split()) > 1}
    add = [l for l in lines if l.split()[1] not in have]
    if add:
        s = s + add
        io.open(wf, "w", encoding="utf-8", newline="\n").write("\n".join(s) + "\n")
    print("added %d national competition(s) to %s" % (len(add), wf))
    return 0


if __name__ == "__main__":
    sys.exit(main())
