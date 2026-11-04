"""python add_eight_leagues.py --base <pesdb> --world <fl26world.txt> [--dry]

The eight leagues that were missing, each with its own competition (cid 258..265), regulation,
region, Select Team slot and clubs recycled from the rows no competition owns.

Clubs are rows of the game whose name is still "Something Club NN": they are renamed and given
the country, so no club is duplicated and no competition loses a club.
"""

import io
import os
import re
import sys

sys.path.insert(0, r"C:\Users\viarm\test-carpeta\pes-2021\tools")
import mkleague as M
import pesdb
from make_country_leagues import put_team_name, set_country

T_REC, T_ID, T_NAME = 1532, 0x08, 0x170

# name, code, cid, reg, country(flag), conf, region(id), slot, legs, kickoff, reply
LEAGUES = [
    ("TT Premier Football League", "FL_TT_D1", 258, 900, 133, 6, 115, -1, 2, 20, 10),
    ("TFF 1. Lig", "FL_TR_D2", 259, 901, 190, 2, 116, -1, 2, 25, 18),
    ("Aruba Division di Honor", "FL_AW_D1", 260, 902, 105, 6, 117, -1, 2, 30, 10),
    ("Russian First League", "FL_RU_D2", 261, 903, 230, 2, 118, -1, 2, 22, 18),
    ("Danish 1. Division", "FL_DK_D2", 262, 904, 203, 2, 119, -1, 2, 28, 12),
    ("Scottish Championship", "FL_SC_D2", 263, 905, 232, 2, 120, -1, 2, 30, 10),
    ("Swiss Challenge League", "FL_CH_D2", 264, 906, 238, 2, 121, -1, 2, 25, 10),
    ("Yokary Liga", "FL_TM_D1", 265, 907, 42, 3, 122, -1, 2, 40, 8),
    ("USL Championship", "FL_USL_CH", 266, 908, 135, 6, 123, -1, 2, 25, 10),
]

CLUBS = {
    "TT Premier Football League": [
        "Central FC",
        "W Connection",
        "Defence Force",
        "San Juan Jabloteh",
        "Morvant Caledonia United",
        "Point Fortin Civic",
        "Club Sando",
        "Police FC",
        "Cunupia FC",
        "La Horquetta Rangers",
    ],
    "TFF 1. Lig": [
        "Kocaelispor",
        "Boluspor",
        "Erzurumspor",
        "Sakaryaspor",
        "Bandirmaspor",
        "Umraniyespor",
        "Manisa FK",
        "Keciorengucu",
        "Adanaspor",
        "Sanliurfaspor",
        "Istanbulspor",
        "Amed Sportif",
        "Corum FK",
        "Igdir FK",
        "Serik Belediyespor",
        "Pendikspor",
        "Esenler Erokspor",
        "Genclerbirligi",
    ],
    "Aruba Division di Honor": [
        "SV Dakota",
        "SV Britannia",
        "River Plate Aruba",
        "SV La Fama",
        "SV Nacional",
        "SV Estrella",
        "SV Bubali",
        "Deportivo Nacional",
        "Sporting Aruba",
        "SV Caiquetio",
    ],
    "Russian First League": [
        "Torpedo Moscow",
        "Baltika",
        "Rodina",
        "Rotor Volgograd",
        "Ural",
        "Shinnik",
        "Chayka",
        "KAMAZ",
        "Neftekhimik",
        "Yenisey",
        "SKA-Khabarovsk",
        "Alania",
        "Kuban",
        "Volgar",
        "Tekstilshchik",
        "Ufa",
        "Arsenal Tula",
        "Spartak Kostroma",
    ],
    "Danish 1. Division": [
        "Esbjerg fB",
        "AC Horsens",
        "Hobro IK",
        "Vendsyssel FF",
        "FC Fredericia",
        "Kolding IF",
        "Hillerod Fodbold",
        "B.93",
        "FC Roskilde",
        "Naestved BK",
        "AaB",
        "FC Helsingor",
    ],
    "Scottish Championship": [
        "Ayr United",
        "Dunfermline Athletic",
        "Falkirk",
        "Greenock Morton",
        "Hamilton Academical",
        "Livingston",
        "Partick Thistle",
        "Queen's Park",
        "Raith Rovers",
        "St Johnstone",
    ],
    "Swiss Challenge League": [
        "FC Aarau",
        "AC Bellinzona",
        "Etoile Carouge",
        "Neuchatel Xamax",
        "FC Schaffhausen",
        "Stade Lausanne Ouchy",
        "FC Thun",
        "FC Vaduz",
        "FC Wil",
        "Yverdon Sport",
    ],
    "Yokary Liga": [
        "Altyn Asyr",
        "Ahal",
        "Kopetdag",
        "Merw",
        "Nebitci",
        "Shagadam",
        "Energetik",
        "Asgabat",
    ],
    "USL Championship": [
        "Sacramento Republic",
        "Indy Eleven",
        "Louisville City",
        "Tampa Bay Rowdies",
        "Phoenix Rising",
        "San Antonio FC",
        "Detroit City",
        "Birmingham Legion",
        "New Mexico United",
        "Pittsburgh Riverhounds",
    ],
}


