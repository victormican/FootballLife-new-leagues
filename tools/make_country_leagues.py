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
T_CANON = 0x170
T_ABBR, T_SHORT = 0x372, 0x35A
T_LONG, T_LONG_LEN = 0x37C, 22
OTHER_EU = 98
OTHER_EU_REG = 364
GAME_CLUB_MAX = 71578

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

# Second wave (2026-11-03): Belarus, Kazakhstan, Estonia, Armenia, Latvia, Lithuania, Kosovo,
# Northern Ireland and Finland, plus the Liechtenstein cup, which takes the place of Copa
# Argentina: its competition id carries a competition that country really has.
SPEC2 = [
    {
        "reg": 344,
        "cid": 55,
        "country": 196,
        "name": "Vysheyshaya Liga",
        "moved": [],
        "rename": {},
        "take": ["BATE Borisov", "Dinamo Minsk", "Shakhtyor Soligorsk"],
        "clubs": [
            "Neman Grodno",
            "Torpedo-BelAZ Zhodino",
            "Dinamo Brest",
            "Isloch Minsk",
            "Slavia Mozyr",
            "FC Vitebsk",
            "FC Gomel",
        ],
    },
    {
        "reg": 345,
        "cid": 57,
        "country": 216,
        "name": "Kazakhstan Premier League",
        "moved": [],
        "rename": {},
        "take": ["Kairat Almaty", "FC Astana"],
        "clubs": [
            "FK Aktobe",
            "Tobol Kostanay",
            "Ordabasy Shymkent",
            "Kyzylzhar Petropavlovsk",
            "FC Atyrau",
            "Kaspy Aktau",
            "Zhetysu Taldykorgan",
            "Okzhetpes Kokshetau",
        ],
    },
    {
        "reg": 346,
        "cid": 58,
        "country": 205,
        "name": "Meistriliiga",
        "moved": [],
        "rename": {},
        "take": ["Flora Tallinn"],
        "clubs": [
            "Levadia Tallinn",
            "Nomme Kalju",
            "Paide Linnameeskond",
            "Trans Narva",
            "FC Kuressaare",
            "Tammeka Tartu",
            "Parnu Vaprus",
            "Harju JK Laagri",
            "Kalev Tallinn",
        ],
    },
    {
        "reg": 347,
        "cid": 59,
        "country": 193,
        "name": "Armenian Premier League",
        "moved": [],
        "rename": {},
        "take": ["Ararat-Armenia", "Pyunik Yerevan"],
        "clubs": [
            "FC Urartu",
            "Ararat Yerevan",
            "Alashkert",
            "FC Noah",
            "Van Charentsavan",
            "BKMA Yerevan",
            "West Armenia",
            "Shirak Gyumri",
        ],
    },
    {
        "reg": 348,
        "cid": 60,
        "country": 217,
        "name": "Virsliga",
        "moved": [],
        "rename": {},
        "take": ["Riga FC", "FC RFS"],
        "clubs": [
            "Valmiera FC",
            "FK Liepaja",
            "FK Ventspils",
            "BFC Daugavpils",
            "Metta",
            "Super Nova",
            "Tukums 2000",
            "Auda",
        ],
    },
    {
        "reg": 349,
        "cid": 61,
        "country": 219,
        "name": "A Lyga",
        "moved": [],
        "rename": {},
        "take": ["Zalgiris Vilnius", "Suduva"],
        "clubs": [
            "Kauno Zalgiris",
            "FK Panevezys",
            "Hegelmann",
            "FA Siauliai",
            "Banga Gargzdai",
            "Dziugas Telsiai",
            "TransINVEST",
            "Dainava Alytus",
        ],
    },
    {
        "reg": 350,
        "cid": 62,
        "country": 311,
        "name": "Superliga e Kosoves",
        "moved": [],
        "rename": {},
        "take": ["FC Ballkani", "KF Prishtina"],
        "clubs": [
            "Drita Gjilan",
            "SC Gjilani",
            "KF Feronikeli",
            "KF Llapi",
            "KF Dukagjini",
            "KF Malisheva",
            "KF Vushtrria",
            "KF Istogu",
        ],
    },
    {
        "reg": 351,
        "cid": 63,
        "country": 225,
        "name": "NIFL Premiership",
        "moved": [],
        "rename": {},
        "take": [],
        "clubs": [
            "Linfield",
            "Glentoran",
            "Crusaders",
            "Cliftonville",
            "Coleraine",
            "Glenavon",
            "Ballymena United",
            "Portadown",
            "Dungannon Swifts",
            "Carrick Rangers",
        ],
    },
    {
        "reg": 352,
        "cid": 64,
        "country": 207,
        "name": "Veikkausliiga",
        "moved": [],
        "rename": {},
        "take": ["HJK Helsinki", "KuPS", "Inter Turku", "Ilves"],
        "clubs": [
            "HIFK",
            "FC Honka",
            "FC Lahti",
            "IFK Mariehamn",
            "SJK Seinajoki",
            "VPS Vaasa",
        ],
    },
    {
        "reg": 375,
        "cid": 48,
        "country": 218,
        "name": "Liechtensteiner Cup",
        "moved": [],
        "rename": {},
        "take": ["Vaduz"],
        "size": 7,
        "fresh": True,
        "clubs": [
            "USV Eschen/Mauren",
            "FC Balzers",
            "FC Ruggell",
            "FC Schaan",
            "FC Triesen",
            "FC Triesenberg",
        ],
    },
]

