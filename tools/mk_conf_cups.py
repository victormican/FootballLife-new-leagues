"""python mk_conf_cups.py --base <pesdb> --world <fl26world.txt> --out <livecpk root>
                         [--cups a,b,...] [--dry]

Cups the world has not got, each in a competition id of its own.

WARNING (measured 2026-11-04): the ids above 255 do not survive the boot.  The tables take
them -- 267 competitions, 446 regulations, check_world clean -- and `fl26cid16.lua` reads the
high byte in Select Team, the census and Edit, but the game builds a fixed table of 16-byte
entries indexed by `id - 1` (FL_2026+0x14f1c42, `mov rax,[r15+rax*8]`) and cid 256 walks off
it: 0xc0000005 before the main menu.  The real ceiling is 255 competitions and every one of
the world's 255 ids is taken, so these cups only fit after freeing ids (see
docs/developers/fork/limites-escalables.md).  `--cups` is still useful once that is done.

What it does, in this order:

  1. Undoes the "Sudamericana in the Custom Cup" trick: restores Competition.bin,
     CompetitionRegulation.bin, CompetitionEntry.bin and fl26world.txt from the
     `*.before-sudam-*` backups, so cid 37 is the shipped CUSTOM_CUP again.
  2. Builds every cup of `--cups` (default: all of them) through `mkccup.py` with its own
     competition id, competitions 256 and up: `mkccup` writes the high byte in
     Competition.bin +0x07, CompetitionEntry.bin +0x0b and CompetitionRegulation.bin +0x910,
     which is what `fl26cid16.lua` reads.
  3. Appends the `ccup` lines with cid= / conf= / region= / clubs= so `fl26swiss` exposes them
     in Kick Off > Cup.

Clubs are invited by team id (`0:<id>`): the top N of the confederation, taken position by
position across its leagues (all the champions first, then all the runners-up, ...), leagues
ordered by competition id so the shipped ones go first.

The national-team Caribbean Cup is not here: it needs `national=1` and the pre-round shapes of
`add_nations_cups.py`, which already has the `caribbean` preset (cid 267).
"""

import io
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import mkleague as M
import pesdb

# name, code, cid, conf, region, groups, size, source
#   source: ("conf", conf, skip) picks clubs from that confederation, skipping `skip` clubs;
#           ("mix", [conf, ...]) picks the champion of each confederation.
CUPS = [
    ("Copa Sudamericana", "FL_SUDAMER", 257, 4, 26, 8, 32, ("conf", 4, 5)),
    ("Copa Intercontinental", "FL_INTERC", 257, 1, 1, 0, 4, ("mix", [2, 4, 6, 5])),
    ("CAF Champions League", "FL_CAFCL", 258, 5, 1, 4, 16, ("conf", 5, 1)),
    ("CAF Confederation Cup", "FL_CAFCC", 259, 5, 1, 4, 16, ("conf", 5, 2)),
    ("AFC Challenge League", "FL_AFCCH", 260, 3, 1, 4, 16, ("conf", 3, 1)),
    ("CAF Super Cup", "FL_CAFSC", 261, 5, 1, 0, 2, ("conf", 5, 1)),
    ("AFC Super Cup", "FL_AFCSC", 262, 3, 1, 0, 2, ("conf", 3, 1)),
    ("CONCACAF Super Cup", "FL_CNCSC", 263, 6, 23, 0, 2, ("conf", 6, 1)),
    ("CONCACAF Central American Cup", "FL_CENTRO", 264, 6, 23, 4, 16, ("conf", 6, 1)),
    ("CONCACAF Caribbean Cup", "FL_CRBCC", 265, 6, 23, 4, 16, ("conf", 6, 3)),
    ("CFU Club Shield", "FL_CFUSH", 266, 6, 23, 0, 8, ("conf", 6, 6)),
]

SETTLED = {
    # the shipped cup that every knockout of a custom cup is copied from
    "like": 23,
    "first_reg": 500,
}


def have(path):
    return os.path.exists(path)


