r"""python mk_regional_cups.py --base <pesdb> --worldfile <fl26world.txt> [--go]

Create the regional cups the world has not got:

  nacionales  African Nations Championship (CHAN), ASEAN Championship, CAFA Nations Cup,
              WAFF Championship, EAFF E-1, SAFF Championship
  clubes      Copa UNAF, WAFU A/B Club Championship, UNIFFAC, CECAFA Kagame Cup,
              COSAFA Club Cup, ASEAN Club Championship, CAFA/WAFF/EAFF/SAFF Club Championship

Each one is a single-match knockout with byes (like the FA Cup, `like=23`): a competition row,
one regulation, its entries and a `ccup` line.  Clubs are the champions of the leagues of the
region that the world has; national teams, the countries' national teams.

Dry run by default; --go writes the tables and both copies of the world file after copying them
to *.before-regional.
"""

import argparse
import io
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import mkleague as M
import nations as N
import pesdb

COMP, REG, ENT = 36, 2352, 12
R_ID, R_CID, R_CID_HI, R_TEAMS = 0x02, 0x08, 0x492, 0x0B
NAME_RUN2, NAME_SLOT = 0x4B2, 115
TEMPLATE_CID, TEMPLATE_REG = 825, 531  # Albania Cup: a single-match knockout of 8
MAX = 16

# region -> country flag ids (Country.bin flag ids of this world)
UNAF = [76, 44, 92, 58]
WAFU_A = [83]
WAFU_B = [80, 64, 56]
UNIFFAC = [50, 55, 98]
CECAFA = [67, 90]
COSAFA = [87, 45, 94]
ASEAN = [10, 21, 36, 38]
CAFA = [240, 216, 42, 11]
WAFF = [2, 12, 14, 17, 26, 30, 37]
EAFF = [13, 16]
SAFF = [9]
CAF = sorted(set(UNAF + WAFU_A + WAFU_B + UNIFFAC + CECAFA + COSAFA))

