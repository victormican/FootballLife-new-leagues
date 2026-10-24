"""python newlife_limits.py [--newlife <folder with the NewLife zips>] [--world <world pesdb>]
                          [--json]

How much of a NewLife release fits in the game's tables.  Read-only.

The caps with fl26caps (0.2.4): 2,400 teams, 61,905 players, 3,400 coaches, 600 regulations,
255 competitions.  The Select Team layout of this branch has 97 league slots, and a league needs
22-30 players a club, so the player cap is often the first wall.

A NewLife release is the 7 (1.4.x) or 10 (1.5b12) zips with clubs.csv, players.csv, coaches.csv
and newlife.json each; Deflate64 is fine for Python's zipfile.  An unpacked folder with the same
files works too.  `clubs.csv` has `in_game` (1 when the game already has the club), `country` and
`league`; the first league of a country in file order is taken as its first division.
"""

import csv
import io
import json
import os
import sys
import zipfile
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pesdb

CAPS = {
    "teams": 2400,
    "players": 61905,
    "coaches": 3400,
    "regulations": 600,
    "competitions": 255,
    "slots": 97,
    "regions": 127 - 29 + 1,
}
DEFAULT_WORLD = (
    r"D:\SP Football Life 2026\SiderAddons\livecpk\_FL26MyWorld\common\etc\pesdb"
)
DEFAULT_NEWLIFE = r"C:\Users\viarm\test-carpeta\newlife-classics\out"
SIZES = {
    "Team.bin": 1532,
    "Player.bin": 312,
    "Coach.bin": 600,
    "Competition.bin": 36,
    "CompetitionRegulation.bin": 2352,
}


def read_csv(path_or_zip, name):
    """(header, rows) of a member of a zip or a file in a folder, as dicts"""
    if path_or_zip.lower().endswith(".zip"):
        with zipfile.ZipFile(path_or_zip) as z:
            if name not in z.namelist():
                return []
            with z.open(name) as f:
                return list(
                    csv.DictReader(
                        io.TextIOWrapper(f, encoding="utf-8", errors="replace")
                    )
                )
    p = os.path.join(path_or_zip, name)
    if not os.path.isfile(p):
        return []
    with io.open(p, encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))


def json_of(path_or_zip):
    if path_or_zip.lower().endswith(".zip"):
        with zipfile.ZipFile(path_or_zip) as z:
            if "newlife.json" not in z.namelist():
                return {}
            return json.load(io.TextIOWrapper(z.open("newlife.json"), encoding="utf-8"))
    p = os.path.join(path_or_zip, "newlife.json")
    return json.load(io.open(p, encoding="utf-8")) if os.path.isfile(p) else {}


def read_part(path):
    clubs = read_csv(path, "clubs.csv")
    players = read_csv(path, "players.csv")
    coaches = read_csv(path, "coaches.csv")
    per = defaultdict(
        lambda: defaultdict(lambda: [0, 0])
    )  # country -> league -> [clubs, in_game]
    for row in clubs:
        c, lg = row.get("country", ""), row.get("league", "")
        ing = int(row.get("in_game") or 0)
        per[c][lg][0] += 1
        per[c][lg][1] += ing
    first = {}
    for c, leagues in per.items():
        for lg, (n, ing) in leagues.items():
            first[c] = (lg, n, ing)
            break
    name = os.path.basename(path)
    return {
        "part": name,
        "club_part": not any(k in name.lower() for k in ("selections", "fantasy", "classics")),
        "clubs": len(clubs),
        "players": len(players),
        "coaches": len(coaches),
        "in_game": sum(int(r.get("in_game") or 0) for r in clubs),
        "countries": len(per),
        "leagues": sum(len(v) for v in per.values()),
        "first": first,
        "json": json_of(path),
    }


def world_counts(path):
    out = {}
    for n, size in SIZES.items():
        p = os.path.join(path, n)
        if not os.path.isfile(p):
            out[n] = 0
            continue
        raw = pesdb.wesys_unpack(open(p, "rb").read())
        out[n] = len(raw) // size
    return out


