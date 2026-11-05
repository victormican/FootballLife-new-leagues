r"""python dup_cups.py --world <pesdb dir> --worldfile <fl26world.txt>
                     [--suffix " II"] [--limit N] [--only TEXT] [--go]

Duplicate the world's straight-knockout cups: each one gets a new competition id and a new
regulation (a full copy of its row and its entries), and a `ccup` line with the same entrants,
dates and shape, with a suffix on the name.

Only `groups=0` cups are duplicated: a group cup has a master regulation, one replica per group
and a knockout, and duplicating it needs all three; a straight knockout is a single regulation.

Cost per duplicated cup: 1 competition id, 1 regulation id, the same entries. No clubs, no
players, no slots. This world has 527 competition ids and 659 regulation ids free, so the 271
cups fit twice (```962 regulations```); the cup menu needs its rows raised to 1.024 first
(`fl26cupgrow`), because 542 cups do not fit in 512.

    --dry (default) prints the plan; --go writes the three tables and both copies of the world
    file, after copying them to *.before-dupcups.
"""

import argparse
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import mkleague as M
import pesdb

COMP, REG, ENT = 36, 2352, 12
R_RID, R_CID, R_TEAMS, R_CID_HI = 0x02, 0x08, 0x0B, 0x492
NAME_RUN2, NAME_SLOT = 0x4B2, 115


def load(d, n):
    with open(os.path.join(d, n), "rb") as f:
        return bytearray(pesdb.wesys_unpack(f.read()))


