"""python make_carabao.py --base <world pesdb> --worldfile <fl26world.txt>
                         [--cup-cid 235] [--cup-reg 266] [--dry]

Put the Carabao Cup into a world that has no free competition id, by turning one of the
competitions it already has into it: the default is the Campeonato Cearense (competition 235,
regulation 266), one of the Brazilian state cups of the test copy.

What it writes
  Competition.bin            the competition row copies the FA Cup's (region 32, UEFA, the
                             English flagship), with the new id and the code FL_CARAB
  CompetitionRegulation.bin  regulation <reg> copies the FA Cup's row (reg 23: a knockout of 44,
                             one match a round, its calendar), with the new id and name
  CompetitionEntry.bin       the old entries go; 44 new ones follow: the 20 Premier League clubs
                             (reg 17) and the 24 of the Championship (reg 79)
  the world file             the `ccup` line becomes the Carabao Cup (the same days, fill and
                             byes the builder gives it), and the world gets the UEFA access list
                             with `uefa <reg> 0 2 17` -- its winner plays the Conference League

The access list is the shipped one (116 places, the same table the module has compiled) plus
the cup winner's place; writing it is what makes the winner's place possible, because a world
without uefa lines uses the module's table, which cannot know the cup.

Both world files must be the same file: pass each of them once.
"""

import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pesdb
import mkleague as M
import fl26world as W

FA_CUP_CID = 15
FA_CUP_REG = 23
PL_REG, CH_REG = 17, 79
REGION, CONF = 32, 2
DAYS = "238,265,300,356,13,73"
FILL = 226


def main():
    a = sys.argv[1:]
    get = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    base, wf = get("--base"), get("--worldfile")
    if not base or not wf:
        print(__doc__)
        return 1
    cid, reg = int(get("--cup-cid", "235")), int(get("--cup-reg", "266"))
    dry = "--dry" in a

    comp = bytearray(M.load(base, "Competition.bin"))
    regs = bytearray(M.load(base, "CompetitionRegulation.bin"))
    ents = bytearray(M.load(base, "CompetitionEntry.bin"))

    def comp_row(which):
        for i in range(0, len(comp), M.COMP):
            if comp[i + M.CID_OFF] == which:
                return i
        return None

    def reg_row(which):
        for i in range(0, len(regs), M.REG):
            if int.from_bytes(regs[i + M.R_ID : i + M.R_ID + 2], "little") == which:
                return i
        return None

    src_c, dst_c = comp_row(FA_CUP_CID), comp_row(cid)
    src_r, dst_r = reg_row(FA_CUP_REG), reg_row(reg)
    if None in (src_c, dst_c, src_r, dst_r):
        print(
            "missing rows: FA Cup competition/regulation or the target %d/%d"
            % (cid, reg)
        )
        return 1

    # the clubs: the Premier League and the Championship in their entry order
    def clubs_of(league_reg):
        c_id = int.from_bytes(
            regs[reg_row(league_reg) + M.R_CID : reg_row(league_reg) + M.R_CID + 1],
            "little",
        )
        rows = sorted(
            (ents[i + M.E_ORDER], int.from_bytes(ents[i : i + 4], "little"))
            for i in range(0, len(ents), M.ENT)
            if ents[i + M.E_CID] == c_id
        )
        return [t for _o, t in rows]

    field = clubs_of(PL_REG) + clubs_of(CH_REG)
    if len(field) != 44:
        print(
            "the field is %d clubs (20 Premier + 24 Championship expected)" % len(field)
        )
        return 1

    eid = max(
        int.from_bytes(ents[i + M.E_EID : i + M.E_EID + 4], "little")
        for i in range(0, len(ents), M.ENT)
    )
    print(
        "competition %d -> Carabao Cup (the FA Cup's row), regulation %d -> a knockout of 44"
        % (cid, reg)
    )
    print("  entries: %d clubs (Premier League and Championship)" % len(field))
    print("  uefa %d 0 2 %d (the winner plays the Conference League)" % (reg, PL_REG))
    if dry:
        print("dry run: nothing written")
        return 0

    # competition row
    c = bytearray(comp[src_c : src_c + M.COMP])
    c[M.CID_OFF] = cid
    M.put(c, M.CODE_OFF, "FL_CARAB", M.COMP - M.CODE_OFF)
    # region and confederation stay the FA Cup's (England, UEFA)
    comp[dst_c : dst_c + M.COMP] = c
    # regulation row
    r = bytearray(regs[src_r : src_r + M.REG])
    r[M.R_BELOW : M.R_BELOW + 2] = bytes(2)
    r[M.R_ID : M.R_ID + 2] = reg.to_bytes(2, "little")
    r[M.R_CID] = cid
    M.put_names(r, 0, "Carabao Cup")
    regs[dst_r : dst_r + M.REG] = r
    # entries
    keep = [
        ents[i : i + M.ENT]
        for i in range(0, len(ents), M.ENT)
        if ents[i + M.E_CID] != cid
    ]
    for k, t in enumerate(field):
        e = bytearray(M.ENT)
        e[M.E_TEAM : M.E_TEAM + 4] = t.to_bytes(4, "little")
        eid += 1
        e[M.E_EID : M.E_EID + 4] = eid.to_bytes(4, "little")
        e[M.E_CID], e[M.E_ORDER] = cid, k + 1
        keep.append(e)
    ents = b"".join(keep)
    for n, b in (
        ("Competition.bin", comp),
        ("CompetitionRegulation.bin", regs),
        ("CompetitionEntry.bin", ents),
    ):
        open(os.path.join(base, n), "wb").write(pesdb.wesys_pack(bytes(b)))

    # the world file: the ccup line and the access list
    lines = io.open(wf, encoding="utf-8", errors="replace").read().splitlines()
    out = []
    for l in lines:
        w = l.split()
        if w and w[0] == "ccup" and len(w) > 1 and w[1] == str(reg):
            continue
        if w and w[0] == "uefa":
            continue
        out.append(l)
    entry = (
        ",".join("%d:%d" % (PL_REG, p) for p in range(1, 21))
        + ","
        + ",".join("%d:%d" % (CH_REG, p) for p in range(1, 25))
    )
    out.append(
        "ccup %d ko=%d groups=0 entry=%s cid=%d fill=%d national=1 days=%s like=%d "
        "draw=byes name=Carabao Cup" % (reg, reg, entry, cid, FILL, DAYS, FA_CUP_REG)
    )
    uefa, _over = W.uefa_places([[reg, 0, 2, PL_REG]], [], True)
    out += ["uefa %d %d %d %d" % tuple(e) for e in uefa]
    io.open(wf, "w", encoding="utf-8", newline="\n").write("\n".join(out) + "\n")
    print("written: %s (%d uefa lines)" % (wf, len(uefa)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
