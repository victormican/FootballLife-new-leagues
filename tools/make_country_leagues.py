"""python make_country_leagues.py --base <pesdb> --worldfile <fl26world.txt> [--dry]

Turns five of our generic leagues into real first divisions -- Azerbaijan, Ireland, Wales,
Iceland and Hungary -- and gives the clubs that already were in "Other European Leagues"
a league of their own.

How it works (2026-11-03)
  * a generic league already has a competition id, a regulation, a slot and ten clubs, so
    nothing is created: the league line, the regulation name and the ten club rows change;
  * the clubs of the new country that sat in "Other European Leagues" (cid 98) move into the
    new competition, and the same number of donor clubs move the other way, renamed to real
    clubs of countries still without a league, so that group stays 48;
  * every renamed club gets its country's flag id at Team.bin +0x46;
  * the two empty "Generic League 66/67" twins are dropped (they shared cid 50/51).

Also renames the 48 clubs of "Other Latin American Teams" (cid 95) to real South American
clubs with their own flags, when --latin is given.
"""

import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pesdb
import mkleague as M

T_REC, T_ID, T_COUNTRY, T_NATIONAL = 1532, 0x08, 0x46, 0x53
T_NAME, T_NAME_LEN, T_NAME_SLOTS, T_NAME_STEP = 0x9E, 70, 20, 70
T_ABBR, T_SHORT = 0x372, 0x35A
T_LONG, T_LONG_LEN = 0x37C, 22
OTHER_EU = 98

SPEC = [
    {
        "reg": 339,
        "cid": 50,
        "country": 195,
        "name": "Azerbaijan Premier League",
        "moved": [4326],
        "rename": {4326: "Qarabağ FK"},
        "clubs": [
            "Neftçi Baku",
            "Sabah FK",
            "Zira FK",
            "Sumqayit",
            "Gabala FK",
            "Sabail FK",
            "Turan Tovuz",
            "Kapaz PFK",
            "Araz-Naxçıvan",
        ],
    },
    {
        "reg": 340,
        "cid": 51,
        "country": 214,
        "name": "League of Ireland Premier Division",
        "moved": [71668, 71669, 71670],
        "rename": {},
        "clubs": [
            "Shelbourne",
            "Derry City",
            "Bohemians",
            "Sligo Rovers",
            "Cork City",
            "Waterford FC",
            "Drogheda United",
        ],
    },
    {
        "reg": 341,
        "cid": 52,
        "country": 241,
        "name": "Cymru Premier",
        "moved": [71667],
        "rename": {},
        "clubs": [
            "Connah's Quay Nomads",
            "Bala Town",
            "Newtown AFC",
            "Cardiff Metropolitan",
            "Barry Town United",
            "Penybont",
            "Haverfordwest County",
            "Caernarfon Town",
            "Aberystwyth Town",
        ],
    },
    {
        "reg": 342,
        "cid": 53,
        "country": 213,
        "name": "Besta deild karla",
        "moved": [72913],
        "rename": {72913: "Víkingur Reykjavík"},
        "clubs": [
            "Breiðablik",
            "Valur",
            "KR Reykjavík",
            "FH Hafnarfjörður",
            "KA Akureyri",
            "Stjarnan",
            "ÍA Akranes",
            "HK Kópavogur",
            "Fram Reykjavík",
        ],
    },
    {
        "reg": 343,
        "cid": 54,
        "country": 212,
        "name": "Nemzeti Bajnokság I",
        "moved": [2375, 71677, 71678, 71679],
        "rename": {
            2375: "Ferencvárosi TC",
            71677: "MOL Fehérvár FC",
            71678: "Újpest FC",
            71679: "Debreceni VSC",
        },
        "clubs": [
            "Puskás Akadémia",
            "Zalaegerszegi TE",
            "Kecskeméti TE",
            "Paksi FC",
            "MTK Budapest",
            "Diósgyőri VTK",
        ],
    },
]

# real clubs of countries that still have no league of their own, to keep Other European at 48
REFILL = [
    ("BATE Borisov", "BIELORRUSIA"),
    ("Dinamo Minsk", "BIELORRUSIA"),
    ("Shakhtyor Soligorsk", "BIELORRUSIA"),
    ("Kairat Almaty", "KAZAJISTÁN"),
    ("FC Astana", "KAZAJISTÁN"),
    ("FC Ballkani", "Kosovo"),
    ("KF Prishtina", "Kosovo"),
    ("Dinamo Batumi", "Georgia"),
    ("Torpedo Kutaisi", "Georgia"),
    ("Pyunik Yerevan", "Armenia"),
]