def set_reg_name(r, name):
    b = pesdb.game_text(name).encode("utf-8")[:114]
    b = b.decode("utf-8", "ignore").encode("utf-8")
    for k in range(10):
        o = 0x14 + k * NAME_SLOT
        r[o : o + NAME_SLOT] = b + bytes(NAME_SLOT - len(b))
    for k in range(10):
        o = NAME_RUN2 + k * NAME_SLOT
        r[o : o + NAME_SLOT] = b + bytes(NAME_SLOT - len(b))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--world", required=True)
    ap.add_argument("--worldfile", required=True)
    ap.add_argument("--suffix", default=" II")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--only", default="")
    ap.add_argument("--go", action="store_true")
    a = ap.parse_args()

    comp = load(a.world, "Competition.bin")
    regs = load(a.world, "CompetitionRegulation.bin")
    ents = load(a.world, "CompetitionEntry.bin")

    used_c = {
        comp[o + 5] | (comp[o + 7] << 8) for o in range(0, len(comp) - COMP + 1, COMP)
    }
    used_r = {
        int.from_bytes(regs[o + R_RID : o + R_RID + 2], "little")
        for o in range(0, len(regs) - REG + 1, REG)
    }
    free_c = [c for c in range(256, 1024) if c not in used_c and (c & 0xFF)]
    free_r = [r for r in range(1, 1201) if r not in used_r]

    lines = open(a.worldfile, encoding="utf-8", errors="replace").read().splitlines()
    cups = []
    for i, line in enumerate(lines):
        p = line.split()
        if not p or p[0] != "ccup":
            continue
        d = {"reg": p[1]}
        for tok in p[2:]:
            if "=" in tok:
                k, v = tok.split("=", 1)
                d[k] = v
        m = re.search(r"name=(.*)$", line)
        d["name"] = m.group(1).strip() if m else ""
        if d.get("groups", "0") != "0":
            continue
        if not d.get("ko"):
            continue
        if a.only and a.only.lower() not in d["name"].lower():
            continue
        cups.append((i, line, d))
    if a.limit:
        cups = cups[: a.limit]
    print(
        "straight-knockout cups to duplicate: %d (free cid %d, free reg %d)"
        % (len(cups), len(free_c), len(free_r))
    )
    if len(cups) > min(len(free_c), len(free_r)):
        raise SystemExit("not enough free ids")

    comp_rows, reg_rows, ent_rows, new_lines = [], [], [], []
    max_eid = max(
        int.from_bytes(ents[o + 4 : o + 8], "little")
        for o in range(0, len(ents) - ENT + 1, ENT)
    )
    for k, (idx, line, d) in enumerate(cups):
        cid, rid = free_c[k], free_r[k]
        old_cid = int(d.get("cid", 0) or 0)
        old_reg = int(d.get("ko", 0) or 0)
        cr = next(
            (
                comp[o : o + COMP]
                for o in range(0, len(comp) - COMP + 1, COMP)
                if (comp[o + 5] | (comp[o + 7] << 8)) == old_cid
            ),
            None,
        )
        rr = next(
            (
                regs[o : o + REG]
                for o in range(0, len(regs) - REG + 1, REG)
                if int.from_bytes(regs[o + R_RID : o + R_RID + 2], "little") == old_reg
            ),
            None,
        )
        if cr is None or rr is None:
            print(
                "  SKIP %-40s (cid %d / reg %d not found)"
                % (d["name"][:40], old_cid, old_reg)
            )
            continue
        c = bytearray(cr)
        M.set_comp_cid(c, 0, cid)
        c[M.CODE_OFF : M.CODE_OFF + 28] = (
            ("FL_DUP_%d" % cid).encode()[:27].ljust(28, b"\0")
        )
        c[0x14:0x24] = (d["name"] + a.suffix).encode("utf-8")[:15].ljust(16, b"\0")
        r = bytearray(rr)
        r[R_RID : R_RID + 2] = rid.to_bytes(2, "little")
        r[R_CID] = cid & 0xFF
        r[R_CID_HI] = (cid >> 8) & 0xFF
        set_reg_name(r, d["name"] + a.suffix)
        rows = []
        for o in range(0, len(ents) - ENT + 1, ENT):
            if (ents[o + 8] | (ents[o + 0x0B] << 8)) != old_cid:
                continue
            e = bytearray(ents[o : o + ENT])
            max_eid += 1
            e[4:8] = max_eid.to_bytes(4, "little")
            e[8] = cid & 0xFF
            e[0x0B] = (cid >> 8) & 0xFF
            rows.append(e)
        if not rows:
            print("  SKIP %-40s (no entries)" % d["name"][:40])
            continue
        text = line.replace("ccup %d" % old_reg, "ccup %d" % rid, 1)
        text = text.replace("ko=%d" % old_reg, "ko=%d" % rid, 1)
        text = re.sub(r"cid=\d+", "cid=%d" % cid, text, count=1)
        text = re.sub(r"name=.*$", "name=%s%s" % (d["name"], a.suffix), text)
        comp_rows.append(c)
        reg_rows.append(r)
        ent_rows.extend(rows)
        new_lines.append((d["name"] + a.suffix, text))
        if k < 5:
            print(
                "   %-34s cid %-4d reg %-4d (%d entries)"
                % (d["name"][:34], cid, rid, len(rows))
            )
    print("planned: %d cups" % len(new_lines))
    if not a.go:
        print("dry run: nothing written (pass --go)")
        return

    for n in ("Competition.bin", "CompetitionRegulation.bin", "CompetitionEntry.bin"):
        dst = os.path.join(a.world, n + ".before-dupcups")
        if not os.path.exists(dst):
            shutil.copy2(os.path.join(a.world, n), dst)
    for c in comp_rows:
        comp += c
    for r in reg_rows:
        regs += r
    for e in ent_rows:
        ents += e
    with open(os.path.join(a.world, "Competition.bin"), "wb") as f:
        f.write(pesdb.wesys_pack(bytes(comp)))
    with open(os.path.join(a.world, "CompetitionRegulation.bin"), "wb") as f:
        f.write(pesdb.wesys_pack(bytes(regs)))
    with open(os.path.join(a.world, "CompetitionEntry.bin"), "wb") as f:
        f.write(pesdb.wesys_pack(bytes(ents)))

    body = [l for l in lines if l.startswith("ccup ")] + [t for _n, t in new_lines]
    body.sort(key=lambda l: (l.split("name=", 1)[-1].strip().lower(), l))
    rest = [l for l in lines if not l.startswith("ccup ")]
    first = next((i for i, l in enumerate(lines) if l.startswith("ccup ")), len(lines))
    out = rest[:first] + body + rest[first:]
    text = "\n".join(out) + "\n"
    dst = a.worldfile + ".before-dupcups"
    if not os.path.exists(dst):
        shutil.copy2(a.worldfile, dst)
    with open(a.worldfile, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    live = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(a.world)))),
        "fl26world.txt",
    )
    if os.path.abspath(live) != os.path.abspath(a.worldfile):
        with open(live, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
    print("written: %d cups duplicated" % len(new_lines))


if __name__ == "__main__":
    main()
