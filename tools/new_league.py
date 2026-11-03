"""python new_league.py --base <pesdb> --worldfile <fl26world.txt> [--dry]

Leagues built from scratch, one entry per country: the generic leagues ran out, so each of these
gets a new cid, a new competition row and a new regulation (mkleague.add_league copies one of our
own leagues as the prototype) and ten clubs taken from rows no competition owns any more. A spec
whose cid is already in Competition.bin is skipped, so the tool can be run again.

The first run also took the eight South American copies out of "Other Latin American Teams"
(cid 95): they are clubs that already play in their own league, so the row, its entry and its 22
assignments went, and the group went from 48 to 40.
"""

import io
import os
import re
import sys
import unicodedata

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
    74206: "Técnico Universitario",
    74208: "Guayaquil City",
    74220: "Montevideo City Torque",
}

LEAGUES = [
    {
        "cid": 239,
        "reg": 8457,
        "region": 106,
        "slot": 234,
        "country": 108,
        "conf": 6,
        "name": "Belize Premier League",
        "code": "FL_108_D1",
        "kickoff": 17,
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
    },
    {
        "cid": 240,
        "reg": 8458,
        "region": 107,
        "slot": 235,
        "country": 140,
        "conf": 6,
        "name": "Curacao Prome Divishon",
        "code": "FL_140_D1",
        "kickoff": 17,
        "clubs": [
            "CRKSV Jong Colombia",
            "RKSV Centro Dominguito",
            "SV Victory Boys",
            "CRKSV Jong Holland",
            "CSD Barber",
            "RKVFC Sithoc",
            "SV Hubentut Fortuna",
            "UNDEBA",
            "RKSV Scherpenheuvel",
            "SV Vesta",
        ],
    },
    {
        "cid": 241,
        "reg": 8459,
        "region": 108,
        "slot": 236,
        "country": 139,
        "conf": 6,
        "name": "Suriname Major League",
        "code": "FL_139_D1",
        "kickoff": 17,
        "clubs": [
            "SV Robinhood",
            "Inter Moengotapoe",
            "SV Transvaal",
            "SV Notch",
            "Walking Boyz Company",
            "SV Leo Victor",
            "SV Voorwaarts",
            "PVV",
            "SV Broki",
            "SV Flora",
        ],
    },
    {
        "cid": 242,
        "reg": 8460,
        "region": 109,
        "slot": 237,
        "country": 120,
        "conf": 6,
        "name": "Ligue Haitienne",
        "code": "FL_120_D1",
        "kickoff": 17,
        "clubs": [
            "Violette AC",
            "Don Bosco FC",
            "Tempete FC",
            "AS Mirebalais",
            "Racing Club Haitien",
            "AS Capoise",
            "Baltimore SC",
            "America des Cayes",
            "Cavaly AS",
            "FICA",
        ],
    },
]


def norm(s):
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

    # --- out: the South American copies (skipped when they are already gone)
    before = off()
    here = [t for t in DROPS if t in before]
    for tid in here:
        if any(
            int.from_bytes(ents[k : k + 4], "little") == tid
            and ents[k + M.E_CID] != OTHER_LAT
            for k in range(0, len(ents), M.ENT)
        ):
            raise SystemExit(
                "%s is also in another competition; not dropping it" % DROPS[tid]
            )
    if here:
        for tid in sorted(here, key=lambda t: before[t], reverse=True):
            o = before[tid]
            del teams[o : o + T_REC]
        keep = bytearray()
        for k in range(0, len(ents), M.ENT):
            if int.from_bytes(ents[k : k + 4], "little") not in here:
                keep += ents[k : k + M.ENT]
        ents = keep
        n_assign = len(assign) // 16
        keep = bytearray()
        for k in range(0, len(assign), 16):
            if int.from_bytes(assign[k + 8 : k + 12], "little") not in here:
                keep += assign[k : k + 16]
        assign = keep
        print(
            "fuera %d copias sudamericanas y sus %d fichas"
            % (len(here), n_assign - len(assign) // 16)
        )

    # --- "Other Latin American Teams": order and count follow whatever is left
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

    # --- the leagues that are still missing
    taken_cids = {comp[i + M.CID_OFF] for i in range(0, len(comp), M.COMP)}
    pending = [s for s in LEAGUES if s["cid"] not in taken_cids]
    taken_rows = {
        int.from_bytes(ents[k : k + 4], "little") for k in range(0, len(ents), M.ENT)
    }
    rows = lambda: [
        tid
        for tid, o in sorted(off().items())
        if tid not in taken_rows and re.search(r"Club \d+$", name(o))
    ]
    pool = rows()
    world_names = {norm(name(o)) for o in off().values()}
    for spec in pending:
        if spec["cid"] in taken_cids:
            raise SystemExit("competition id %d is taken" % spec["cid"])
        if spec.get("rows"):
            use = spec["rows"]
            for tid in use:
                if tid in taken_rows:
                    raise SystemExit("team %d still has a competition entry" % tid)
        else:
            use = pool[: len(spec["clubs"])]
            pool = pool[len(use) :]
        for club in spec["clubs"]:
            if norm(club) in world_names:
                raise SystemExit("club name already in the world: %r" % club)
            world_names.add(norm(club))

        off2 = off()
        for tid, club in zip(use, spec["clubs"]):
            o = off2[tid]
            row = bytearray(teams[o : o + T_REC])
            put_team_name(row, club)
            set_country(row, spec["country"])
            teams[o : o + T_REC] = row

        cid, rid = M.add_league(
            comp,
            regs,
            ents,
            spec["cid"],
            spec["reg"],
            M.enc_region(spec["region"]),
            spec["name"],
            spec["code"],
            use,
            proto_code="FL_223_D1",
            tier=1,
        )
        # add_league writes a 28-byte code, which also clears the 16-byte name at +0x14
        M.put(comp, (len(comp) // M.COMP - 1) * M.COMP + 0x14, spec["name"], 16)
        taken_cids.add(cid)
        taken_rows |= set(use)
        print(
            "%s: cid %d reg %d region %d slot %d, %d clubes (%d..%d)"
            % (
                spec["name"],
                cid,
                rid,
                spec["region"],
                spec["slot"],
                len(use),
                use[0],
                use[-1],
            )
        )

    if not pending:
        print("no queda ninguna liga por crear")

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

    # --- the world file: the new lines, and the group's count
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
    for spec in pending:
        last += 1
        out.insert(
            last,
            "league %d cid=%d region=%d country=%d conf=%d slot=%d tier=1 promote=0 "
            "demote=0 clubs=%d legs=2 kickoff=%d name=%s"
            % (
                spec["reg"],
                spec["cid"],
                spec["region"],
                spec["country"],
                spec["conf"],
                spec["slot"],
                len(spec["clubs"]),
                spec["kickoff"],
                spec["name"],
            ),
        )
    io.open(wf, "w", encoding="utf-8", newline="\n").write("\n".join(out) + "\n")
    print("world: %d lineas" % len(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