# real South American clubs for "Other Latin American Teams": second-rank clubs, so that the
# famous ones stay in their own league; the ones already in the world are skipped by name
LATIN = [
    ("Deportivo Llacuabamba", "PERÚ"),
    ("Sport Chavelines", "PERÚ"),
    ("Atlético Grau", "PERÚ"),
    ("Alianza Universidad", "PERÚ"),
    ("Pirata FC", "PERÚ"),
    ("Juan Aurich", "PERÚ"),
    ("Comerciantes Unidos", "PERÚ"),
    ("Los Chankas", "PERÚ"),
    ("Deportivo Coopsol", "PERÚ"),
    ("Santos FC Nazca", "PERÚ"),
    ("Universitario de Sucre", "BOLIVIA"),
    ("Real Potosí", "BOLIVIA"),
    ("Destroyers", "BOLIVIA"),
    ("Petrolero Yacuiba", "BOLIVIA"),
    ("Aurora", "BOLIVIA"),
    ("Ciclón", "BOLIVIA"),
    ("Vaca Díez", "BOLIVIA"),
    ("Universitario de Vinto", "BOLIVIA"),
    ("ULA FC", "VENEZUELA"),
    ("Trujillanos FC", "VENEZUELA"),
    ("Zulia FC", "VENEZUELA"),
    ("Lala FC", "VENEZUELA"),
    ("Gran Valencia", "VENEZUELA"),
    ("Hermanos Colmenárez", "VENEZUELA"),
    ("Zamora FC", "VENEZUELA"),
    ("Carabobo FC", "VENEZUELA"),
    ("Mushuc Runa", "ECUADOR"),
    ("Técnico Universitario", "ECUADOR"),
    ("Orense SC", "ECUADOR"),
    ("Guayaquil City", "ECUADOR"),
    ("Cumbayá FC", "ECUADOR"),
    ("9 de Octubre", "ECUADOR"),
    ("Sportivo Ameliano", "PARAGUAY"),
    ("General Caballero", "PARAGUAY"),
    ("Resistencia SC", "PARAGUAY"),
    ("Tacuary", "PARAGUAY"),
    ("12 de Octubre", "PARAGUAY"),
    ("Deportivo Recoleta", "PARAGUAY"),
    ("Atlético Tembetary", "PARAGUAY"),
    ("Sportivo San Lorenzo", "PARAGUAY"),
    ("River Plate Montevideo", "URUGUAY"),
    ("Montevideo City Torque", "URUGUAY"),
    ("CA Progreso", "URUGUAY"),
    ("CA Fénix", "URUGUAY"),
    ("Deportivo Maldonado", "URUGUAY"),
    ("La Luz FC", "URUGUAY"),
    ("Racing Montevideo", "URUGUAY"),
    ("Rampla Juniors", "URUGUAY"),
    ("Águilas Doradas", "COLOMBIA"),
    ("La Equidad", "COLOMBIA"),
    ("Jaguares de Córdoba", "COLOMBIA"),
    ("Alianza Petrolera", "COLOMBIA"),
    ("Envigado FC", "COLOMBIA"),
    ("Patriotas Boyacá", "COLOMBIA"),
    ("Boyacá Chicó", "COLOMBIA"),
    ("Unión Magdalena", "COLOMBIA"),
    ("Ñublense", "CHILE"),
    ("Unión Española", "CHILE"),
    ("Deportes Copiapó", "CHILE"),
    ("CD O'Higgins", "CHILE"),
    ("Curicó Unido", "CHILE"),
    ("Magallanes", "CHILE"),
    ("Santiago Wanderers", "CHILE"),
    ("Deportes Iquique", "CHILE"),
    ("Argentinos Juniors", "ARGENTINA"),
    ("Defensa y Justicia", "ARGENTINA"),
    ("Banfield", "ARGENTINA"),
    ("Godoy Cruz", "ARGENTINA"),
    ("Rosario Central", "ARGENTINA"),
    ("Central Córdoba", "ARGENTINA"),
    ("Barracas Central", "ARGENTINA"),
    ("Platense", "ARGENTINA"),
]


def core(name):
    """the longest word of a name, to notice a club that is already in the world under a
    longer name ("Emelec" vs "Club Sport Emelec")"""
    import unicodedata

    words = [
        w
        for w in "".join(
            c
            for c in unicodedata.normalize("NFD", name.lower())
            if unicodedata.category(c) != "Mn"
        )
        .replace("-", " ")
        .split()
        if len(w) >= 4
    ]
    return max(words, key=len) if words else ""


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