CUPS = [
    ("African Nations Championship", "FL_CHAN", "national", CAF),
    ("Copa UNAF", "FL_UNAF", "club", UNAF),
    ("WAFU A Club Championship", "FL_WAFUA", "club", WAFU_A),
    ("WAFU B Club Championship", "FL_WAFUB", "club", WAFU_B),
    ("UNIFFAC Club Cup", "FL_UNIFFAC", "club", UNIFFAC),
    ("CECAFA Kagame Cup", "FL_CECAFA", "club", CECAFA),
    ("COSAFA Club Cup", "FL_COSAFA", "club", COSAFA),
    ("ASEAN Club Championship", "FL_ASEA", "club", ASEAN),
    ("CAFA Club Championship", "FL_CAFAC", "club", CAFA),
    ("WAFF Club Championship", "FL_WAFFC", "club", WAFF),
    ("EAFF Club Championship", "FL_EAFFC", "club", EAFF),
    ("SAFF Club Championship", "FL_SAFFC", "club", SAFF),
    ("ASEAN Championship", "FL_ASEN", "national", ASEAN),
    ("CAFA Nations Cup", "FL_CAFAN", "national", CAFA),
    ("WAFF Championship", "FL_WAFFN", "national", WAFF),
    ("EAFF E-1 Football Championship", "FL_EAFFN", "national", EAFF),
    ("SAFF Championship", "FL_SAFFN", "national", SAFF),
]


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
    ap.add_argument("--base", required=True)
    ap.add_argument("--worldfile", required=True)
    ap.add_argument("--countries", default="")
    ap.add_argument("--go", action="store_true")
    a = ap.parse_args()

    comp = load(a.base, "Competition.bin")
    regs = load(a.base, "CompetitionRegulation.bin")
    ents = load(a.base, "CompetitionEntry.bin")

    used_c = {
        comp[o + 5] | (comp[o + 7] << 8) for o in range(0, len(comp) - COMP + 1, COMP)
    }
    used_r = {
        int.from_bytes(regs[o + R_ID : o + R_ID + 2], "little")
        for o in range(0, len(regs) - REG + 1, REG)
    }
    comp_rec = {
        comp[o + 5] | (comp[o + 7] << 8): comp[o : o + COMP]
        for o in range(0, len(comp) - COMP + 1, COMP)
    }
    reg_rec = {
        int.from_bytes(regs[o + R_ID : o + R_ID + 2], "little"): regs[o : o + REG]
        for o in range(0, len(regs) - REG + 1, REG)
    }

    teams_of = {}
    for o in range(0, len(ents) - ENT + 1, ENT):
        c2 = ents[o + 8] | (ents[o + 0x0B] << 8)
        teams_of.setdefault(c2, []).append(
            (ents[o + 9], int.from_bytes(ents[o : o + 4], "little"))
        )
    for v in teams_of.values():
        v.sort()

    # league cid -> country flag, and the champion (position 1) of each
    leagues = {}
    for l in io.open(a.worldfile, encoding="utf-8", errors="replace"):
        if not l.startswith("league "):
            continue
        cid = re.search(r"\bcid=(\d+)", l)
        cty = re.search(r"\bcountry=(-?\d+)", l)
        if cid and cty:
            leagues[int(cid.group(1))] = int(cty.group(1))
    champ = {}
    for cid, flag in leagues.items():
        for pos, t in teams_of.get(cid, []):
            if pos == 1:
                champ.setdefault(flag, t)
                break

    nats = N.read(a.base, a.countries or a.base)
    by_flag = {}
    for n in nats:
        by_flag.setdefault(n["country"], []).append(n["id"])

    lines = io.open(a.worldfile, encoding="utf-8", errors="replace").read().splitlines()
    have = {l.split("name=")[-1].strip() for l in lines if l.startswith("ccup ")}

    new_lines, comp_rows, reg_rows, ent_rows = [], [], [], []
    max_eid = max(
        int.from_bytes(ents[o + 4 : o + 8], "little")
        for o in range(0, len(ents) - ENT + 1, ENT)
    )

    for name, code, kind, flags in CUPS:
        if name in have:
            print("  %-34s ya esta" % name[:34])
            continue
        if kind == "club":
            teams = [champ[f] for f in flags if f in champ]
        else:
            teams = [t for f in flags for t in by_flag.get(f, [])]
        teams = teams[:MAX]
        if len(teams) < 2:
            print("  SKIP %-34s (%d equipos)" % (name[:34], len(teams)))
            continue
        cid = next(c for c in range(256, 1024) if c not in used_c and (c & 0xFF))
        used_c.add(cid)
        reg = next(r for r in range(1, 1024) if r not in used_r)
        used_r.add(reg)

        c = bytearray(comp_rec[TEMPLATE_CID])
        M.set_comp_cid(c, 0, cid)
        c[M.CODE_OFF : M.CODE_OFF + 28] = code.encode()[:27].ljust(28, b"\0")
        c[0x14:0x24] = name.encode("utf-8")[:15].ljust(16, b"\0")
        comp_rows.append(c)

        r = bytearray(reg_rec[TEMPLATE_REG])
        r[R_ID : R_ID + 2] = reg.to_bytes(2, "little")
        r[R_CID] = cid & 0xFF
        r[R_CID_HI] = (cid >> 8) & 0xFF
        r[R_TEAMS] = (r[R_TEAMS] & 0xC0) | (len(teams) & 0x3F)
        set_reg_name(r, name)
        reg_rows.append(r)

        for k, t in enumerate(teams):
            e = bytearray(ENT)
            e[0:4] = t.to_bytes(4, "little")
            e[4:8] = (max_eid + 1 + k).to_bytes(4, "little")
            e[8] = cid & 0xFF
            e[9] = k + 1
            e[0x0B] = (cid >> 8) & 0xFF
            ent_rows.append(e)
        max_eid += len(teams)

        line = (
            "ccup %d ko=%d groups=0 entry=%s cid=%d fill=20 national=1 days=20,27,34,41 "
            "like=23 name=%s"
            % (reg, reg, ",".join("0:%d" % t for t in teams), cid, name)
        )
        new_lines.append(line)
        print(
            "  %-34s cid %-4d reg %-4d %2d equipos (%s)"
            % (name[:34], cid, reg, len(teams), kind)
        )

    print("copas nuevas:", len(new_lines))
    if not a.go:
        print("dry run: nothing written (pass --go)")
        return 0

    for n in ("Competition.bin", "CompetitionRegulation.bin", "CompetitionEntry.bin"):
        dst = os.path.join(a.base, n + ".before-regional")
        if not os.path.exists(dst):
            shutil.copy2(os.path.join(a.base, n), dst)
    comp += b"".join(comp_rows)
    regs += b"".join(reg_rows)
    ents += b"".join(ent_rows)
    open(os.path.join(a.base, "Competition.bin"), "wb").write(
        pesdb.wesys_pack(bytes(comp))
    )
    open(os.path.join(a.base, "CompetitionRegulation.bin"), "wb").write(
        pesdb.wesys_pack(bytes(regs))
    )
    open(os.path.join(a.base, "CompetitionEntry.bin"), "wb").write(
        pesdb.wesys_pack(bytes(ents))
    )

    rest = [l for l in lines if not l.startswith("ccup ")]
    block = [l for l in lines if l.startswith("ccup ")] + new_lines
    block.sort(key=lambda l: l.split("name=", 1)[-1].strip().lower())
    first = next((i for i, l in enumerate(lines) if l.startswith("ccup ")), len(lines))
    out = rest[:first] + block + rest[first:]
    text = "\n".join(out) + "\n"
    io.open(a.worldfile, "w", encoding="utf-8", newline="\n").write(text)
    live = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(a.base)))),
        "fl26world.txt",
    )
    if os.path.abspath(live) != os.path.abspath(a.worldfile):
        io.open(live, "w", encoding="utf-8", newline="\n").write(text)
    print("written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