def main():
    a = sys.argv[1:]
    get = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    nlf = get("--newlife", DEFAULT_NEWLIFE)
    world = get("--world", DEFAULT_WORLD)
    parts = []
    for n in sorted(os.listdir(nlf), key=str.lower):
        p = os.path.join(nlf, n)
        if n.lower().endswith(".zip") or (
            os.path.isdir(p) and os.path.isfile(os.path.join(p, "clubs.csv"))
        ):
            parts.append(read_part(p))
    total = {
        k: sum(p[k] for p in parts) for k in ("clubs", "players", "coaches", "in_game")
    }
    # one first division per country: the first part/league the country appears in
    first = {}
    for p in parts:
        if not p["club_part"]:
            continue
        for c, v in p["first"].items():
            first.setdefault(c, v)
    f_clubs = sum(v[1] for v in first.values())
    f_new = sum(v[1] - v[2] for v in first.values())
    f_sizes = [v[1] for v in first.values()]
    bins = Counter()
    for n in f_sizes:
        bins[
            "<10" if n < 10 else "10-24" if n <= 24 else "25-30" if n <= 30 else ">30"
        ] += 1
    w = world_counts(world)
    used = {
        "teams": w["Team.bin"],
        "players": w["Player.bin"],
        "coaches": w["Coach.bin"],
        "competitions": w["Competition.bin"],
        "regulations": w["CompetitionRegulation.bin"],
    }
    free = {k: CAPS[k] - used[k] for k in used}
    report = {
        "newlife": {
            "folder": nlf,
            "parts": parts,
            "total": total,
            "first": {
                "countries": len(first),
                "clubs": f_clubs,
                "new": f_new,
                "sizes": dict(bins),
            },
        },
        "world": {"path": world, "used": used, "free": free, "caps": CAPS},
    }
    if "--json" in a:
        print(json.dumps(report, indent=1, ensure_ascii=False))
        return 0
    print("NewLife: %s" % nlf)
    for p in parts:
        print(
            "  %-34s %5d clubs %7d players %4d coaches"
            % (p["part"], p["clubs"], p["players"], p["coaches"])
        )
    print(
        "  %-34s %5d clubs %7d players %4d coaches (%d clubs already in the game, %d new)"
        % (
            "TOTAL",
            total["clubs"],
            total["players"],
            total["coaches"],
            total["in_game"],
            total["clubs"] - total["in_game"],
        )
    )
    print(
        "\nfirst divisions (one league per country, by file order): %d countries, %d clubs, %d new"
        % (len(first), f_clubs, f_new)
    )
    print(
        "  sizes: "
        + ", ".join(
            "%s %d" % (k, bins[k]) for k in ("<10", "10-24", "25-30", ">30") if bins[k]
        )
    )
    print("\nworld: %s" % world)
    for k in ("teams", "players", "coaches", "competitions", "regulations"):
        print("  %-14s %6d of %6d used, %6d free" % (k, used[k], CAPS[k], free[k]))
    print(
        "  %-14s %6s of %6d (the Select Team layout)"
        % ("slots", "91 used", CAPS["slots"])
    )
    print("\nwhat fits")
    squads = free["players"] // 22
    print("  players: %d squads of 22, %d of 30" % (squads, free["players"] // 30))
    print(
        "  clubs:   %d more (a 20-club league needs 20, and its 22-man squads need 440 players)"
        % free["teams"]
    )
    print(
        "  a 20-club league: %s"
        % ("fits" if free["teams"] >= 20 and free["players"] >= 440 else "does not fit")
    )
    print(
        "  first divisions: need %d teams and about %d players"
        % (743 + f_new, f_new * 22)
    )
    print(
        "  full NewLife: %d new clubs, %d players; the team cap is %.1fx short, the player cap %.1fx"
        % (
            total["clubs"] - total["in_game"],
            total["players"],
            (total["clubs"] - total["in_game"]) / CAPS["teams"],
            total["players"] / CAPS["players"],
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