# Third wave (2026-11-03): Luxembourg, the Faroe Islands and San Marino, the last three countries
# of the batched generic leagues.
SPEC3 = [
    {
        "reg": 353,
        "cid": 80,
        "country": 220,
        "name": "National Division",
        "moved": [],
        "rename": {},
        "take": [
            "F91 Dudelange",
            "Jeunesse Esch",
            "Progres Niederkorn",
            "FC Differdange 03",
        ],
        "clubs": [
            "Racing FC Union Luxembourg",
            "Swift Hesperange",
            "FC Rodange 91",
            "US Mondorf-les-Bains",
            "US Hostert",
            "FC Wiltz 71",
        ],
    },
    {
        "reg": 354,
        "cid": 81,
        "country": 206,
        "name": "Betri deildin",
        "moved": [],
        "rename": {},
        "take": [
            "Vikingur Gota",
            "HB Torshavn",
            "NSI Runavik",
            "KI Klaksvik",
        ],
        "clubs": [
            "B36 Torshavn",
            "B68 Toftir",
            "EB/Streymur",
            "IF Fuglafjordur",
            "Skala IF",
            "07 Vestur",
        ],
    },
    {
        "reg": 355,
        "cid": 83,
        "country": 231,
        "name": "Campionato Sammarinese",
        "moved": [],
        "rename": {},
        "take": ["Tre Fiori", "Tre Penne", "La Fiorita"],
        "clubs": [
            "Folgore",
            "Virtus",
            "Libertas",
            "Cosmos",
            "Domagnano",
            "Faetano",
            "Juvenes/Dogana",
        ],
    },
]

REFILL3 = [
    ("Silkeborg IF", "DINAMARCA"),
    ("Randers FC", "DINAMARCA"),
    ("Vejle BK", "DINAMARCA"),
    ("AC Horsens", "DINAMARCA"),
    ("Dundee FC", "ESCOCIA"),
    ("St Mirren", "ESCOCIA"),
    ("Livingston FC", "ESCOCIA"),
    ("Kayserispor", "TURQUÍA"),
    ("Gaziantep FK", "TURQUÍA"),
    ("Alanyaspor", "TURQUÍA"),
    ("Torpedo Moscow", "RUSIA"),
    ("Baltika Kaliningrad", "RUSIA"),
    ("FC Orenburg", "RUSIA"),
    ("TPS Turku", "FINLANDIA"),
    ("IF Gnistan", "FINLANDIA"),
    ("Birkirkara FC", "MALTA"),
    ("UE Sant Julia", "ANDORRA"),
    ("Speranta Nisporeni", "MOLDAVIA"),
    ("FC Telavi", "GEORGIA"),
    ("FC Belshina Bobruisk", "BIELORRUSIA"),
    ("Hvidovre IF", "DINAMARCA"),
    ("FC Helsingor", "DINAMARCA"),
    ("Partick Thistle", "ESCOCIA"),
    ("Raith Rovers", "ESCOCIA"),
    ("Caykur Rizespor", "TURQUÍA"),
    ("Goztepe", "TURQUÍA"),
    ("Pari Nizhny Novgorod", "RUSIA"),
    ("Fakel Voronezh", "RUSIA"),
    ("Hamrun Spartans", "MALTA"),
    ("Gzira United", "MALTA"),
    ("Penya Encarnada", "ANDORRA"),
    ("Zaria Balti", "MOLDAVIA"),
    ("FC Samtredia", "GEORGIA"),
    ("FC Slutsk", "BIELORRUSIA"),
]

