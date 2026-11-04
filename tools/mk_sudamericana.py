"""python mk_sudamericana.py --base <pesdb> --worldfile <fl26world.txt> [--dry] [--revert]

Copa Sudamericana en la fila de la "Custom Cup" (cid 37), que el juego trae **sin un solo club**
y por tanto es el único hueco libre que queda: los 255 ids estan gastados.

Reglas: 32 clubes de las ligas CONMEBOL del mundo (conf=4), tomando los puestos 5 y siguientes de
cada una (los 4 primeros van a la Libertadores), 8 grupos de 4 y eliminatoria de 16 -- la forma de
la propia Libertadores (reg 47 grupos, 48 eliminatoria), que es lo que la fila ya tiene.
"""

import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pesdb
import mkleague as M

CID = 37
REG_GROUP, REG_KO = 47, 48
NAME = "Copa Sudamericana"
CODE = "FL_SUDAMER"


def main():
    a = sys.argv[1:]
    get = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    base, wf = get("--base"), get("--worldfile")
    if not base or not wf:
        print(__doc__)
        return 2
    dry = "--dry" in a

    comp = bytearray(M.load(base, "Competition.bin"))
    regs = bytearray(M.load(base, "CompetitionRegulation.bin"))
    ents = bytearray(M.load(base, "CompetitionEntry.bin"))

    # las ligas CONMEBOL del mundo, con sus clubes por puesto
    leagues = []
    for line in io.open(wf, encoding="utf-8", errors="replace"):
        if not line.startswith("league "):
            continue
        kv = dict(re.findall(r"(\w+)=(-?\d+)", line))
        if int(kv.get("conf", 0)) != 4:
            continue
        leagues.append(int(line.split()[1]))
    clubs = []
    for rid in leagues:
        cid = next(
            regs[i + M.R_CID]
            for i in range(0, len(regs), M.REG)
            if int.from_bytes(regs[i + M.R_ID : i + M.R_ID + 2], "little") == rid
        )
        have = sorted(
            (ents[k + M.E_ORDER], int.from_bytes(ents[k : k + 4], "little"))
            for k in range(0, len(ents), M.ENT)
            if ents[k + M.E_CID] == cid
        )
        for pos, tid in have[4:7]:
            if tid not in clubs:
                clubs.append(tid)
        if len(clubs) >= 32:
            break
    clubs = clubs[:32]
    print("%d club(es) de %d liga(s) CONMEBOL" % (len(clubs), len(leagues)))
    if len(clubs) < 32:
        raise SystemExit(
            "solo %d clubes: el mundo no tiene suficientes ligas CONMEBOL" % len(clubs)
        )

    # fila de competicion
    for i in range(0, len(comp), M.COMP):
        if comp[i + M.CID_OFF] == CID:
            M.put(comp, i + 0x14, NAME, 16)
            M.put(comp, i + M.CODE_OFF, CODE, M.COMP - M.CODE_OFF)
            M.put(comp, i + 0x14, NAME, 16)
            break
    # fase de grupos: 32 clubes otra vez (la habiamos subido a 33 para ocultarla)
    for i in range(0, len(regs), M.REG):
        rid = int.from_bytes(regs[i + M.R_ID : i + M.R_ID + 2], "little")
        if rid == REG_GROUP:
            regs[i + M.R_TEAMS] = (regs[i + M.R_TEAMS] & 0xC0) | 32
            M.put_names(regs, i, NAME)

    # entradas: las de cid 37 no existen (la Custom Cup estaba vacia)
    ents = bytes(ents)
    keep = bytearray()
    for k in range(0, len(ents), M.ENT):
        if ents[k + M.E_CID] != CID:
            keep += ents[k : k + M.ENT]
    ents = keep
    eid = max(
        int.from_bytes(ents[k + M.E_EID : k + M.E_EID + 4], "little")
        for k in range(0, len(ents), M.ENT)
    )
    for n, tid in enumerate(clubs, 1):
        e = bytearray(M.ENT)
        e[M.E_TEAM : M.E_TEAM + 4] = tid.to_bytes(4, "little")
        e[M.E_EID : M.E_EID + 4] = (eid + n).to_bytes(4, "little")
        e[M.E_CID] = CID
        e[M.E_ORDER] = n
        ents += e
    print("%s: cid %d, %d entradas" % (NAME, CID, len(clubs)))

    ccup = "ccup %d ko=%d groups=8 entry=%s cid=%d conf=4 region=1 clubs=%s name=%s" % (
        REG_GROUP,
        REG_KO,
        ",".join("0:%d" % t for t in clubs),
        CID,
        ",".join(str(t) for t in clubs),
        NAME,
    )
    if dry:
        print(ccup)
        print("dry run: nothing written")
        return 0
    open(os.path.join(base, "Competition.bin"), "wb").write(
        pesdb.wesys_pack(bytes(comp))
    )
    open(os.path.join(base, "CompetitionRegulation.bin"), "wb").write(
        pesdb.wesys_pack(bytes(regs))
    )
    open(os.path.join(base, "CompetitionEntry.bin"), "wb").write(
        pesdb.wesys_pack(bytes(ents))
    )

    lines = io.open(wf, encoding="utf-8", errors="replace").read().splitlines()
    lines = [
        l for l in lines if not (l.startswith("ccup ") and " cid=%d " % CID in l + " ")
    ]
    idx = max(i for i, l in enumerate(lines) if l.startswith("ccup "))
    lines.insert(idx + 1, ccup)
    io.open(wf, "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
    print("world: %d lineas" % len(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
