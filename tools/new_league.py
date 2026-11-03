"""python new_league.py --base <pesdb> --worldfile <fl26world.txt> [--dry]

The generic leagues ran out, so Belize is the first league built from scratch: a new cid, a new
competition row and a new regulation (mkleague.add_league), ten clubs taken from rows that no
competition owns any more. The same run takes the eight South American copies out of "Other
Latin American Teams" (cid 95): they are the same clubs that already play in their own leagues
(Ecuador, Peru, Uruguay, Bolivia, Venezuela), so the row, its entry and its 22 assignments go.
"""

import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pesdb
import mkleague as M
from make_country_leagues import put_team_name, set_country

T_REC, T_ID = 1532, 0x08
OTHER_LAT = 95

# the copies inside "Other Latin American Teams", by team id
DROPS = {
    74187: "Los Chankas",
    74191: "Real Potosí",
    74197: "Universitario de Vinto",
    74203: "Zamora FC",
    74205: "Mushuc Runa",
    74206: "Tecnico Universitario",
    74208: "Guayaquil City",
    74220: "Montevideo City Torque",
}

# rows with no competition of their own ("Generic League 18 Club 01".."10")
BELIZE = {
    "cid": 239,
    "reg": 8457,
    "region": 106,
    "slot": 234,
    "country": 108,
    "conf": 6,
    "name": "Belize Premier League",
    "code": "FL_108_D1",
    "clubs": [
        "Verdes FC",
        "Belmopan Bandits",
        "San Pedro Pirates",
        "Wagiya SC",
        "Garden City FC",
        "Altitude FC",
        "Police United",
        "Griga United",
        "Freedom Fighters",
        "Benque Viejo FC",
    ],
    "rows": [73265, 73266, 73267, 73268, 73269, 73270, 73271, 73272, 73273, 73274],
}