# Fourth wave (2026-11-03): the last six generic leagues. Moldova, Andorra, Malta, Gibraltar and
# Georgia get their league; the sixth carries Liechtenstein's cup, whose seven clubs come from the
# old "Copa Argentina" competition (cid 48), which disappears with this wave.
SPEC4 = [
    {
        "reg": 356,
        "cid": 85,
        "country": 223,
        "name": "Super Liga",
        "moved": [],
        "rename": {},
        "take": [
            "FC Sheriff Tiraspol",
            "Zimbru Chisinau",
            "Dacia Chisinau",
            "Speranta Nisporeni",
        ],
        "clubs": [
            "Milsami Orhei",
            "FC Balti",
            "Petrocub Hincesti",
            "Sfintul Gheorghe",
            "Dinamo-Auto Tiraspol",
            "Codru Lozova",
        ],
    },
    {
        "reg": 357,
        "cid": 87,
        "country": 192,
        "name": "Primera Divisio",
        "moved": [],
        "rename": {},
        "take": ["Santa Coloma", "Inter Club d'Escaldes", "UE Sant Julia"],
        "clubs": [
            "Penya Encarnada",
            "FC Ordino",
            "UE Engordany",
            "FC Encamp",
            "Lusitanos",
            "Atletic Escaldes",
            "CE Carroi",
        ],
    },
    {
        "reg": 358,
        "cid": 88,
        "country": 222,
        "name": "Maltese Premier League",
        "moved": [],
        "rename": {},
        "take": [
            "Valletta",
            "Hibernians",
            "Floriana FC",
            "Birkirkara FC",
        ],
        "clubs": [
            "Hamrun Spartans",
            "Gzira United",
            "Mosta FC",
            "Balzan FC",
            "Sirens FC",
            "Sliema Wanderers",
        ],
    },
    {
        "reg": 359,
        "cid": 89,
        "country": 245,
        "name": "Gibraltar Football League",
        "moved": [],
        "rename": {},
        "take": ["Lincoln Red Imps", "St Joseph's"],
        "clubs": [
            "Lynx FC",
            "Mons Calpe",
            "Glacis United",
            "Britannia XI",
            "Manchester 62",
            "Europa Point",
            "College 1975",
            "Lions Gibraltar",
        ],
    },
    {
        "reg": 360,
        "cid": 93,
        "country": 209,
        "name": "Erovnuli Liga",
        "moved": [],
        "rename": {},
        "take": [
            "Dinamo Tbilisi",
            "Dinamo Batumi",
            "Torpedo Kutaisi",
            "Saburtalo Tbilisi",
            "FC Telavi",
        ],
        "clubs": ["Iberia 1999", "Dila Gori", "Samgurali", "Gagra", "Sioni Bolnisi"],
    },
    {
        "reg": 361,
        "cid": 94,
        "country": 218,
        "name": "Liechtensteiner Cup",
        "moved": [],
        "rename": {},
        "size": 7,
        "take_from": 48,
        "take": [
            "Vaduz",
            "USV Eschen/Mauren",
            "FC Balzers",
            "FC Ruggell",
            "FC Schaan",
            "FC Triesen",
            "FC Triesenberg",
        ],
        "clubs": [],
        "drop": (375, 48),
    },
]

