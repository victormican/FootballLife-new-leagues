"""python mk_conf_cup.py --base <pesdb> --worldfile <fl26world.txt>
                        --name "CAF Confederation Cup" --code FL_CAFCC --conf 5
                        [--clubs 16] [--groups 4] [--positions 5,6,7,8]
                        [--cid N] [--reg N] [--ko N] [--like 23] [--dry]

Build a continental club cup out of the clubs the world's leagues already have: it takes
position `p` of the leagues of a confederation, cycling the leagues, until it has `--clubs`
entries, and hands the spec to `mkccup.py` (which writes the competition, the regulation, its
group replicas and the entries) and then appends the `ccup` line it prints to the world file.

`--groups N` builds groups of four plus a knockout (reg = the group master, ko = the knockout);
`--groups 0` builds a straight knockout (give reg = ko, and optionally `--like 23`, the FA Cup's
shape, which also allows any field the bracket screen draws).
"""

import io
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import mkleague as M


def main():
    a = sys.argv[1:]
    get = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    base, wf = get("--base"), get("--worldfile")
    name, code = get("--name"), get("--code")
    if not base or not wf or not name or not code:
        print(__doc__)
        return 1
    conf = int(get("--conf", "0"))
    clubs = int(get("--clubs", "16"))
    groups = int(get("--groups", "4"))
    positions = [int(x) for x in get("--positions", "5,6,7,8").split(",") if x.strip()]
    like = get("--like")
    dry = "--dry" in a

    lines = io.open(wf, encoding="utf-8", errors="replace").read().splitlines()
    leagues = []
    for l in lines:
        w = l.split()
        if w and w[0] == "league":
            kv = dict(x.split("=", 1) for x in w[2:] if "=" in x)
            if "serve" in kv or kv.get("slot") == "123":
                continue
            if int(kv.get("conf", -1)) != conf:
                continue
            leagues.append((int(w[1]), int(kv.get("clubs", "0") or 0)))
    if not leagues:
        print("no league of confederation %d in the world" % conf)
        return 1
    entries, k = [], 0
    while len(entries) < clubs and k < len(positions) * len(leagues) + len(positions):
        league, n = leagues[(len(entries) // len(positions)) % len(leagues)]
        pos = positions[len(entries) % len(positions)]
        if pos <= n:
            entries.append("%d:%d" % (league, pos))
        k += 1
        if k > 4 * clubs:
            break
    if len(entries) < clubs:
        print(
            "only %d entries could be taken from confederation %d"
            % (len(entries), conf)
        )
        return 1

    comp = M.load(base, "Competition.bin")
    regs = M.load(base, "CompetitionRegulation.bin")
    used_c = {comp[i + M.CID_OFF] for i in range(0, len(comp), M.COMP)}
    used_r = {
        int.from_bytes(regs[i + M.R_ID : i + M.R_ID + 2], "little")
        for i in range(0, len(regs), M.REG)
    }
    cid = int(get("--cid", "0")) or next(c for c in range(48, 256) if c not in used_c)
    reg = int(get("--reg", "0")) or next(r for r in range(198, 1024) if r not in used_r)
    ko = int(get("--ko", "0")) or (
        reg
        if groups == 0
        else next(r for r in range(198, 1024) if r not in used_r and r != reg)
    )
    region = 25
    spec = "|".join(
        [
            name,
            code,
            str(cid),
            str(reg),
            str(ko),
            str(groups),
            ",".join(entries),
            str(conf),
            str(region),
        ]
        + ([str(like)] if like else [])
    )
    print("cup spec:", spec)
    if dry:
        print("dry run: nothing written")
        return 0

    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(base))))
    r = subprocess.run(
        [
            sys.executable,
            os.path.join(HERE, "mkccup.py"),
            "--base",
            base,
            "--out",
            root,
            "--cup",
            spec,
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    out = (r.stdout or "") + (r.stderr or "")
    print(out.strip()[-600:])
    if r.returncode:
        print("mkccup failed (%d)" % r.returncode)
        return r.returncode
    line = None
    for l in out.splitlines():
        if l.strip().startswith("ccup "):
            line = l.strip()
    if not line:
        print("mkccup wrote no ccup line")
        return 1
    if "cid=" not in line:
        line = line + " cid=%d" % cid
    lines = [
        l
        for l in io.open(wf, encoding="utf-8", errors="replace").read().splitlines()
        if not l.startswith("ccup %d " % reg)
    ]
    lines.append(line)
    io.open(wf, "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
    print("world file: " + line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
