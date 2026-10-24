"""python mk_oceania.py --base <world pesdb> --worldfile <fl26world.txt>
                       [--countries <pesdb with Country.bin>] [--cid 91] [--reg 196]

Make "Oceania" a **league** of the OFC national teams instead of a cup.

Why: the Select Team list only gets a team list for a slot whose competition is a league
(`CompetitionRegulation.bin` `type` 4, as every league of the world is); a cup (type 3) is
played from Kick Off > Cup and its slot stays empty, so a row named "Oceania" on a free slot
showed no group at all (2026-10-24, sider.log: the row went to slot 22 and nothing appeared).

This removes the cup competition/regulation this tool's sibling (`add_nations_cups.py
--preset oceania`) built, and adds it again through `mkleague.add_league`, which copies the
shape of a shipped league: 11 OFC national teams, one round (`legs=1`), the world line's
`clubs=11`. The slot is left at `-1` so `fl26comptab` picks one the exe leaves free.

It does not touch Team.bin or Player.bin: the teams already exist (the 211 of the world).
"""

import io
import sys
import os

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pesdb
import mkleague as M
import nations as N


def main():
    a = sys.argv[1:]
    get = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    base, wf = get("--base"), get("--worldfile")
    if not base or not wf:
        print(__doc__)
        return 1
    countries = get("--countries") or base
    cid = int(get("--cid", "91"))
    reg = int(get("--reg", "196"))

    nats = [e for e in N.read(base, countries) if e["conf"] == 7]
    nats.sort(key=lambda e: e["id"])
    if len(nats) < 11:
        print("only %d OFC national teams in this world" % len(nats))
        return 1
    teams = [e["id"] for e in nats]
    print("OFC national teams: %d" % len(teams))

    comp = M.load(base, "Competition.bin")
    regs = M.load(base, "CompetitionRegulation.bin")
    ents = M.load(base, "CompetitionEntry.bin")

    # 1. out with the cup: its competition row, its regulation and its entries
    comp = b"".join(
        comp[i : i + M.COMP]
        for i in range(0, len(comp), M.COMP)
        if comp[i + M.CID_OFF] != cid
    )
    regs = b"".join(
        regs[i : i + M.REG]
        for i in range(0, len(regs), M.REG)
        if int.from_bytes(regs[i + M.R_ID : i + M.R_ID + 2], "little") != reg
    )
    ents = b"".join(
        ents[i : i + M.ENT]
        for i in range(0, len(ents), M.ENT)
        if ents[i + M.E_CID] != cid
    )
    comp, regs, ents = bytearray(comp), bytearray(regs), bytearray(ents)

    # 2. in again as a league, the shape every other league of the world has
    M.add_league(
        comp,
        regs,
        ents,
        cid,
        reg,
        M.enc_region(25),
        "Oceania",
        "FL_OCEA",
        teams,
        tier=1,
    )
    print("Oceania: cid %d, regulation %d, %d teams" % (cid, reg, len(teams)))

    open(os.path.join(base, "Competition.bin"), "wb").write(
        pesdb.wesys_pack(bytes(comp))
    )
    open(os.path.join(base, "CompetitionRegulation.bin"), "wb").write(
        pesdb.wesys_pack(bytes(regs))
    )
    open(os.path.join(base, "CompetitionEntry.bin"), "wb").write(
        pesdb.wesys_pack(bytes(ents))
    )

    # 3. the world file: a league line, the cup line goes
    lines = io.open(wf, encoding="utf-8", errors="replace").read().splitlines()
    out = [l for l in lines if not l.startswith("ccup %d " % reg)]
    new = (
        "league %d cid=%d region=25 country=200 conf=7 slot=-1 tier=1 promote=0 demote=0 "
        "clubs=%d legs=1 kickoff=166 name=Oceania" % (reg, cid, len(teams))
    )
    for i, l in enumerate(out):
        if l.startswith("league %d " % reg):
            out[i] = new
            break
    else:
        out.append(new)
    io.open(wf, "w", encoding="utf-8", newline="\n").write("\n".join(out) + "\n")
    print("world file: %s" % new)
    return 0


if __name__ == "__main__":
    sys.exit(main())