# No refills: every UEFA country has a league after this wave, so the donors that are left over are
# let go and "Other European Leagues" ends with the clubs that nobody else wanted.
REFILL4 = []

# The donor clubs each new league does not need go to "Other European Leagues", renamed to real
# clubs of countries that still have no league of their own.  Names already in the world are
# skipped, so the list is longer than the clubs needed.
REFILL2 = [
    ("FC Copenhagen", "DINAMARCA"),
    ("FC Nordsjaelland", "DINAMARCA"),
    ("FC Midtjylland", "DINAMARCA"),
    ("Motherwell", "ESCOCIA"),
    ("St Johnstone", "ESCOCIA"),
    ("Kilmarnock", "ESCOCIA"),
    ("Ross County", "ESCOCIA"),
    ("Fenerbahce", "TURQUÍA"),
    ("Besiktas", "TURQUÍA"),
    ("Kasimpasa", "TURQUÍA"),
    ("Antalyaspor", "TURQUÍA"),
    ("Dynamo Moscow", "RUSIA"),
    ("Ural Yekaterinburg", "RUSIA"),
    ("FC Haka", "FINLANDIA"),
    ("Saburtalo Tbilisi", "GEORGIA"),
    ("Sliema Wanderers", "MALTA"),
    ("Floriana FC", "MALTA"),
    ("Progres Niederkorn", "LUXEMBURGO"),
    ("FC Differdange 03", "LUXEMBURGO"),
    ("Vikingur Gota", "ISLAS FEROE"),
    ("HB Torshavn", "ISLAS FEROE"),
    ("NSI Runavik", "ISLAS FEROE"),
    ("Europa FC", "GIBRALTAR"),
    ("St Joseph's", "GIBRALTAR"),
    ("Inter Club d'Escaldes", "ANDORRA"),
    ("Tre Fiori", "SAN MARINO"),
    ("Tre Penne", "SAN MARINO"),
    ("Zimbru Chisinau", "MOLDAVIA"),
    ("Silkeborg IF", "DINAMARCA"),
    ("Randers FC", "DINAMARCA"),
    ("Konyaspor", "TURQUÍA"),
    ("Krylia Sovetov", "RUSIA"),
    ("FC Sochi", "RUSIA"),
    ("Dacia Chisinau", "MOLDAVIA"),
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
    wave2 = "--wave2" in a
    wave3 = "--wave3" in a
    wave4 = "--wave4" in a
    if wave4:
        spec_list, refill_list = SPEC4, REFILL4
    elif wave3:
        spec_list, refill_list = SPEC3, REFILL3
    elif wave2:
        spec_list, refill_list = SPEC2, REFILL2
    else:
        spec_list, refill_list = SPEC, REFILL

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
        tid: pesdb.cstr(teams[o + T_CANON : o + T_CANON + T_NAME_LEN]).strip()
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

    def tid_of(name):
        for tid, n in names.items():
            if n.strip().lower() == name.strip().lower():
                return tid
        raise SystemExit("no esta en el mundo: %r" % name)

    def move(tid, src, dst):
        k = ent_index(tid, src)
        if k is None:
            raise SystemExit(
                "club %d (%s) no esta en la competicion %d" % (tid, names[tid], src)
            )
        ents[k + M.E_CID] = dst

    # --- checks before writing
    for spec in spec_list:
        spec["moved"] = list(spec["moved"]) + [tid_of(n) for n in spec.get("take", [])]
        if len(spec["moved"]) + len(spec["clubs"]) != spec.get("size", 10):
            raise SystemExit(
                "league %s: %d moved + %d clubs != %d"
                % (
                    spec["name"],
                    len(spec["moved"]),
                    len(spec["clubs"]),
                    spec.get("size", 10),
                )
            )
    used = {}
    for tid, n in names.items():
        used.setdefault(n.lower(), []).append(tid)
    problems = []
    for spec in spec_list:
        for n in spec["clubs"]:
            hit = used.get(n.lower())
            if hit:
                problems.append("%s: already in the world as %s" % (n, hit))
    if problems:
        print("nombres duplicados:")
        for p in problems:
            print("  " + p)
        return 1

    # --- one league per country
    in_entry = {
        int.from_bytes(ents[k : k + 4], "little") for k in range(0, len(ents), M.ENT)
    }
    fresh_pool = sorted(
        t
        for t in rowoff
        if t >= GAME_CLUB_MAX
        and t not in in_entry
        and "CLASSICS" not in names.get(t, "").upper()
    )
    fresh_taken = set()
    trim = []
    for spec in spec_list:
        cid, reg = spec["cid"], spec["reg"]
        fid = spec["country"]
        donors = [
            int.from_bytes(ents[k : k + 4], "little")
            for k in range(0, len(ents), M.ENT)
            if ents[k + M.E_CID] == cid
        ]
        want = len(spec["clubs"]) + len(spec["moved"])
        if len(donors) < want:
            raise SystemExit("cid %d has %d clubs, needs %d" % (cid, len(donors), want))
        for tid in spec["moved"]:
            move(tid, spec.get("take_from", OTHER_EU), cid)
            # a real club that joins its country's league takes that country's flag
            rename(tid, spec["rename"].get(tid, names[tid]), fid)
        if spec.get("fresh"):
            # the competition's own entries belong to clubs that play elsewhere (the old Copa
            # Argentina): they go, and the new clubs come from team rows nobody uses
            trim += [(t, cid) for t in donors]
            pool = [t for t in fresh_pool if t not in fresh_taken]
            pick = pool[: len(spec["clubs"])]
            if len(pick) < len(spec["clubs"]):
                raise SystemExit(
                    "no hay clubes genericos libres para %s" % spec["name"]
                )
            fresh_taken |= set(pick)
            for tid, name in zip(pick, spec["clubs"]):
                rename(tid, name, fid)
            eid = max(
                int.from_bytes(ents[k + M.E_EID : k + M.E_EID + 4], "little")
                for k in range(0, len(ents), M.ENT)
            )
            for k, tid in enumerate(pick):
                e = bytearray(M.ENT)
                e[M.E_TEAM : M.E_TEAM + 4] = tid.to_bytes(4, "little")
                e[M.E_EID : M.E_EID + 4] = (eid + 1 + k).to_bytes(4, "little")
                e[M.E_CID] = cid
                e[M.E_ORDER] = k + 1
                ents += e
            print(
                "reg %-3d cid %-2d %-38s %d clubes (%d nuevos, %d fuera)"
                % (reg, cid, spec["name"], want, len(pick), len(donors))
            )
            spec["_leaving"] = []
        else:
            free = [t for t in donors if ent_index(t, cid) is not None]
            staying = free[: len(spec["clubs"])]
            leaving = free[len(spec["clubs"]) : len(spec["clubs"]) + len(spec["moved"])]
            trim += [(t, cid) for t in free[len(spec["clubs"]) + len(spec["moved"]) :]]
            for tid, name in zip(staying, spec["clubs"]):
                rename(tid, name, fid)
            print(
                "reg %-3d cid %-2d %-38s %d clubes (%d movidos%s)"
                % (
                    reg,
                    cid,
                    spec["name"],
                    want,
                    len(spec["moved"]),
                    ", %d fuera" % (len(free) - want) if len(free) > want else "",
                )
            )
            spec["_leaving"] = leaving

        # regulation name and teams
        for i in range(0, len(regs), M.REG):
            if int.from_bytes(regs[i + M.R_ID : i + M.R_ID + 2], "little") != reg:
                continue
            rc = bytearray(regs[i : i + M.REG])
            M.put_names(rc, 0, spec["name"])
            rc[M.R_TEAMS] = (rc[M.R_TEAMS] & ~0x3F) | (want & 0x3F)
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

    # --- competitions this wave retires (the old Copa Argentina, whose clubs moved to Liechtenstein)
    for spec in spec_list:
        if not spec.get("drop"):
            continue
        rid, gone = spec["drop"]
        keep = bytearray()
        for i in range(0, len(regs), M.REG):
            if int.from_bytes(regs[i + M.R_ID : i + M.R_ID + 2], "little") != rid:
                keep += regs[i : i + M.REG]
        regs = keep
        keep = bytearray()
        for i in range(0, len(comp), M.COMP):
            if comp[i + M.CID_OFF] != gone:
                keep += comp[i : i + M.COMP]
        comp = keep
        keep = bytearray()
        for k in range(0, len(ents), M.ENT):
            if ents[k + M.E_CID] != gone:
                keep += ents[k : k + M.ENT]
        ents = keep
        print("fuera la competicion %d y su regulacion %d" % (gone, rid))

    # --- the clubs that go the other way, into Other European Leagues
    leaving = [(spec, t) for spec in spec_list for t in spec["_leaving"]]
    seen_core = {core(v) for v in names.values()}
    refills = []
    for name, country in refill_list:
        if len(refills) == len(leaving):
            break
        if name.lower() in used or core(name) in seen_core:
            continue
        refills.append((name, country))
    for (spec, tid), (name, country) in zip(leaving, refills):
        move(tid, spec["cid"], OTHER_EU)
        rename(tid, name, flag_of(country))
        print("Other European: %-24s %s" % (name, country))
    for spec, tid in leaving[len(refills) :]:
        trim.append((tid, spec["cid"]))
    if len(leaving) > len(refills):
        print(
            "Other European: %d sobrantes fuera (no hay club real con plaza libre)"
            % (len(leaving) - len(refills))
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

    if trim:
        drop = set(trim)
        keep = bytearray()
        for k in range(0, len(ents), M.ENT):
            key = (int.from_bytes(ents[k : k + 4], "little"), ents[k + M.E_CID])
            if key not in drop:
                keep += ents[k : k + M.ENT]
        ents = keep
        print("fuera %d entradas sobrantes" % len(drop))

    # --- renumber the order of every competition we touched
    touched = {s["cid"] for s in spec_list} | ({95} if latin else set()) | {OTHER_EU}
    for cid in sorted(touched):
        n = 0
        for k in range(0, len(ents), M.ENT):
            if ents[k + M.E_CID] == cid:
                n += 1
                ents[k + M.E_ORDER] = n
        print("  cid %-3d order 1..%d" % (cid, n))

    # --- "Other European Leagues" keeps whatever clubs have no league of their own
    eu_count = sum(
        1 for k in range(0, len(ents), M.ENT) if ents[k + M.E_CID] == OTHER_EU
    )
    for i in range(0, len(regs), M.REG):
        if int.from_bytes(regs[i + M.R_ID : i + M.R_ID + 2], "little") != OTHER_EU_REG:
            continue
        rc = bytearray(regs[i : i + M.REG])
        rc[M.R_TEAMS] = (rc[M.R_TEAMS] & ~0x3F) | (eu_count & 0x3F)
        regs[i : i + M.REG] = rc
        print("Other European: %d clubes" % eu_count)
        break

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
            if rid in (382, 383) or any(
                s.get("drop") and s["drop"][0] == rid for s in spec_list
            ):
                print("world: fuera la liga %d" % rid)
                continue
            spec = next((s for s in spec_list if s["reg"] == rid), None)
            if spec:
                kv = dict(x.split("=", 1) for x in w[2:] if "=" in x)
                out.append(
                    "league %d cid=%s region=%s country=%d conf=2 slot=%s tier=1 "
                    "promote=0 demote=0 clubs=%d legs=%s kickoff=%s name=%s"
                    % (
                        rid,
                        kv.get("cid", spec["cid"]),
                        kv.get("region", "29"),
                        spec["country"],
                        kv.get("slot", "-1"),
                        len(spec["clubs"]) + len(spec["moved"]),
                        kv.get("legs", "2"),
                        kv.get("kickoff", "99"),
                        spec["name"],
                    )
                )
                continue
            if rid == OTHER_EU_REG:
                parts = [
                    "clubs=%d" % eu_count if p.startswith("clubs=") else p for p in w
                ]
                out.append(" ".join(parts))
                continue
        out.append(line)
    io.open(wf, "w", encoding="utf-8", newline="\n").write("\n".join(out) + "\n")
    print("world: %d lineas" % len(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
