r"""python mk_otros_ofc.py --base <pesdb> --worldfile <fl26world.txt> [--go]

"Otros OFC": the Oceania counterpart of "Otros Concacaf" (slot 247). A practice league on a
slot of its own (248) with the clubs of the world's four OFC leagues, served by fl26clubs.

The competition and the regulation are copies of "Otros Concacaf" (cid 221, reg 250, type 8),
so it behaves the same; only the id, the name and the club list change.

Dry run by default; --go writes the tables and both copies of the world file after copying them
to *.before-otrosofc.
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
import pesdb

COMP, REG, ENT = 36, 2352, 12
R_ID, R_CID, R_CID_HI, R_TEAMS = 0x02, 0x08, 0x492, 0x0B
NAME_RUN2, NAME_SLOT = 0x4B2, 115
TEMPLATE_CID, TEMPLATE_REG = 221, 250
SLOT = 248
NAME = "Otros OFC"


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

    # the four OFC leagues of the world -> their clubs
    teams_of = {}
    for o in range(0, len(ents) - ENT + 1, ENT):
        c2 = ents[o + 8] | (ents[o + 0x0B] << 8)
        teams_of.setdefault(c2, []).append(
            (ents[o + 9], int.from_bytes(ents[o : o + 4], "little"))
        )
    cids, seen = [], set()
    for l in io.open(a.worldfile, encoding="utf-8", errors="replace"):
        if not l.startswith("league "):
            continue
        d = dict(re.findall(r"(\w+)=([^ ]+)", l))
        if d.get("conf") == "7" and d.get("cid") and d.get("slot") not in ("-1", "123"):
            if int(d["cid"]) not in seen:
                seen.add(int(d["cid"]))
                cids.append(int(d["cid"]))
    teams = []
    for c2 in cids:
        for pos, t in sorted(teams_of.get(c2, [])):
            if t not in teams:
                teams.append(t)
    teams = teams[:48]
    print("ligas OFC cids:", cids, "| clubes:", len(teams))
    if len(teams) < 2:
        raise SystemExit("no hay clubes OFC")

    cid = next(c for c in range(256, 1024) if c not in used_c and (c & 0xFF))
    reg = next(r for r in range(1, 1024) if r not in used_r)

    c = bytearray(comp_rec[TEMPLATE_CID])
    M.set_comp_cid(c, 0, cid)
    c[M.CODE_OFF : M.CODE_OFF + 28] = ("FL_OFC_LEAGUE").encode()[:27].ljust(28, b"\0")
    c[0x14:0x24] = NAME.encode("utf-8")[:15].ljust(16, b"\0")

    r = bytearray(reg_rec[TEMPLATE_REG])
    r[R_ID : R_ID + 2] = reg.to_bytes(2, "little")
    r[R_CID] = cid & 0xFF
    r[R_CID_HI] = (cid >> 8) & 0xFF
    r[R_TEAMS] = (r[R_TEAMS] & 0xC0) | (len(teams) & 0x3F)
    set_reg_name(r, NAME)

    max_eid = max(
        int.from_bytes(ents[o + 4 : o + 8], "little")
        for o in range(0, len(ents) - ENT + 1, ENT)
    )
    ent_rows = []
    for k, t in enumerate(teams):
        e = bytearray(ENT)
        e[0:4] = t.to_bytes(4, "little")
        e[4:8] = (max_eid + 1 + k).to_bytes(4, "little")
        e[8] = cid & 0xFF
        e[9] = k + 1
        e[0x0B] = (cid >> 8) & 0xFF
        ent_rows.append(e)

    line = (
        "league %d cid=%d region=25 country=166 conf=7 slot=%d tier=3 promote=0 demote=0 "
        "clubs=%d legs=2 kickoff=166 exhibition=1 name=%s"
        % (reg, cid, SLOT, len(teams), NAME)
    )
    print("cid %d, reg %d, slot %d, %d clubes" % (cid, reg, SLOT, len(teams)))
    print(line)
    if not a.go:
        print("dry run: nothing written (pass --go)")
        return 0

    for n in ("Competition.bin", "CompetitionRegulation.bin", "CompetitionEntry.bin"):
        dst = os.path.join(a.base, n + ".before-otrosofc")
        if not os.path.exists(dst):
            shutil.copy2(os.path.join(a.base, n), dst)
    comp += c
    regs += r
    for e in ent_rows:
        ents += e
    open(os.path.join(a.base, "Competition.bin"), "wb").write(
        pesdb.wesys_pack(bytes(comp))
    )
    open(os.path.join(a.base, "CompetitionRegulation.bin"), "wb").write(
        pesdb.wesys_pack(bytes(regs))
    )
    open(os.path.join(a.base, "CompetitionEntry.bin"), "wb").write(
        pesdb.wesys_pack(bytes(ents))
    )

    wf = a.worldfile
    lines = io.open(wf, encoding="utf-8", errors="replace").read().splitlines()
    if not any(
        l.split("name=")[-1].strip() == NAME for l in lines if l.startswith("league ")
    ):
        at = next(i for i, l in enumerate(lines) if l.startswith("league "))
        lines.insert(at, line)
    text = "\n".join(lines) + "\n"
    io.open(wf, "w", encoding="utf-8", newline="\n").write(text)
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
