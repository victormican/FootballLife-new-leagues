r"""python dup_cups_groups.py --world <pesdb dir> --worldfile <fl26world.txt>
                             [--suffix " II"] [--go]

Duplicate the cups `dup_cups.py` leaves alone:

- group cups (groups>0): the master regulation, one replica per group at
  `master + 1024 * (g + 1)`, the knockout regulation and the entries;
- a cup with no entries of its own (Copa Intercontinental): its field comes from cup
  winners, so only the competition and the regulation are copied.

Every new master and knockout id stays below 1024: `fl26swiss` recognises a group or a tie as
`id & 0x3ff`, so a master above 1023 would break the replica arithmetic.

Dry run by default; --go writes the three tables and both copies of the world file after
copying them to *.before-dupgroups.
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
R_ID, R_CID, R_CID_HI, R_TEAMS = 0x02, 0x08, 0x492, 0x0B
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
        int.from_bytes(regs[o + R_ID : o + R_ID + 2], "little")
        for o in range(0, len(regs) - REG + 1, REG)
    }
    free_c = [c for c in range(256, 1024) if c not in used_c and (c & 0xFF)]
    free_m = [m for m in range(1, 1024) if m not in used_r]
    free_k = [m for m in range(1, 1024) if m not in used_r]

    lines = open(a.worldfile, encoding="utf-8", errors="replace").read().splitlines()
    cups = []
    for i, line in enumerate(lines):
        p = line.split()
        if not p or p[0] != "ccup":
            continue
        d = {"reg": int(p[1])}
        for tok in p[2:]:
            if "=" in tok:
                k, v = tok.split("=", 1)
                d[k] = v
        m = re.search(r"name=(.*)$", line)
        d["name"] = m.group(1).strip() if m else ""
        if d["name"].endswith(a.suffix.strip() or " II"):
            continue
        groups = int(d.get("groups", 0) or 0)
        cid = int(d.get("cid", 0) or 0)
        rows = [
            o
            for o in range(0, len(ents) - ENT + 1, ENT)
            if (ents[o + 8] | (ents[o + 0x0B] << 8)) == cid
        ]
        if not groups and rows:
            continue  # a straight knockout: dup_cups.py does it
        if not groups and not rows and ":0" not in d.get("entry", ""):
            continue  # nothing to copy and no cup winners
        if a.only and a.only.lower() not in d["name"].lower():
            continue
        cups.append((i, line, d, rows))

    print(
        "cups for this pass: %d (free cid %d, free master %d)"
        % (len(cups), len(free_c), len(free_m))
    )
    comp_rows, reg_rows, ent_rows, new_lines = [], [], [], []
    max_eid = max(
        int.from_bytes(ents[o + 4 : o + 8], "little")
        for o in range(0, len(ents) - ENT + 1, ENT)
    )
    reg_rec = {
        int.from_bytes(regs[o + R_ID : o + R_ID + 2], "little"): regs[o : o + REG]
        for o in range(0, len(regs) - REG + 1, REG)
    }
    comp_rec = {
        comp[o + 5] | (comp[o + 7] << 8): comp[o : o + COMP]
        for o in range(0, len(comp) - COMP + 1, COMP)
    }
    taken = set(used_r)

    def ids_ok(m, groups):
        return m not in taken and all(
            (m + 1024 * (k + 1)) not in taken for k in range(groups)
        )

    for idx, line, d, rows in cups:
        groups = int(d.get("groups", 0) or 0)
        cid = int(d.get("cid", 0) or 0)
        ko = int(d.get("ko", d["reg"]) or 0)
        master = d["reg"]
        if cid not in comp_rec or master not in reg_rec or ko not in reg_rec:
            print("  SKIP %-34s (missing row)" % d["name"][:34])
            continue
        if not free_c:
            raise SystemExit("no free ids left")
        new_cid = free_c.pop(0)
        new_m = next((m for m in free_m if ids_ok(m, groups)), None)
        if new_m is None:
            raise SystemExit("no free master with %d replicas" % groups)
        taken.add(new_m)
        for k in range(groups):
            taken.add(new_m + 1024 * (k + 1))
        if groups:
            new_k = next((m for m in free_k if m not in taken), None)
            if new_k is None:
                raise SystemExit("no free knockout id")
            taken.add(new_k)
        else:
            new_k = new_m  # a straight knockout: master and bracket are the same row

        c = bytearray(comp_rec[cid])
        M.set_comp_cid(c, 0, new_cid)
        c[M.CODE_OFF : M.CODE_OFF + 28] = (
            ("FL_DUP_%d" % new_cid).encode()[:27].ljust(28, b"\0")
        )
        c[0x14:0x24] = (d["name"] + a.suffix).encode("utf-8")[:15].ljust(16, b"\0")
        comp_rows.append(c)

        def reg_copy(src, new_id, name):
            r = bytearray(reg_rec[src])
            r[R_ID : R_ID + 2] = new_id.to_bytes(2, "little")
            r[R_CID] = new_cid & 0xFF
            r[R_CID_HI] = (new_cid >> 8) & 0xFF
            set_reg_name(r, name)
            used_r.add(new_id)
            reg_rows.append(r)

        label = d["name"] + a.suffix
        reg_copy(master, new_m, label)
        for g in range(groups):
            src = master + 1024 * (g + 1)
            if src not in reg_rec:
                raise SystemExit("reg %d has no replica %d" % (master, src))
            reg_copy(src, new_m + 1024 * (g + 1), label)
        if new_k != new_m:
            reg_copy(ko, new_k, label)

        for o in rows:
            e = bytearray(ents[o : o + ENT])
            max_eid += 1
            e[4:8] = max_eid.to_bytes(4, "little")
            e[8] = new_cid & 0xFF
            e[0x0B] = (new_cid >> 8) & 0xFF
            ent_rows.append(e)

        text = re.sub(r"^ccup %d" % master, "ccup %d" % new_m, line)
        text = re.sub(r"\bko=%d" % ko, "ko=%d" % new_k, text)
        text = re.sub(r"\bcid=\d+", "cid=%d" % new_cid, text, count=1)
        text = re.sub(r"name=.*$", "name=%s" % label, text)
        new_lines.append((label, text))
        print(
            "  %-34s cid %-4d master %-4d ko %-4d groups %d (%d entries)"
            % (d["name"][:34], new_cid, new_m, new_k, groups, len(rows))
        )

    print(
        "planned: %d cups, %d regulations, %d entries"
        % (len(new_lines), len(reg_rows), len(ent_rows))
    )
    if not a.go:
        print("dry run: nothing written (pass --go)")
        return 0

    for n in ("Competition.bin", "CompetitionRegulation.bin", "CompetitionEntry.bin"):
        dst = os.path.join(a.world, n + ".before-dupgroups")
        if not os.path.exists(dst):
            shutil.copy2(os.path.join(a.world, n), dst)
    for r in reg_rows:
        regs += r
    for e in ent_rows:
        ents += e
    for c in comp_rows:
        comp += c
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
    dst = a.worldfile + ".before-dupgroups"
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
    return 0


if __name__ == "__main__":
    sys.exit(main())