def restore(base, world):
    """Undo the Custom Cup trick: the backups talk before mk_sudamericana.py ran."""
    pesdb_dir = base
    for name in (
        "Competition.bin",
        "CompetitionRegulation.bin",
        "CompetitionEntry.bin",
    ):
        backups = sorted(
            f for f in os.listdir(pesdb_dir) if f.startswith(name + ".before-sudam-")
        )
        if not backups:
            print("%s: no .before-sudam- backup, left alone" % name)
            continue
        src = os.path.join(pesdb_dir, backups[-1])
        io.open(os.path.join(pesdb_dir, name), "wb").write(io.open(src, "rb").read())
        print("restored %s from %s" % (name, backups[-1]))
    wb = sorted(
        f
        for f in os.listdir(os.path.dirname(world))
        if f.startswith(os.path.basename(world) + ".before-sudam-")
    )
    if wb:
        src = os.path.join(os.path.dirname(world), wb[-1])
        io.open(world, "wb").write(io.open(src, "rb").read())
        print("restored %s from %s" % (os.path.basename(world), wb[-1]))


def leagues_by_conf(world):
    out = {}
    for line in io.open(world, encoding="utf-8", errors="replace"):
        if not line.startswith("league "):
            continue
        kv = dict(re.findall(r"(\w+)=(-?\d+)", line))
        out.setdefault(int(kv.get("conf", 0)), []).append(int(line.split()[1]))
    return out


def clubs_of(ents, cid):
    return [
        (e[M.E_ORDER], int.from_bytes(e[M.E_TEAM : M.E_TEAM + 4], "little"))
        for e in ents
        if e[M.E_CID] == cid
    ]


def pick(comp, regs, ents, world, cups):
    """Position by position across the confederation's leagues, shipped ids first."""
    leagues = leagues_by_conf(world)
    cid_of_reg = {
        int.from_bytes(r[M.R_ID : M.R_ID + 2], "little"): r[M.R_CID] for r in regs
    }
    by_pos = {}
    for conf, reg_ids in leagues.items():
        rows = []
        for rid in reg_ids:
            cid = cid_of_reg.get(rid)
            if cid is None:
                continue
            for order, tid in clubs_of(ents, cid):
                rows.append((order, cid, tid))
        rows.sort()
        by_pos[conf] = rows

    out = {}
    for name, code, cid, conf, region, groups, size, source in cups:
        picked = []
        if source[0] == "mix":
            for c in source[1]:
                for order, _cid, tid in by_pos.get(c, []):
                    if order == 1 and tid not in picked:
                        picked.append(tid)
                        break
            picked = picked[:size]
        else:
            # position by position: every confederation's champions first, then the
            # runners-up of each league, and so on (a league's places stay together only
            # inside its own position)
            from_pos = source[2]
            rows = [r for r in by_pos.get(source[1], []) if r[0] >= from_pos]
            rows.sort(key=lambda r: (r[0], r[1], r[2]))
            for _order, _cid, tid in rows:
                if tid not in picked:
                    picked.append(tid)
                    if len(picked) == size:
                        break
        if len(picked) < size:
            raise SystemExit(
                "%s: only %d club(s) in confederation %d, %d needed"
                % (name, len(picked), source[1] if source[0] == "conf" else -1, size)
            )
        out[name] = picked
    return out


