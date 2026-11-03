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
    {
        "cid": 243,
        "reg": 8461,
        "region": 110,
        "slot": 238,
        "country": 55,
        "conf": 5,
        "name": "Linafoot",
        "code": "FL_55_D1",
        "kickoff": 70,
        "clubs": [
            "TP Mazembe",
            "AS Vita Club",
            "FC Saint-Eloi Lupopo",
            "CS Don Bosco",
            "AS Dauphins Noirs",
            "JS Groupe Bazano",
            "OC Bukavu Dawa",
            "SM Sanga Balende",
            "AC Rangers",
            "US Tshinkunku",
        ],
    },
    {
        "cid": 244,
        "reg": 8462,
        "region": 111,
        "slot": 239,
        "country": 98,
        "conf": 5,
        "name": "Congo Ligue 1",
        "code": "FL_98_D1",
        "kickoff": 70,
        "clubs": [
            "AS Otoho",
            "Etoile du Congo",
            "Diables Noirs",
            "CARA Brazzaville",
            "AC Leopards",
            "JS Talangai",
            "AS Kondzo",
            "FC Nathaly's",
            "Inter Brazzaville",
            "AS Cheminots",
        ],
    },
    {
        "cid": 245,
        "reg": 8463,
        "region": 112,
        "slot": 240,
        "country": 164,
        "conf": 7,
        "name": "Fiji Premier League",
        "code": "FL_164_D1",
        "kickoff": 70,
        "clubs": [
            "Rewa FC",
            "Ba FC",
            "Suva FC",
            "Lautoka FC",
            "Nadi FC",
            "Labasa FC",
            "Nadroga FC",
            "Navua FC",
            "Nasinu FC",
            "Tailevu Naitasiri",
        ],
    },
    {
        "cid": 246,
        "reg": 8464,
        "region": 113,
        "slot": 241,
        "country": 110,
        "conf": 6,
        "name": "Canadian Premier League",
        "code": "FL_110_D1",
        "kickoff": 17,
        "clubs": [
            "Forge FC",
            "Cavalry FC",
            "York United FC",
            "Atletico Ottawa",
            "Pacific FC",
            "HFX Wanderers",
            "Valour FC",
            "Vancouver FC",
        ],
    },
    {
        "cid": 247,
        "reg": 8465,
        "region": 80,
        "slot": 242,
        "country": 124,
        "conf": 6,
        "name": "Liga de Expansion MX",
        "code": "FL_124_D2",
        "kickoff": 17,
        "tier": 2,
        "clubs": [
            "Leones Negros",
            "Atlante FC",
            "Tapatio",
            "Mineros de Zacatecas",
            "Correcaminos UAT",
            "Venados FC",
            "Dorados de Sinaloa",
            "Cancun FC",
            "Tlaxcala FC",
            "Alebrijes de Oaxaca",
        ],
    },
    {
        "cid": 248,
        "reg": 8466,
        "region": 114,
        "slot": 243,
        "country": 113,
        "conf": 6,
        "name": "Liga Cubana",
        "code": "FL_113_D1",
        "kickoff": 17,
        "clubs": [
            "Villa Clara",
            "Cienfuegos",
            "Santiago de Cuba",
            "La Habana",
            "Pinar del Rio",
            "Camaguey",
            "Las Tunas",
            "Holguin",
            "Granma",
            "Matanzas",
        ],
    },
    {
        "cid": 249,
        "reg": 8467,
        "region": 24,
        "slot": 244,
        "country": 13,
        "conf": 3,
        "name": "J2 League",
        "code": "FL_13_D2",
        "kickoff": 18,
        "tier": 2,
        "clubs": [
            "Ventforet Kofu",
            "Montedio Yamagata",
            "Oita Trinita",
            "Tokushima Vortis",
            "Renofa Yamaguchi",
            "Roasso Kumamoto",
            "Kagoshima United",
            "Blaublitz Akita",
            "Iwate Grulla Morioka",
            "Thespa Gunma",
            "Tochigi SC",
            "Zweigen Kanazawa",
            "Ehime FC",
            "Fujieda MYFC",
            "Iwaki FC",
            "Kataller Toyama",
        ],
    },
]