def main():
    a = sys.argv[1:]
    get = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    base, world = get("--base"), get("--world")
    if not base or not world:
        print(__doc__)
        return 1
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
    teams_raw = bytearray(
        pesdb.wesys_unpack(open(os.path.join(base, "Team.bin"), "rb").read())
    )

    used = set()
    for i in range(0, len(ents), M.ENT):
        used.add(int.from_bytes(ents[i : i + 4], "little"))
    taken = {
        int.from_bytes(comp[i + M.CID_OFF : i + M.CID_OFF + 1], "little")
        | (comp[i + M.C_CID_HI] << 8)
        for i in range(0, len(comp), M.COMP)
    }
    free = []
    for i in range(0, len(teams_raw), T_REC):
        r = teams_raw[i : i + T_REC]
        tid = int.from_bytes(r[T_ID : T_ID + 4], "little")
        nm = r[T_NAME : T_NAME + 60].split(b"\x00")[0].decode("latin1", "replace")
        # a row of the "Other ..." pools carries a pool number in the high nibble of +0x4f:
        # Select Team lists those clubs even with no competition entry, so taking one renames a
        # club of the pool (it happened with Other Latin American, 2026-11-04)
        in_pool = (r[0x4F] >> 4) != 0
        if tid not in used and not in_pool and re.search(r"Club \d+$", nm):
            free.append(tid)
    free.sort()
    print("%d filas de club libres" % len(free))

    lines = []
    for name, code, cid, reg, flag, conf, region, slot, legs, kickoff, n in LEAGUES:
        if cid in taken:
            print("%s: cid %d ya existe, se omite" % (name, cid))
            continue
        if len(free) < n:
            print("%s: solo quedan %d filas libres" % (name, len(free)))
            return 2
        rows, free = free[:n], free[n:]
        for row_id, club in zip(rows, CLUBS[name]):
            i = teams_raw.find(row_id.to_bytes(4, "little"))
            off = row_id * 0  # find the record by scanning
            for k in range(0, len(teams_raw), T_REC):
                if (
                    int.from_bytes(teams_raw[k + T_ID : k + T_ID + 4], "little")
                    == row_id
                ):
                    row = teams_raw[k : k + T_REC]
                    put_team_name(row, club)
                    set_country(row, flag)
                    teams_raw[k : k + T_REC] = row
                    break
        M.add_league(
            comp,
            regs,
            ents,
            cid,
            reg,
            M.enc_region(region),
            name,
            code,
            rows,
            proto_code="FL_223_D1",
            quiet=True,
            tier=1,
        )
        # add_league writes a 28-byte code, which also clears the 16-byte name at +0x14: the
        # menu does not list a competition without it (new_league.py writes it for the same
        # reason). This was the bug on 2026-11-04: the eight leagues came out nameless.
        M.put(comp, (len(comp) // M.COMP - 1) * M.COMP + 0x14, name, 16)
        lines.append(
            "league %d cid=%d region=%d country=%d conf=%d slot=%d tier=1 promote=0 demote=0 "
            "clubs=%d legs=%d kickoff=%d name=%s"
            % (reg, cid, region, flag, conf, slot, n, legs, kickoff, name)
        )
        print(
            "  %-28s cid %d reg %d region %d slot %d %d clubes"
            % (name, cid, reg, region, slot, n)
        )

    if dry:
        print("\n".join(lines))
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
    open(os.path.join(base, "Team.bin"), "wb").write(pesdb.wesys_pack(bytes(teams_raw)))

    cur = io.open(world, encoding="utf-8", errors="replace").read().splitlines()
    have = {l.split()[1] for l in cur if l.startswith("league ")}
    add = [l for l in lines if l.split()[1] not in have]
    # right after the last league line (the league block comes before uefa/rcal/ccup)
    at = max(i for i, l in enumerate(cur) if l.startswith("league "))
    cur[at + 1 : at + 1] = add
    io.open(world, "w", encoding="utf-8", newline="\n").write("\n".join(cur) + "\n")
    print("añadidas %d lineas league a %s" % (len(add), world))
    return 0


if __name__ == "__main__":
    sys.exit(main())