def main():
    a = sys.argv[1:]
    get = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    base, world, out = get("--base"), get("--world"), get("--out")
    if not base or not world or not out:
        print(__doc__)
        return 1
    dry = "--dry" in a
    want = [
        c.strip()
        for c in (get("--cups") or ",".join(c[0] for c in CUPS)).split(",")
        if c.strip()
    ]
    cups = [c for c in CUPS if c[0] in want]
    bad = [w for w in want if w not in {c[0] for c in CUPS}]
    if bad:
        print("unknown cup(s): %s" % ", ".join(bad))
        return 1

    if not dry:
        restore(base, world)

    comp = pesdb.wesys_unpack(
        io.open(os.path.join(base, "Competition.bin"), "rb").read()
    )
    regs = pesdb.wesys_unpack(
        io.open(os.path.join(base, "CompetitionRegulation.bin"), "rb").read()
    )
    ents = pesdb.wesys_unpack(
        io.open(os.path.join(base, "CompetitionEntry.bin"), "rb").read()
    )
    C = [comp[i : i + M.COMP] for i in range(0, len(comp), M.COMP)]
    R = [regs[i : i + M.REG] for i in range(0, len(regs), M.REG)]
    E = [ents[i : i + M.ENT] for i in range(0, len(ents), M.ENT)]

    used_cid = {c[M.CID_OFF] for c in C} | {
        c[M.CID_OFF] | (c[M.C_CID_HI] << 8) for c in C
    }
    used_reg = {int.from_bytes(r[M.R_ID : M.R_ID + 2], "little") for r in R}
    for name, code, cid, _conf, _region, _groups, _size, _src in cups:
        if cid in used_cid:
            raise SystemExit("%s: cid %d is taken" % (name, cid))

    picks = pick(C, R, E, world, cups)

    def ids_of(reg, groups):
        if not groups:
            return [reg]
        return [reg] + [reg + (g + 1) * 1024 for g in range(groups)]

    pool = [r for r in range(176, 1024) if r not in used_reg]
    args = [
        sys.executable,
        os.path.join(HERE, "mkccup.py"),
        "--base",
        base,
        "--out",
        out,
    ]
    lines = []
    for name, code, cid, conf, region, groups, size, _src in cups:
        reg = None
        for cand in pool:
            if not [i for i in ids_of(cand, groups) if i in used_reg]:
                reg = cand
                break
        if reg is None:
            raise SystemExit("%s: no free regulation id left" % name)
        pool.remove(reg)
        for i in ids_of(reg, groups):
            used_reg.add(i)
        if groups:
            ko = pool.pop(0)
            used_reg.add(ko)
        else:
            ko = reg
        entry = ",".join("0:%d" % t for t in picks[name])
        spec = "|".join(
            [
                name,
                code,
                str(cid),
                str(reg),
                str(ko),
                str(groups),
                entry,
                str(max(2, min(7, conf))),
                str(region),
            ]
        )
        if not groups:
            spec += "|%d" % SETTLED["like"]
        args += ["--cup", spec]
        lines.append(
            "ccup %d ko=%d groups=%d entry=%s cid=%d conf=%d region=%d clubs=%s name=%s"
            % (
                reg,
                ko,
                groups,
                entry,
                cid,
                conf,
                region,
                ",".join(str(t) for t in picks[name]),
                name,
            )
        )
        print(
            "  %-32s cid %d  reg %d%s"
            % (name, cid, reg, " + %d groups" % groups if groups else "")
        )

    if dry:
        print("\n".join(lines))
        print("dry run: nothing written")
        return 0

    rc = subprocess.call(args)
    if rc:
        print("mkccup failed (%d)" % rc)
        return rc

    # mkccup writes the code at +0x08, which runs over +0x14: put the name where the menu
    # reads it (mk_sudamericana.py did the same for the Custom Cup row)
    comp = bytearray(
        pesdb.wesys_unpack(io.open(os.path.join(base, "Competition.bin"), "rb").read())
    )
    by_cid = {comp[i + M.CID_OFF]: i for i in range(0, len(comp), M.COMP)}
    for name, code, cid, conf, _region, _groups, _size, _src in cups:
        i = by_cid.get(cid & 0xFF)
        if i is not None and comp[i + M.C_CID_HI] == (cid >> 8):
            M.put(comp, i + 0x14, name, 16)
            comp[i + M.FLAG_OFF] = (comp[i + M.FLAG_OFF] & ~0x07) | (conf & 0x07)
    io.open(os.path.join(base, "Competition.bin"), "wb").write(
        pesdb.wesys_pack(bytes(comp))
    )

    s = io.open(world, encoding="utf-8", errors="replace").read().splitlines()
    have = {l.split()[1] for l in s if l.startswith("ccup ") and len(l.split()) > 1}
    add = [l for l in lines if l.split()[1] not in have]
    s += add
    io.open(world, "w", encoding="utf-8", newline="\n").write("\n".join(s) + "\n")
    print("added %d ccup line(s) to %s" % (len(add), world))
    return 0


if __name__ == "__main__":
    sys.exit(main())
