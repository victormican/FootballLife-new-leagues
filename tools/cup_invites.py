"""python cup_invites.py --base <world pesdb> --worldfile <fl26world.txt>
                        --cup <name or cid> --clubs <id|name,...> [--dry] [--show]

Choose the clubs that play a cup's first round, including clubs of the "Other" groups and
clubs of the game, instead of the league positions.

A `ccup` line of the world file names its field by *positions* (`entry=<reg>:<position>`), and
the module then asks those leagues for the club at that place. `clubs=` replaces the whole
field by team ids named one by one (fl26swiss `fl26_swiss_ccup_opts`, "invited by name"). The
module only uses the list when its length is exactly the cup's field (the number of `entry`
pairs, or eight groups of four), so this tool checks that and refuses otherwise.

Clubs are named by team id, or by name as Team.bin spells it (case-insensitive substring); a
name that matches more than one team is reported with the candidates. Ids must exist in the
world's Team.bin.

Examples:
  python cup_invites.py --base <pesdb> --worldfile <world> --cup "Campeonato Paulista" --show
  python cup_invites.py --base <pesdb> --worldfile <world> --cup "Campeonato Paulista" \
      --clubs 9030,1247,137,1255,1254,2459,5767,2465
"""

import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pesdb

T_REC, T_ID, T_NAME, T_NAME_LEN = 1532, 0x08, 0x170, 70


def teams(base):
    raw = pesdb.wesys_unpack(open(os.path.join(base, "Team.bin"), "rb").read())
    out = {}
    for i in range(0, len(raw), T_REC):
        tid = int.from_bytes(raw[i + T_ID : i + T_ID + 4], "little")
        name = (
            raw[i + T_NAME : i + T_NAME + T_NAME_LEN]
            .split(b"\0")[0]
            .decode("utf-8", "replace")
        )
        out[tid] = name
    return out


def fields(line):
    """the cup's knockout id, its cid, its field size and its clubs= list (or None)"""
    ko = int((line.split("ko=")[1]).split()[0]) if " ko=" in line else None
    cid = int(line.split("cid=")[1].split()[0]) if " cid=" in line else None
    n = 0
    if " entry=" in line:
        ent = line.split(" entry=")[1].split()[0]
        n = len([p for p in ent.split(",") if p])
    groups = int(line.split("groups=")[1].split()[0]) if " groups=" in line else 0
    if groups:
        n = groups * 4
    clubs = None
    if " clubs=" in line:
        clubs = [int(x) for x in line.split(" clubs=")[1].split()[0].split(",") if x]
    name = line.split(" name=")[1].strip() if " name=" in line else ""
    return ko, cid, n, clubs, name


def main():
    a = sys.argv[1:]
    get = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    base, wf = get("--base"), get("--worldfile")
    want = get("--cup")
    if not base or not wf or not want:
        print(__doc__)
        return 1
    dry = "--dry" in a
    show = "--show" in a
    names = teams(base)
    by_id = {str(k): k for k in names}
    lowered = {}
    for tid, name in names.items():
        lowered.setdefault(name.strip().lower(), []).append(tid)

    lines = io.open(wf, encoding="utf-8", errors="replace").read().splitlines()
    hit = None
    for i, line in enumerate(lines):
        if not line.startswith("ccup "):
            continue
        ko, cid, n, clubs, name = fields(line)
        if (
            str(ko) == want
            or str(cid) == want
            or name.strip().lower() == want.strip().lower()
        ):
            hit = i
            break
    if hit is None:
        print("no ccup line named %r; the world has:" % want)
        for line in lines:
            if line.startswith("ccup "):
                ko, cid, n, clubs, name = fields(line)
                print("  cid %-4s ko %-4s %2d clubs  %s" % (cid, ko, n, name))
        return 1
    line = lines[hit]
    ko, cid, n, clubs, name = fields(line)
    print("cup %s (cid %s, ko %s): %d clubs in its first round" % (name, cid, ko, n))
    print(
        "  now: %s"
        % (", ".join(str(c) for c in clubs) if clubs else "the leagues' positions")
    )
    if show:
        for c in clubs or []:
            print("    %-6d %s" % (c, names.get(c, "?")))
        return 0

    got = []
    for x in (get("--clubs") or "").split(","):
        s = x.strip()
        if not s:
            continue
        if s.isdigit():
            tid = int(s)
            if tid not in names:
                print("team %d is not in Team.bin" % tid)
                return 1
            got.append(tid)
            continue
        cand = lowered.get(s.lower())
        if not cand:
            cand = [t for nm, ids in lowered.items() if s.lower() in nm for t in ids]
        if len(cand) != 1:
            print(
                "club %r: %s"
                % (
                    s,
                    "no team"
                    if not cand
                    else "more than one: "
                    + ", ".join("%d %s" % (t, names[t]) for t in sorted(cand)[:8]),
                )
            )
            return 1
        got.append(cand[0])
    if len(set(got)) != len(got):
        print("a club is invited twice")
        return 1
    if len(got) != n:
        print(
            "%d clubs for a cup of %d -- the module drops invitations whose count does not "
            "match its field" % (len(got), n)
        )
        return 1
    old = (" clubs=" + ",".join(map(str, clubs))) if clubs else ""
    new = " clubs=" + ",".join(map(str, got))
    if old:
        line = line.replace(old, new, 1)
    else:
        head, sep, tail = line.partition(" name=")
        line = head + new + sep + tail
    lines[hit] = line
    for c in got:
        print("  %-6d %s" % (c, names[c]))
    if dry:
        print("dry run: nothing written")
        return 0
    io.open(wf, "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
    print("written: %s" % wf)
    return 0


if __name__ == "__main__":
    sys.exit(main())
