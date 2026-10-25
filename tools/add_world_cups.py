"""python add_world_cups.py --base <pesdb> --worldfile <fl26world.txt>
                          [--countries <pesdb with Country.bin>] [--dry]

Insert the cups a world of national teams and continents is expected to have:

  FIFA World Cup            32 national teams (13 UEFA, 5 CAF, 4 AFC, 4 CONMEBOL, 4 CONCACAF, 2 OFC)
  FIFA Club World Cup       32 clubs, the first of the leagues of every confederation
  UEFA EURO                 24 UEFA national teams
  Copa America              16: the 10 CONMEBOL plus 6 invited CONCACAF
  AFC Asian Cup             24 AFC national teams
  CAF Africa Cup of Nations 24 CAF national teams

Cups of 24 and 11 are a single-match knockout like the FA Cup (regulation 23), which draws any
number of byes; 32 and 16 are a plain knockout. Competition ids 66..71 are shipped rows no league
of this world uses: they are dropped so the cups take their id, and the names come from the new
regulations. The world file gets the `ccup` lines with their `cid=`.
"""

import io
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import mkleague as M
import nations as N

CIDS = [256, 257, 258, 259, 260, 261]
REGS = [210, 211, 212, 213, 214, 215]


def pick(items, n):
    """n of a list, spread over it (not just the first ones)"""
    if n >= len(items):
        return list(items)[:n]
    step = len(items) / float(n)
    return [items[int(k * step)] for k in range(n)]


def main():
    a = sys.argv[1:]
    get = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    base, wf = get("--base"), get("--worldfile")
    if not base or not wf:
        print(__doc__)
        return 1
    countries = get("--countries") or base
    dry = "--dry" in a

    nats = N.read(base, countries)
    by_conf = {}
    for e in nats:
        by_conf.setdefault(e["conf"], []).append(e["id"])
    for k in by_conf:
        by_conf[k].sort()

    lines = io.open(wf, encoding="utf-8", errors="replace").read().splitlines()
    leagues = {}
    for l in lines:
        w = l.split()
        if w and w[0] == "league":
            kv = dict(x.split("=", 1) for x in w[2:] if "=" in x)
            if "serve" in kv or kv.get("slot") == "123":
                continue
            leagues.setdefault(int(kv.get("conf", "-1")), []).append(int(w[1]))
    for k in leagues:
        leagues[k].sort()

    # the national cups, by team id
    world_cup = []
    for conf, n in ((2, 13), (5, 5), (3, 4), (4, 4), (6, 4), (7, 2)):
        world_cup += pick(by_conf.get(conf, []), n)
    if len(world_cup) < 32:
        print("only %d national teams for the World Cup" % len(world_cup))
        return 1
    euro = pick(by_conf.get(2, []), 24)
    asian = pick(by_conf.get(3, []), 24)
    afcon = pick(by_conf.get(5, []), 24)
    copa = by_conf.get(4, [])[:10] + pick(by_conf.get(6, []), 6)
    # 32 clubs: the first of the leagues of every confederation
    club_spots = ((2, 14), (4, 8), (3, 6), (5, 4))
    clubs = []
    for conf, n in club_spots:
        for reg in pick(leagues.get(conf, []), n):
            clubs.append("%d:1" % reg)
    if len(clubs) < 32:
        print("only %d leagues for the Club World Cup" % len(clubs))
        return 1

    cups = [
        (
            "FIFA World Cup",
            "FL_WCUP",
            CIDS[0],
            REGS[0],
            0,
            [str(t) for t in world_cup],
            4,
        ),
        ("FIFA Club World Cup", "FL_CWC32", CIDS[1], REGS[1], 0, clubs, 4),
        ("UEFA EURO", "FL_EURO", CIDS[2], REGS[2], 23, [str(t) for t in euro], 2),
        ("Copa America", "FL_COPA", CIDS[3], REGS[3], 0, [str(t) for t in copa], 4),
        ("AFC Asian Cup", "FL_ASIA", CIDS[4], REGS[4], 23, [str(t) for t in asian], 3),
        (
            "CAF Africa Cup of Nations",
            "FL_AFCON",
            CIDS[5],
            REGS[5],
            23,
            [str(t) for t in afcon],
            5,
        ),
    ]

    comp = M.load(base, "Competition.bin")
    rows = [comp[i : i + M.COMP] for i in range(0, len(comp), M.COMP)]
    regs = M.load(base, "CompetitionRegulation.bin")
    rrows = [regs[i : i + M.REG] for i in range(0, len(regs), M.REG)]
    ents = M.load(base, "CompetitionEntry.bin")
    erows = [ents[i : i + M.ENT] for i in range(0, len(ents), M.ENT)]
    dropped = [r[M.CID_OFF] for r in rows if r[M.CID_OFF] in CIDS]
    print("competition rows taken over: %s" % dropped)

    specs = []
    for name, code, cid, reg, like, entries, conf in cups:
        ent = ",".join(e if ":" in e else "0:" + e for e in entries)
        specs.append(
            "%s|%s|%d|%d|%d|0|%s|%d|25%s"
            % (name, code, cid, reg, reg, ent, conf, "|%d" % like if like else "")
        )

    if dry:
        for s in specs:
            print("cup:", s)
        print("dry run: nothing written")
        return 0

    comp = b"".join(r for r in rows if r[M.CID_OFF] not in CIDS)
    open(os.path.join(base, "Competition.bin"), "wb").write(pesdb_pack(comp))
    # the shipped rows of those ids go with their regulations and entries: the cups take the id
    for name, keep, key in (
        (
            "CompetitionRegulation.bin",
            [r for r in rrows if r[M.R_CID] not in CIDS],
            M.R_ID,
        ),
        ("CompetitionEntry.bin", [r for r in erows if r[M.E_CID] not in CIDS], M.E_CID),
    ):
        open(os.path.join(base, name), "wb").write(pesdb_pack(b"".join(keep)))
        print("  %s: %d records" % (name, len(keep)))

    out = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(base))))
    cmd = [
        sys.executable,
        os.path.join(HERE, "mkccup.py"),
        "--base",
        base,
        "--out",
        out,
    ]
    for s in specs:
        cmd += ["--cup", s]
    r = subprocess.run(
        cmd, capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    print(((r.stdout or "") + (r.stderr or "")).strip()[-1200:])
    if r.returncode:
        print("mkccup failed (%d)" % r.returncode)
        return r.returncode

    new = []
    for l in lines:
        if any(l.startswith("ccup ") and " cid=%d" % c in l for c in CIDS):
            continue
        new.append(l)
    for name, code, cid, reg, like, entries, conf in cups:
        ent = ",".join(e if ":" in e else "0:" + e for e in entries)
        new.append(
            "ccup %d ko=%d groups=0 entry=%s cid=%d fill=150 national=1 days=160,163,166 "
            "like=%d draw=seeded name=%s" % (reg, reg, ent, cid, like or 6, name)
        )
    io.open(wf, "w", encoding="utf-8", newline="\n").write("\n".join(new) + "\n")
    print("world file: %d ccup line(s)" % len(cups))
    return 0


def pesdb_pack(b):
    import pesdb

    return pesdb.wesys_pack(bytes(b))


if __name__ == "__main__":
    sys.exit(main())