def set_country(row, fid):
    v = int.from_bytes(row[T_COUNTRY : T_COUNTRY + 2], "little")
    v = (v & 0x3) | (fid << 2)
    row[T_COUNTRY : T_COUNTRY + 2] = v.to_bytes(2, "little")


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    a = sys.argv[1:]
    get = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    base, wf = get("--base"), get("--worldfile")
    if not base or not wf:
        print(__doc__)
        return 2
    dry = "--dry" in a
    latin = "--latin" in a

    teams = bytearray(
        pesdb.wesys_unpack(open(os.path.join(base, "Team.bin"), "rb").read())
    )
    ents = bytearray(
        pesdb.wesys_unpack(
            open(os.path.join(base, "CompetitionEntry.bin"), "rb").read()
        )
    )
    regs = bytearray(
        pesdb.wesys_unpack(
            open(os.path.join(base, "CompetitionRegulation.bin"), "rb").read()
        )
    )
    comp = bytearray(
        pesdb.wesys_unpack(open(os.path.join(base, "Competition.bin"), "rb").read())
    )
    cty = pesdb.wesys_unpack(open(os.path.join(base, "Country.bin"), "rb").read())

    cflag = {}
    for i in range(0, len(cty), 1420):
        r = cty[i : i + 1420]
        fid = (int.from_bytes(r[:4], "little") >> 10) & 0x1FF
        n = pesdb.cstr(r[148:218]).strip()
        if n:
            cflag.setdefault(n.upper(), fid)

    def flag_of(country):
        want = country.upper()
        if want in cflag:
            return cflag[want]
        for name, fid in cflag.items():
            if name.startswith(want[:5]) or want.startswith(name[:5]):
                return fid
        raise SystemExit("sin id de bandera para %r" % country)

    rowoff = {}
    for o in range(0, len(teams), T_REC):
        rowoff[int.from_bytes(teams[o + T_ID : o + T_ID + 4], "little")] = o

    names = {
        tid: pesdb.cstr(teams[o + T_NAME : o + T_NAME + T_NAME_LEN]).strip()
        for tid, o in rowoff.items()
    }

    def ent_index(tid, cid):
        for k in range(0, len(ents), M.ENT):
            if (
                int.from_bytes(ents[k : k + 4], "little") == tid
                and ents[k + M.E_CID] == cid
            ):
                return k
        return None

    def rename(tid, text, fid):
        o = rowoff[tid]
        row = bytearray(teams[o : o + T_REC])
        put_team_name(row, text)
        set_country(row, fid)
        teams[o : o + T_REC] = row
        names[tid] = text

    def move(tid, src, dst):
        k = ent_index(tid, src)
        if k is None:
            raise SystemExit(
                "club %d (%s) no esta en la competicion %d" % (tid, names[tid], src)
            )
        ents[k + M.E_CID] = dst

    # --- checks before writing
    for spec in SPEC:
        if len(spec["moved"]) + len(spec["clubs"]) != 10:
            raise SystemExit(
                "league %s: %d moved + %d clubs != 10"
                % (spec["name"], len(spec["moved"]), len(spec["clubs"]))
            )
    used = {}
    for tid, n in names.items():
        used.setdefault(n.lower(), []).append(tid)
    problems = []
    for spec in SPEC:
        for n in spec["clubs"]:
            hit = used.get(n.lower())
            if hit:
                problems.append("%s: already in the world as %s" % (n, hit))
    for n, _ in REFILL:
        hit = used.get(n.lower())
        if hit:
            problems.append("%s: already in the world as %s" % (n, hit))
    if problems:
        print("nombres duplicados:")
        for p in problems:
            print("  " + p)
        return 1

    # --- the five leagues
    for spec in SPEC:
        cid, reg = spec["cid"], spec["reg"]
        fid = spec["country"]
        donors = [
            int.from_bytes(ents[k : k + 4], "little")
            for k in range(0, len(ents), M.ENT)
            if ents[k + M.E_CID] == cid
        ]
        if len(donors) != 10:
            raise SystemExit("cid %d has %d clubs, expected 10" % (cid, len(donors)))
        for tid in spec["moved"]:
            move(tid, OTHER_EU, cid)
            if tid in spec["rename"]:
                rename(tid, spec["rename"][tid], fid)
        free = [t for t in donors if ent_index(t, cid) is not None]
        staying = free[: len(spec["clubs"])]
        leaving = free[len(spec["clubs"]) :]
        if len(leaving) != len(spec["moved"]):
            raise SystemExit(
                "league %s: %d leaving for %d moved"
                % (spec["name"], len(leaving), len(spec["moved"]))
            )
        for tid, name in zip(staying, spec["clubs"]):
            rename(tid, name, fid)
        print(
            "reg %-3d cid %-2d %-38s %d clubes (%d movidos)"
            % (reg, cid, spec["name"], 10, len(spec["moved"]))
        )
        spec["_leaving"] = leaving

        # regulation name and teams
        for i in range(0, len(regs), M.REG):
            if int.from_bytes(regs[i + M.R_ID : i + M.R_ID + 2], "little") != reg:
                continue
            rc = bytearray(regs[i : i + M.REG])
            M.put_names(rc, 0, spec["name"])
            rc[M.R_TEAMS] = (rc[M.R_TEAMS] & ~0x3F) | 10
            regs[i : i + M.REG] = rc
            break
        else:
            raise SystemExit("no regulation %d" % reg)

        # competition row: name and code
        for i in range(0, len(comp), M.COMP):
            if comp[i + M.CID_OFF] != cid:
                continue
            cc = bytearray(comp[i : i + M.COMP])
            code = ("FL_%03d_D1" % fid).encode("ascii")[:11]
            cc[M.CODE_OFF : M.CODE_OFF + 12] = code.ljust(12, b"\0")
            # the name field of a Competition.bin row is 16 bytes, from +0x14
            nm = spec["name"].encode("utf-8")[:15]
            cc[20:36] = nm.ljust(16, b"\0")
            comp[i : i + M.COMP] = cc
            break

    # --- the clubs that go the other way, into Other European Leagues
    leaving = [t for spec in SPEC for t in spec["_leaving"]]
    if len(leaving) != len(REFILL):
        raise SystemExit("%d leaving for %d refills" % (len(leaving), len(REFILL)))
    for tid, (name, country) in zip(leaving, REFILL):
        for spec in SPEC:
            if tid in spec["_leaving"]:
                move(tid, spec["cid"], OTHER_EU)
                break
        rename(tid, name, flag_of(country))
    print(
        "Other European: %d clubes nuevos -> %s"
        % (len(leaving), ", ".join(n for n, _ in REFILL))
    )

    # --- Other Latin American Teams
    if latin:
        cid = 95
        gen = [
            int.from_bytes(ents[k : k + 4], "little")
            for k in range(0, len(ents), M.ENT)
            if ents[k + M.E_CID] == cid
        ]
        taken = {}
        for tid, n in names.items():
            taken.setdefault(core(n), True)
        picked = []
        for name, country in LATIN:
            if len(picked) == len(gen):
                break
            if name.lower() in used or core(name) in taken:
                continue
            used[name.lower()] = [-1]
            picked.append((name, country))
        if len(picked) < len(gen):
            raise SystemExit(
                "Latin America: %d names for %d clubs" % (len(picked), len(gen))
            )
        for tid, (name, country) in zip(gen, picked):
            rename(tid, name, flag_of(country))
        print("Other Latin American: %d clubes reales" % len(gen))
        for name, country in picked:
            print("    %-26s %s" % (name, country))

    # --- renumber the order of every competition we touched
    touched = {s["cid"] for s in SPEC} | ({95} if latin else set()) | {OTHER_EU}
    for cid in touched:
        n = 0
        for k in range(0, len(ents), M.ENT):
            if ents[k + M.E_CID] == cid:
                n += 1
                ents[k + M.E_ORDER] = n
        print("  cid %-3d order 1..%d" % (cid, n))

    if dry:
        print("dry run: nothing written")
        return 0

    open(os.path.join(base, "Team.bin"), "wb").write(pesdb.wesys_pack(bytes(teams)))
    open(os.path.join(base, "CompetitionEntry.bin"), "wb").write(
        pesdb.wesys_pack(bytes(ents))
    )
    open(os.path.join(base, "CompetitionRegulation.bin"), "wb").write(
        pesdb.wesys_pack(bytes(regs))
    )
    open(os.path.join(base, "Competition.bin"), "wb").write(
        pesdb.wesys_pack(bytes(comp))
    )

    # --- the world file: rewrite the five lines, drop the empty twins
    lines = io.open(wf, encoding="utf-8", errors="replace").read().splitlines()
    out = []
    for line in lines:
        w = line.split()
        if not w:
            out.append(line)
            continue
        if w[0] == "league" and len(w) > 1 and w[1].isdigit():
            rid = int(w[1])
            if rid in (382, 383):
                print("world: fuera la gemela vacia %d" % rid)
                continue
            spec = next((s for s in SPEC if s["reg"] == rid), None)
            if spec:
                kv = dict(x.split("=", 1) for x in w[2:] if "=" in x)
                out.append(
                    "league %d cid=%s region=%s country=%d conf=2 slot=%s tier=1 "
                    "promote=0 demote=0 clubs=10 legs=%s kickoff=%s name=%s"
                    % (
                        rid,
                        kv.get("cid", spec["cid"]),
                        kv.get("region", "29"),
                        spec["country"],
                        kv.get("slot", "-1"),
                        kv.get("legs", "2"),
                        kv.get("kickoff", "99"),
                        spec["name"],
                    )
                )
                continue
        out.append(line)
    io.open(wf, "w", encoding="utf-8", newline="\n").write("\n".join(out) + "\n")
    print("world: %d lineas" % len(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
