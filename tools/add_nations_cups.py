"""python add_nations_cups.py --base <world pesdb> --worldfile <fl26world.txt>
                             --countries <pesdb with Country.bin>
                             [--preset gold,ofc,wc-ofc,nl-uefa,nl-concacaf]
                             [--size N] [--pre] [--dry]

Build the national-team competitions the game has not got out of the world's own national
teams: the CONCACAF Gold Cup, the OFC Nations Cup, an OFC World Cup qualifying round and the two
Nations Leagues.

Without --pre each one is a straight knockout of N national teams (a multiple of four), one
match a round, in its own window.

With --pre the competition gets the **qualifying round** in front of it, and both are playable
and feed each other:

  pre-round   N national teams, N/2 two-legged ties, invited by name (`clubs=`), two days
  cup         the N/2 winners of those ties, one match a round (`like=23`), its own days

The cup's entries are the tie regulations (`<pre> + 1024 * (tie + 1)`), which is the module's
"the winner of that cup" entry: `fl26_swiss_lpre` plays the ties, `ccup_fill` takes each winner,
and the cup runs.  Both appear under the same competition id, so Kick Off > Cup lists the
competition and a Master League season plays it from the pre-round.

Why it can
  The shipped game has the World Cup, five confederation qualifiers, the EURO, the Copa
  America, the Asian Cup and the Africa Cup as competitions whose entries are national teams
  (competitions 27..36), so a national team is a team the module can resolve -- and since
  2026-10-23 `club_of_id` also falls back to the team record itself, so the 67 a world adds
  resolve too (needs the DLL built from this branch).

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

LIKES = 23  # the FA Cup: one match a round, any bracket it draws
REGION = 25  # decodes to the byte 200 the shipped national cups use
MAX_TIES = 8  # fl26swiss.c LPRE_TIES
PRESETS = {
    #  name                          conf  size fill  days                 code       pre fill days
    "gold": (
        "CONCACAF Gold Cup",
        6,
        16,
        185,
        [190, 193, 196, 199],
        "FL_GOLD",
        182,
        [183, 186],
    ),
    "ofc": ("OFC Nations Cup", 7, 8, 150, [155, 158, 161], "FL_OFCN", 148, [149, 152]),
    # the heading the Select Team list needs for a group of its own: a slot with a name comes
    # from the competition on it, and the OFC teams carry the slot in their own nibble
    "oceania": ("Oceania", 7, 8, 166, [166, 169, 172], "FL_OCEA", 164, [165, 168]),
    "wc-ofc": (
        "OFC World Cup Qualifying",
        7,
        8,
        60,
        [65, 68, 71],
        "FL_OFWCQ",
        58,
        [59, 62],
    ),
    "nl-uefa": (
        "UEFA Nations League",
        2,
        16,
        70,
        [75, 82, 96, 103],
        "FL_UNL",
        68,
        [69, 72],
    ),
    "nl-concacaf": (
        "CONCACAF Nations League",
        6,
        16,
        70,
        [75, 82, 96, 103],
        "FL_CNL",
        68,
        [69, 72],
    ),
}


def free_ids(base):
    comp = M.load(base, "Competition.bin")
    regs = M.load(base, "CompetitionRegulation.bin")
    used_c = {comp[i + M.CID_OFF] for i in range(0, len(comp), M.COMP)}
    used_r = {
        int.from_bytes(regs[i + M.R_ID : i + M.R_ID + 2], "little")
        for i in range(0, len(regs), M.REG)
    }
    cids = [c for c in range(88, 256) if c not in used_c]
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
    pre = "--pre" in a
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

    nats = {}
    for e in N.read(base, countries):
        nats.setdefault(e["conf"], []).append((e["id"], e["name"], e["country"]))
    cids, rids = free_ids(base)
    lines, made, prerounds = [], [], []
    for key in want:
        name, conf, n, fill, days, code, pfill, pdays = PRESETS[key]
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
        cup_size = n // 2 if pre else n
        if len(cids) < 1 or len(rids) < 1:
            print("%s: no free competition or regulation id left" % name)
            continue
        cid, ko = cids.pop(0), rids.pop(0)
        pre_reg = 0
        if pre:
            if n // 2 > MAX_TIES:
                print(
                    "%s: a pre-round takes %d ties at most; %d teams asked"
                    % (name, MAX_TIES, n)
                )
                continue
            if len(rids) < 1:
                print("%s: no free regulation id for its pre-round" % name)
                continue
            pre_reg = rids.pop(0)
            prerounds.append((pre_reg, cid, name, n // 2))
            entry = ",".join("%d:0" % (pre_reg + 1024 * (k + 1)) for k in range(n // 2))
        else:
            entry = ",".join("0:%d" % t for t in pick)
        cup = "|".join(
            [
                name,
                code,
                str(cid),
                str(ko),
                str(ko),
                "0",
                entry,
                str(conf),
                str(REGION),
                str(LIKES),
            ]
        )
        made.append(
            {
                "name": name,
                "cid": cid,
                "ko": ko,
                "pre": pre_reg,
                "pick": pick,
                "fill": fill,
                "days": days,
                "pfill": pfill,
                "pdays": pdays,
                "cup": cup,
                "size": cup_size,
            }
        )
        print(
            "  %s: cid %d, regulation %d%s, %d in the cup"
            % (name, cid, ko, ", pre-round %d" % pre_reg if pre else "", cup_size)
        )

    if dry or not made:
        print("dry run: nothing written" if made else "nothing to build")
        return 0 if made else 1

    if prerounds:
        import mkeuropo

        mkeuropo.prerounds(
            base,
            os.path.dirname(os.path.dirname(os.path.dirname(base))),
            prerounds,
            log=print,
        )
    args = [
        sys.executable,
        os.path.join(HERE, "mkccup.py"),
        "--base",
        base,
        "--out",
        os.path.dirname(os.path.dirname(os.path.dirname(base))),
    ]
    for m in made:
        args += ["--cup", m["cup"]]
    rc = subprocess.call(args)
    if rc:
        print("mkccup failed (%d)" % rc)
        return rc

    for m in made:
        if m["pre"]:
            lines.append(
                "ccup %d ko=%d groups=0 entry=%s cid=%d fill=%d national=1 days=%s "
                "like=%d draw=seeded name=%s"
                % (
                    m["ko"],
                    m["ko"],
                    ",".join(
                        "%d:0" % (m["pre"] + 1024 * (k + 1)) for k in range(m["size"])
                    ),
                    m["cid"],
                    m["fill"],
                    ",".join(map(str, m["days"])),
                    LIKES,
                    m["name"],
                )
            )
            lines.append(
                "lpre %d cup=%d fill=%d days=%s entry=%s clubs=%s"
                % (
                    m["pre"],
                    m["ko"],
                    m["pfill"],
                    ",".join(map(str, m["pdays"])),
                    ",".join("0:0" for _ in range(2 * m["size"])),
                    ",".join(map(str, m["pick"])),
                )
            )
        else:
            lines.append(
                "ccup %d ko=%d groups=0 entry=%s cid=%d fill=%d national=1 days=%s "
                "clubs=%s like=%d draw=seeded name=%s"
                % (
                    m["ko"],
                    m["ko"],
                    ",".join("0:%d" % t for t in m["pick"]),
                    m["cid"],
                    m["fill"],
                    ",".join(map(str, m["days"])),
                    ",".join(map(str, m["pick"])),
                    LIKES,
                    m["name"],
                )
            )
        print("  " + lines[-1])
    s = io.open(wf, encoding="utf-8", errors="replace").read().splitlines()
    have = {
        l.split()[1]
        for l in s
        if (l.startswith("ccup ") or l.startswith("lpre ")) and len(l.split()) > 1
    }
    add = [l for l in lines if l.split()[1] not in have]
    if add:
        s = s + add
        io.open(wf, "w", encoding="utf-8", newline="\n").write("\n".join(s) + "\n")
    print("added %d line(s) to %s" % (len(add), wf))
    return 0


if __name__ == "__main__":
    sys.exit(main())
