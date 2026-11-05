r"""python mk_ofc_cl.py --base <pesdb> --worldfile <fl26world.txt> [--go]

Build the OFC Champions League the world has not got: 8 clubs (the top two of the four OFC
leagues in the world) in two groups of four and a knockout of four.

The shape is copied from the AFC Champions League Two (cid 603, master 279, knockout 280). Every
new regulation id stays below 1024 so `id & 0x3ff` still names the master.

Dry run by default; --go writes the tables and both copies of the world file after copying them
to *.before-ofccl.
"""

import argparse
import io
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import mkleague as M
import pesdb

COMP, REG, ENT = 36, 2352, 12
R_ID, R_CID, R_CID_HI, R_TEAMS = 0x02, 0x08, 0x492, 0x0B
NAME_RUN2, NAME_SLOT = 0x4B2, 115
TEMPLATE_CID, TEMPLATE_MASTER, TEMPLATE_KO = 603, 279, 280
GROUPS, CLUBS = 2, 8
NAME, CODE = "OFC Champions League", "FL_OFCCL"
ENTRY = [182, 197, 198, 8463]  # the four OFC leagues of the world


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

    cid = next(c for c in range(256, 1024) if c not in used_c and (c & 0xFF))
    master = next(
        m
        for m in range(1, 1024)
        if m not in used_r
        and all((m + 1024 * (k + 1)) not in used_r for k in range(GROUPS))
    )
    ko = next(m for m in range(1, 1024) if m not in used_r and m != master)

    reg_rec = {
        int.from_bytes(regs[o + R_ID : o + R_ID + 2], "little"): regs[o : o + REG]
        for o in range(0, len(regs) - REG + 1, REG)
    }
    comp_rec = {
        comp[o + 5] | (comp[o + 7] << 8): comp[o : o + COMP]
        for o in range(0, len(comp) - COMP + 1, COMP)
    }

    c = bytearray(comp_rec[TEMPLATE_CID])
    M.set_comp_cid(c, 0, cid)
    c[M.CODE_OFF : M.CODE_OFF + 28] = CODE.encode()[:27].ljust(28, b"\0")
    c[0x14:0x24] = NAME.encode("utf-8")[:15].ljust(16, b"\0")

    def reg_copy(src, new_id, teams):
        r = bytearray(reg_rec[src])
        r[R_ID : R_ID + 2] = new_id.to_bytes(2, "little")
        r[R_CID] = cid & 0xFF
        r[R_CID_HI] = (cid >> 8) & 0xFF
        r[R_TEAMS] = (r[R_TEAMS] & 0xC0) | (teams & 0x3F)
        set_reg_name(r, NAME)
        return r

    reg_rows = [reg_copy(TEMPLATE_MASTER, master, CLUBS)]
    for g in range(GROUPS):
        reg_rows.append(
            reg_copy(TEMPLATE_MASTER + 1024 * (g + 1), master + 1024 * (g + 1), CLUBS)
        )
    reg_rows.append(reg_copy(TEMPLATE_KO, ko, 4))

    teams_of = {}
    for o in range(0, len(ents) - ENT + 1, ENT):
        c2 = ents[o + 8] | (ents[o + 0x0B] << 8)
        teams_of.setdefault(c2, []).append(
            (ents[o + 9], int.from_bytes(ents[o : o + 4], "little"))
        )
    for v in teams_of.values():
        v.sort()

    reg2cid = {
        int.from_bytes(regs[o + 2 : o + 4], "little"): regs[o + 8]
        | (regs[o + 0x492] << 8)
        for o in range(0, len(regs) - REG + 1, REG)
    }
    picks = []
    for pos in (1, 2):
        for rid in ENTRY:
            for p, t in teams_of.get(reg2cid.get(rid), []):
                if p == pos:
                    picks.append(t)
                    break

    print(
        "OFC CL: cid %d, master %d, replicas %s, ko %d, %d clubs"
        % (
            cid,
            master,
            [master + 1024 * (k + 1) for k in range(GROUPS)],
            ko,
            len(picks),
        )
    )
    if len(picks) != CLUBS:
        raise SystemExit("expected %d clubs, found %d" % (CLUBS, len(picks)))

    max_eid = max(
        int.from_bytes(ents[o + 4 : o + 8], "little")
        for o in range(0, len(ents) - ENT + 1, ENT)
    )
    ent_rows = []
    for k, t in enumerate(picks):
        e = bytearray(ENT)
        e[0:4] = t.to_bytes(4, "little")
        e[4:8] = (max_eid + 1 + k).to_bytes(4, "little")
        e[8] = cid & 0xFF
        e[9] = k + 1
        e[0x0B] = (cid >> 8) & 0xFF
        ent_rows.append(e)

    line = "ccup %d ko=%d groups=%d entry=%s cid=%d conf=7 region=26 name=%s" % (
        master,
        ko,
        GROUPS,
        ",".join("%d:%d" % (r, p) for p in (1, 2) for r in ENTRY),
        cid,
        NAME,
    )
    print(line)
    if not a.go:
        print("dry run: nothing written (pass --go)")
        return 0

    for n in ("Competition.bin", "CompetitionRegulation.bin", "CompetitionEntry.bin"):
        dst = os.path.join(a.base, n + ".before-ofccl")
        if not os.path.exists(dst):
            shutil.copy2(os.path.join(a.base, n), dst)
    comp += c
    for r in reg_rows:
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
        l.split("name=")[-1].strip() == NAME for l in lines if l.startswith("ccup ")
    ):
        block = [l for l in lines if l.startswith("ccup ")] + [line]
        block.sort(key=lambda l: l.split("name=", 1)[-1].strip().lower())
        rest = [l for l in lines if not l.startswith("ccup ")]
        first = next(
            (i for i, l in enumerate(lines) if l.startswith("ccup ")), len(lines)
        )
        out = rest[:first] + block + rest[first:]
        text = "\n".join(out) + "\n"
        io.open(wf, "w", encoding="utf-8", newline="\n").write(text)
        live = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(a.base)))),
            "fl26world.txt",
        )
        if os.path.abspath(live) != os.path.abspath(wf):
            io.open(live, "w", encoding="utf-8", newline="\n").write(text)
    print("written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