# Leagues that already exist but are full of placeholders: their clubs are renamed and the
# surplus entries go, so the competition keeps its cid, region and slot. "countries" gives one
# flag per club for a bucket that mixes countries, and no "name" leaves the shipped name alone.
FILLS = [
    {
        "cid": 168,
        "reg": 198,
        "country": 165,
        "name": "Super Ligue",
        "clubs": [
            "AS Magenta",
            "Hienghène Sport",
            "AS Tiga Sport",
            "AS Lössi",
            "SC Ne Drehu",
            "Horizon Patho",
            "AS Mont-Dore",
            "CA Saint-Louis",
            "ES Wé Luécilla",
            "AS Wetr",
            "US Cagou",
            "JS Baco",
        ],
    },
    {
        "cid": 221,
        "reg": 250,
        "clubs": [
            "Defence Force FC",
            "Central FC",
            "W Connection",
            "San Juan Jabloteh",
            "Police FC TT",
            "Morvant Caledonia United",
            "Point Fortin Civic",
            "Club Sando",
            "Cunupia FC",
            "La Horquetta Rangers",
            "Bayamon FC",
            "Metropolitan FA",
            "Academia Quintana",
            "Puerto Rico Sol",
            "Dandy Town Hornets",
            "PHC Zebras",
            "Devonshire Cougars",
            "Robin Hood FC",
            "Somerset Trojans",
            "Fruta Conquerors",
            "Guyana Defence Force",
            "Alpha United",
            "Western Tigers",
            "Buxton United",
            "Weymouth Wales",
            "Paradise FC",
            "Brittons Hill",
            "UWI Blackbirds",
            "Liberta Blackhawks",
            "Parham FC",
            "SAP FC",
            "Hoppers FC",
            "Hard Rock FC",
            "St Johns Sports",
            "Fontenoy United",
            "Village Superstars",
            "Newtown United",
            "Cayon FC",
            "Dakota Aruba",
            "RCA Aruba",
            "Britannia FC",
            "Bears FC",
            "Western Warriors",
            "System 3 FC",
            "Avenues United",
            "Hope International",
            "Dublanc FC",
            "Sagicor South East",
        ],
        # Trinidad y Tobago, Puerto Rico, Bermudas, Guyana, Barbados, Antigua, Granada,
        # San Cristobal y Nieves, Aruba, Bahamas, San Vicente, Dominica
        "countries": [133] * 10
        + [129] * 4
        + [109] * 5
        + [159] * 5
        + [107] * 4
        + [104] * 4
        + [117] * 3
        + [130] * 3
        + [105] * 3
        + [106] * 2
        + [132] * 3
        + [114] * 2,
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
            tier=spec.get("tier", 1),
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

    # --- leagues that exist but are full of placeholders
    for spec in FILLS:
        rows_in = sorted(
            (
                (ents[k + M.E_ORDER], k)
                for k in range(0, len(ents), M.ENT)
                if ents[k + M.E_CID] == spec["cid"]
            )
        )
        if not rows_in:
            raise SystemExit("competition %d has no entries" % spec["cid"])
        first = int.from_bytes(ents[rows_in[0][1] : rows_in[0][1] + 4], "little")
        if name(off()[first]) == spec["clubs"][0]:
            print("%s: ya tiene sus clubes" % spec.get("name", "liga"))
            continue
        if len(rows_in) < len(spec["clubs"]):
            raise SystemExit(
                "competition %d has %d entries, not %d"
                % (spec["cid"], len(rows_in), len(spec["clubs"]))
            )
        off3 = off()
        flags = spec.get("countries") or [spec.get("country")] * len(spec["clubs"])
        for (_, k), club, flag in zip(rows_in, spec["clubs"], flags):
            tid = int.from_bytes(ents[k : k + 4], "little")
            o = off3[tid]
            row = bytearray(teams[o : o + T_REC])
            put_team_name(row, club)
            if flag is not None:
                set_country(row, flag)
            teams[o : o + T_REC] = row
        # the entries the league no longer uses go; the rest keep their order
        keep_teams = {
            int.from_bytes(ents[k : k + 4], "little")
            for _, k in rows_in[: len(spec["clubs"])]
        }
        keep = bytearray()
        for k in range(0, len(ents), M.ENT):
            tid = int.from_bytes(ents[k : k + 4], "little")
            if ents[k + M.E_CID] == spec["cid"] and tid not in keep_teams:
                continue
            keep += ents[k : k + M.ENT]
        ents = keep
        order = sorted(
            (
                (int.from_bytes(ents[k + 4 : k + 8], "little"), k)
                for k in range(0, len(ents), M.ENT)
                if ents[k + M.E_CID] == spec["cid"]
            )
        )
        for i, (_, k) in enumerate(order, 1):
            ents[k + M.E_ORDER] = i
        n_fill = len(order)
        for i in range(0, len(regs), M.REG):
            if regs[i + M.R_CID] == spec["cid"]:
                regs[i + M.R_TEAMS] = (regs[i + M.R_TEAMS] & 0xC0) | (n_fill & 0x3F)
                if spec.get("name"):
                    M.put_names(regs, i, spec["name"])
                break
        if spec.get("name"):
            for i in range(0, len(comp), M.COMP):
                if comp[i + M.CID_OFF] == spec["cid"]:
                    M.put(comp, i + 0x14, spec["name"], 16)
                    break
        print(
            "%s: cid %d, %d clubes (de %d filas)"
            % (spec.get("name", "liga"), spec["cid"], n_fill, len(rows_in))
        )

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
    fill_cid = {s["cid"]: s for s in FILLS}
    out, last = [], 0
    for line in lines:
        w = line.split()
        if w and w[0] == "league":
            last = len(out)
            kv = dict(p.split("=", 1) for p in w[2:] if "=" in p)
            if w[1].isdigit() and int(w[1]) == lat_reg:
                line = " ".join(
                    "clubs=%d" % n_lat if p.startswith("clubs=") else p for p in w
                )
            elif "cid" in kv and int(kv["cid"]) in fill_cid:
                spec = fill_cid[int(kv["cid"])]
                n = sum(
                    1
                    for k in range(0, len(ents), M.ENT)
                    if ents[k + M.E_CID] == spec["cid"]
                )
                if spec.get("name"):
                    cut = next(
                        (i for i, p in enumerate(w) if p.startswith("name=")), len(w)
                    )
                    w = [p for p in w[:cut] if not p.startswith("clubs=")]
                    line = " ".join(w + ["clubs=%d" % n, "name=%s" % spec["name"]])
                else:
                    line = " ".join(
                        "clubs=%d" % n if p.startswith("clubs=") else p for p in w
                    )
        out.append(line)
    for spec in pending:
        last += 1
        out.insert(
            last,
            "league %d cid=%d region=%d country=%d conf=%d slot=%d tier=%d promote=0 "
            "demote=0 clubs=%d legs=2 kickoff=%d name=%s"
            % (
                spec["reg"],
                spec["cid"],
                spec["region"],
                spec["country"],
                spec["conf"],
                spec["slot"],
                spec.get("tier", 1),
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