def norm(s):
    import unicodedata

    s = unicodedata.normalize("NFD", s)
    return re.sub(
        r"[^a-z0-9]",
        "",
        "".join(c for c in s if unicodedata.category(c) != "Mn").lower(),
    )


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    a = sys.argv[1:]
    get = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    base, wf = get("--base"), get("--worldfile")
    if not base or not wf:
        print(__doc__)
        return 2
    dry = "--dry" in a

    teams = bytearray(
        pesdb.wesys_unpack(open(os.path.join(base, "Team.bin"), "rb").read())
    )
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
    assign = bytearray(
        pesdb.wesys_unpack(
            open(os.path.join(base, "PlayerAssignment.bin"), "rb").read()
        )
    )

    off = lambda: {
        int.from_bytes(teams[o + T_ID : o + T_ID + 4], "little"): o
        for o in range(0, len(teams), T_REC)
    }
    name = lambda o: pesdb.cstr(teams[o + 0x170 : o + 0x170 + 70]).strip()

    # --- checks before touching anything
    before = off()
    for tid, want in DROPS.items():
        if tid not in before:
            raise SystemExit("team %d (%s) is not in Team.bin" % (tid, want))
        if norm(name(before[tid])) != norm(want):
            raise SystemExit("team %d is %r, not %r" % (tid, name(before[tid]), want))
        if any(
            int.from_bytes(ents[k : k + 4], "little") == tid
            and ents[k + M.E_CID] != OTHER_LAT
            for k in range(0, len(ents), M.ENT)
        ):
            raise SystemExit(
                "%s is also entered in another competition; not dropping it" % want
            )
    taken = {
        int.from_bytes(ents[k : k + 4], "little") for k in range(0, len(ents), M.ENT)
    }
    for tid in BELIZE["rows"]:
        if tid in taken:
            raise SystemExit("team %d still has a competition entry" % tid)
        if tid not in before:
            raise SystemExit("team %d is not in Team.bin" % tid)
    world = {norm(name(o)) for o in before.values()}
    for c in BELIZE["clubs"]:
        if norm(c) in world:
            raise SystemExit("club name already in the world: %r" % c)

    # --- out: the South American copies
    for tid in sorted(DROPS, key=lambda t: before[t], reverse=True):
        o = before[tid]
        del teams[o : o + T_REC]
    keep = bytearray()
    for k in range(0, len(ents), M.ENT):
        if int.from_bytes(ents[k : k + 4], "little") not in DROPS:
            keep += ents[k : k + M.ENT]
    ents = keep
    n_assign = len(assign) // 16
    keep = bytearray()
    for k in range(0, len(assign), 16):
        if int.from_bytes(assign[k + 8 : k + 12], "little") not in DROPS:
            keep += assign[k : k + 16]
    assign = keep
    print(
        "fuera %d copias sudamericanas y sus %d fichas"
        % (len(DROPS), n_assign - len(assign) // 16)
    )

    # --- the group they leave keeps its order and its count
    order = sorted(
        (
            (int.from_bytes(ents[k + 4 : k + 8], "little"), k)
            for k in range(0, len(ents), M.ENT)
            if ents[k + M.E_CID] == OTHER_LAT
        )
    )
    for i, (_, k) in enumerate(order, 1):
        ents[k + M.E_ORDER] = i
    n_lat = len(order)
    for i in range(0, len(regs), M.REG):
        if regs[i + M.R_CID] == OTHER_LAT:
            regs[i + M.R_TEAMS] = (regs[i + M.R_TEAMS] & 0xC0) | (n_lat & 0x3F)
            break
    print("Other Latin American: %d clubes" % n_lat)

    # --- Belize: ten free rows become its clubs
    off2 = off()
    for tid, club in zip(BELIZE["rows"], BELIZE["clubs"]):
        o = off2[tid]
        row = bytearray(teams[o : o + T_REC])
        put_team_name(row, club)
        set_country(row, BELIZE["country"])
        teams[o : o + T_REC] = row
    print(
        "Belice: %d clubes en filas sueltas (%d..%d)"
        % (len(BELIZE["clubs"]), BELIZE["rows"][0], BELIZE["rows"][-1])
    )

    # --- the competition itself
    cid, rid = M.add_league(
        comp,
        regs,
        ents,
        BELIZE["cid"],
        BELIZE["reg"],
        M.enc_region(BELIZE["region"]),
        BELIZE["name"],
        BELIZE["code"],
        BELIZE["rows"],
        proto_code="FL_223_D1",
        tier=1,
    )
    # add_league writes a 28-byte code, which also clears the 16-byte name at +0x14
    M.put(comp, (len(comp) // M.COMP - 1) * M.COMP + 0x14, BELIZE["name"], 16)

    if dry:
        print("dry run: nothing written")
        return 0

    for n, b in (
        ("Team.bin", teams),
        ("Competition.bin", comp),
        ("CompetitionRegulation.bin", regs),
        ("CompetitionEntry.bin", ents),
        ("PlayerAssignment.bin", assign),
    ):
        open(os.path.join(base, n), "wb").write(pesdb.wesys_pack(bytes(b)))
        print("  wrote %s" % n)

    # --- the world file: one new league, and the group's new count
    lat_reg = next(
        int.from_bytes(regs[i + M.R_ID : i + M.R_ID + 2], "little")
        for i in range(0, len(regs), M.REG)
        if regs[i + M.R_CID] == OTHER_LAT
    )
    lines = io.open(wf, encoding="utf-8", errors="replace").read().splitlines()
    out, last = [], 0
    for line in lines:
        w = line.split()
        if w and w[0] == "league":
            last = len(out)
            if w[1].isdigit() and int(w[1]) == lat_reg:
                line = " ".join(
                    "clubs=%d" % n_lat if p.startswith("clubs=") else p for p in w
                )
        out.append(line)
    out.insert(
        last + 1,
        "league %d cid=%d region=%d country=%d conf=%d slot=%d tier=1 promote=0 "
        "demote=0 clubs=%d legs=2 kickoff=17 name=%s"
        % (
            rid,
            cid,
            BELIZE["region"],
            BELIZE["country"],
            BELIZE["conf"],
            BELIZE["slot"],
            len(BELIZE["rows"]),
            BELIZE["name"],
        ),
    )
    io.open(wf, "w", encoding="utf-8", newline="\n").write("\n".join(out) + "\n")
    print("world: %d lineas" % len(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
