"""python make_divisions.py --base <pesdb> --worldfile <fl26world.txt> [--dry]

Six new leagues of generic clubs, and the four "Other" filler leagues that go away to supply
them.

Spec (name, country flag id, confederation, tier, teams):
  Primera B Metropolitana  144 (Argentina) 4 3 22
  Federal A                144            4 3 38
  Primera C                144            4 4 28
  Torneo Federal           144            4 4 30
  Torneo Federal Brasil    146 (Brasil)   4 3 30
  Segunda Division Bolivia 145 (Bolivia)  4 2 48

Clubs come from the filler leagues (reg 364 Other European Leagues, 362 Other Latin American
Teams, 363 Other, 250 Otros Concacaf, which are deleted, and 256 Other Clubs (Asia), which keeps
the clubs that are left).  Each one is renamed "<name> NN", gets the country's flag id, and is
put in the new competition.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pesdb
import mkleague as M

T_REC, T_ID, T_NATIONAL, T_COUNTRY = 1532, 0x08, 0x53, 0x46
T_NAME, T_NAME_LEN, T_NAME_SLOTS, T_NAME_STEP = 0x9E, 70, 20, 70
T_ABBR, T_SHORT = 0x372, 0x35A
T_LONG, T_LONG_LEN = 0x37C, 22

SPEC = [
    ("Primera B Metropolitana", 144, 4, 3, 22, "FL_ARG_BM"),
    ("Federal A", 144, 4, 3, 38, "FL_ARG_FA"),
    ("Primera C", 144, 4, 4, 28, "FL_ARG_PC"),
    ("Torneo Federal", 144, 4, 4, 30, "FL_ARG_TF"),
    ("Torneo Federal Brasil", 146, 4, 3, 30, "FL_BRA_TF"),
    ("Segunda División Bolivia", 145, 4, 2, 48, "FL_BOL_SD"),
]
DELETE_REGS = [317, 318, 319, 320, 321, 322, 323, 324, 325, 326, 327, 328, 329, 330, 331, 332, 333, 336, 337, 338]
KEEP_REG, KEEP_TAKE = 317, 0
REGION = {144: 29, 146: 30, 145: 232}


def put_team_name(row, text):
    b = text.encode("utf-8")
    for k in range(T_NAME_SLOTS):
        o = T_NAME + k * T_NAME_STEP
        if o + T_NAME_LEN > T_REC:
            continue
        limit = (T_ABBR - T_SHORT) if o == T_SHORT else T_NAME_LEN - 1
        chunk = b[:limit]
        row[o : o + limit] = chunk + bytes(limit - len(chunk))
        if o != T_SHORT:
            row[o + limit] = 0
    chunk = b[: T_LONG_LEN - 1]
    row[T_LONG : T_LONG + T_LONG_LEN] = chunk + bytes(T_LONG_LEN - len(chunk))
    row[T_LONG + T_LONG_LEN - 1] = 0


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    a = sys.argv[1:]
    get = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    base, wf = get("--base"), get("--worldfile")
    if not base or not wf:
        print(__doc__)
        return 2
    dry = "--dry" in a

    comp = bytearray(
        pesdb.wesys_unpack(open(os.path.join(base, "Competition.bin"), "rb").read())
    )
    regs = bytearray(
        pesdb.wesys_unpack(
            open(os.path.join(base, "CompetitionRegulation.bin"), "rb").read()
        )
    )
    ents = bytearray(
        pesdb.wesys_unpack(
            open(os.path.join(base, "CompetitionEntry.bin"), "rb").read()
        )
    )
    teams = bytearray(
        pesdb.wesys_unpack(open(os.path.join(base, "Team.bin"), "rb").read())
    )

    reg_of = {}
    for i in range(0, len(regs), M.REG):
        reg_of[int.from_bytes(regs[i + M.R_ID : i + M.R_ID + 2], "little")] = regs[
            i + M.R_CID
        ]

    def entries_of(reg):
        cid = reg_of[reg]
        return [k for k in range(0, len(ents), M.ENT) if ents[k + M.E_CID] == cid]

    pool = []
    for reg in DELETE_REGS:
        pool += [int.from_bytes(ents[k : k + 4], "little") for k in entries_of(reg)]
    keep = entries_of(KEEP_REG)
    pool += [int.from_bytes(ents[k : k + 4], "little") for k in keep[:KEEP_TAKE]]
    need = sum(s[4] for s in SPEC)
    print("clubes disponibles %d, hacen falta %d" % (len(pool), need))
    if len(pool) < need:
        raise SystemExit("no hay clubes suficientes")

    if dry:
        for n, (name, flag, conf, tier, count, code) in enumerate(SPEC):
            print("  %-26s %-4d %-3d %-3d %s" % (name, flag, tier, count, code))
        print("dry run: nothing written")
        return 0

    # 1. quitar las entradas de los donantes
    drop = set()
    for reg in DELETE_REGS:
        drop.update(entries_of(reg))
    drop.update(keep[:KEEP_TAKE])
    ents = bytearray(
        b"".join(
            ents[k : k + M.ENT] for k in range(0, len(ents), M.ENT) if k not in drop
        )
    )
    # el donante que sobrevive: su regulacion cuenta los que quedan
    cid_keep = reg_of[KEEP_REG]
    left = sum(1 for k in range(0, len(ents), M.ENT) if ents[k + M.E_CID] == cid_keep)
    for i in range(0, len(regs), M.REG):
        if int.from_bytes(regs[i + M.R_ID : i + M.R_ID + 2], "little") == KEEP_REG:
            regs[i + M.R_TEAMS] = (regs[i + M.R_TEAMS] & 0xC0) | (left & 0x3F)
    print("Other Clubs (Asia): quedan %d" % left)

    # 2. borrar las cuatro ligas donantes
    gone = {reg_of[r] for r in DELETE_REGS}
    comp = bytearray(
        b"".join(
            comp[c : c + M.COMP]
            for c in range(0, len(comp), M.COMP)
            if comp[c + M.CID_OFF] not in gone
        )
    )
    regs = bytearray(
        b"".join(
            regs[r : r + M.REG]
            for r in range(0, len(regs), M.REG)
            if regs[r + M.R_CID] not in gone
        )
    )
    print("borradas %d ligas: %s" % (len(gone), sorted(gone)))

    # 3. crear las seis
    used = {comp[i + M.CID_OFF] for i in range(0, len(comp), M.COMP)}
    free_cids = [c for c in range(1, 256) if c not in used]
    if len(free_cids) < len(SPEC):
        raise SystemExit("solo quedan %d cids libres (1..255)" % len(free_cids))
    cids = free_cids[: len(SPEC)]
    print("cids libres que se usan: %s" % cids)
    reg = (
        max(
            int.from_bytes(regs[i + M.R_ID : i + M.R_ID + 2], "little")
            for i in range(0, len(regs), M.REG)
        )
        + 1
    )
    pos = 0
    made = []
    for (name, flag, conf, tier, count, code), cid in zip(SPEC, cids):
        ids = pool[pos : pos + count]
        pos += count
        for n, tid in enumerate(ids, 1):
            o = next(
                o
                for o in range(0, len(teams), T_REC)
                if int.from_bytes(teams[o + T_ID : o + T_ID + 4], "little") == tid
            )
            row = bytearray(teams[o : o + T_REC])
            put_team_name(row, "%s %02d" % (name, n))
            old = int.from_bytes(row[T_COUNTRY : T_COUNTRY + 2], "little")
            row[T_COUNTRY : T_COUNTRY + 2] = (
                (old & ~(0x1FF << 2)) | (flag << 2)
            ).to_bytes(2, "little")
            teams[o : o + T_REC] = row
        M.add_league(
            comp,
            regs,
            ents,
            cid,
            reg,
            REGION[flag],
            name,
            code,
            ids,
            tier=tier,
            quiet=True,
        )
        made.append((name, cid, reg, count, code, flag, tier))
        cid += 1
        reg += 1

    for name, c, r, count, code, flag, tier in made:
        print(
            "  %-26s cid %-4d reg %-4d %-3d equipos (pais %d, div %d)"
            % (name, c, r, count, flag, tier)
        )

    open(os.path.join(base, "Competition.bin"), "wb").write(
        pesdb.wesys_pack(bytes(comp))
    )
    open(os.path.join(base, "CompetitionRegulation.bin"), "wb").write(
        pesdb.wesys_pack(bytes(regs))
    )
    open(os.path.join(base, "CompetitionEntry.bin"), "wb").write(
        pesdb.wesys_pack(bytes(ents))
    )
    open(os.path.join(base, "Team.bin"), "wb").write(pesdb.wesys_pack(bytes(teams)))

    # 4. world file
    lines = [
        l
        for l in open(wf, encoding="utf-8", errors="replace").read().splitlines()
        if not any(l.startswith("league %d " % r) for r in DELETE_REGS)
    ]
    for name, c, r, count, code, flag, tier in made:
        lines.append(
            "league %d cid=%d region=%d country=%d conf=4 slot=-1 tier=%d promote=0 demote=0 "
            "clubs=%d legs=2 kickoff=99 name=%s"
            % (r, c, REGION[flag], flag, tier, count, name)
        )
    open(wf, "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
    print("world file: %d ligas" % sum(1 for l in lines if l.startswith("league ")))
    return 0


if __name__ == "__main__":
    sys.exit(main())

