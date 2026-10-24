r"""python tools/test_cup_invites.py

The two ways to name a cup's first-round clubs (2026-10-23):

  - `cup_invites.py` on a world file: a team id or a name of Team.bin, the exact field size,
    no repeats, no unknown club, and nothing written when the list is refused;
  - `home_cups` with the recipe's `cup_clubs`: team ids and "<league>/<place>" references,
    duplicates and a wrong count refused, and the ids turned into `opts.clubs` (which
    `ccup_options` writes as `clubs=`).

A fake world folder in a temp directory. No game.
"""

import io
import json
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.environ.pop("FL26_DIR", None)

import pesdb
import leaguebuilder as B

N = 0


def ok(name, cond):
    global N
    N += 1
    print("%2d %s -- %s" % (N, "ok" if cond else "FAIL", name))
    if not cond:
        raise SystemExit(1)


T = tempfile.mkdtemp(prefix="cupinv-")
DB = os.path.join(T, "pesdb")
os.makedirs(DB)
WF = os.path.join(T, "fl26world.txt")

TEAMS = {
    1247: "SC Corinthians",
    137: "SE Palmeiras",
    1255: "Sao Paulo FC",
    1254: "Santos FC",
    2459: "Red Bull Bragantino",
    5767: "Mirassol FC",
    2465: "AA Ponte Preta",
    9030: "Wydad Casablanca",
    5909: "Sao Bernardo FC",
}
raw = bytearray()
for tid, name in TEAMS.items():
    row = bytearray(1532)
    row[8:12] = tid.to_bytes(4, "little")
    b = name.encode("utf-8")[:69]
    row[0x170 : 0x170 + len(b)] = b
    raw += row
open(os.path.join(DB, "Team.bin"), "wb").write(pesdb.wesys_pack(bytes(raw)))

LINE = (
    "ccup 260 ko=260 groups=0 entry=0:1247,0:137,0:1255,0:1254,0:2459,0:5767,0:2465,0:5909 "
    "cid=229 fill=15 national=1 days=20,27,34 clubs=1247,137,1255,1254,2459,5767,2465,5909 "
    "like=23 name=Campeonato Paulista"
)
io.open(WF, "w", encoding="utf-8", newline="\n").write(LINE + "\n")


def run(*args):
    argv = sys.argv
    sys.argv = ["cup_invites.py", "--base", DB, "--worldfile", WF] + list(args)
    try:
        return CUP.main()
    finally:
        sys.argv = argv


def text():
    return io.open(WF, encoding="utf-8").read()


import cup_invites as CUP

ok(
    "the cup is read with its eight clubs",
    run("--cup", "Campeonato Paulista", "--show") == 0,
)
ok(
    "a name of Team.bin is resolved and written",
    run("--cup", "229", "--clubs", "1247,137,1255,1254,2459,5767,2465,Wydad") == 0
    and "clubs=1247,137,1255,1254,2459,5767,2465,9030" in text(),
)
ok(
    "nothing else in the line changed",
    text().strip().startswith("ccup 260 ko=260")
    and "name=Campeonato Paulista" in text(),
)

before = text()
ok("a short list is refused", run("--cup", "229", "--clubs", "1247,137") == 1)
ok(
    "an unknown name is refused",
    run("--cup", "229", "--clubs", "1247,137,1255,1254,2459,5767,2465,ZZZ") == 1,
)
ok(
    "a repeated club is refused",
    run("--cup", "229", "--clubs", "1247,1247,1255,1254,2459,5767,2465,9030") == 1,
)
ok("a name that is a club already in the list is refused",
   run("--cup", "229", "--clubs", "1247,137,1255,1254,2459,5767,2465,Santos") == 1)
ok("a name that matches more than one club is refused",
   run("--cup", "229", "--clubs", "1247,137,1255,1254,2459,5767,2465,FC") == 1)
ok("a refused list leaves the file as it was", text() == before)
ok("a cup that is not there is reported", run("--cup", "No Such Cup") == 1)

# ---- the recipe key
LEAGUES = [
    {
        "rid": 317,
        "name": "Generic League 01",
        "clubs": 10,
        "country": 200,
        "region": 29,
        "teams": list(range(1000, 1010)),
    },
    {
        "rid": 318,
        "name": "Generic League 02",
        "clubs": 10,
        "country": 200,
        "region": 29,
        "teams": list(range(1010, 1020)),
    },
]


def plan(cup_clubs):
    return {
        "leagues": LEAGUES,
        "settings": {"cup_clubs": cup_clubs} if cup_clubs is not None else {},
        "home_cups": [
            {
                "name": "Test Cup",
                "code": "FL_T1",
                "conf": 2,
                "country": 200,
                "region": 29,
                "groups": 0,
                "entry": [(317, 1), (317, 2), (317, 3), (317, 4)],
                "opts": {"fill": 15, "national": 1, "days": []},
            }
        ],
    }


out = B.home_cups(plan({"Test Cup": [9030, 1001, 1002, 1003]}), {200: 2})
ok(
    "cup_clubs with team ids reaches opts.clubs",
    out[0]["refs"] == [9030, 1001, 1002, 1003]
    and out[0]["opts"]["clubs"] == [9030, 1001, 1002, 1003],
)
out = B.home_cups(
    plan({"Test Cup": ["Generic League 02/3", 9030, 1001, 1002]}), {200: 2}
)
ok(
    "cup_clubs takes a league/place reference",
    out[0]["opts"]["clubs"] == [1013, 9030, 1001, 1002],
)
out = B.home_cups(plan({}), {200: 2})
ok("without cup_clubs the cup keeps its league positions", "refs" not in out[0])
for bad, why in (
    ([9030, 1001], "two clubs for a field of four"),
    ([9030, 9030, 1001, 1002], "the same club twice"),
    (["No League/0", 1001, 1002, 1003], "a league that is not in the recipe"),
):
    try:
        B.home_cups(plan({"Test Cup": bad}), {200: 2})
        ok("refused: " + why, False)
    except (B.BuildError, SystemExit):
        ok("refused: " + why, True)

line = B.ccup_options(
    "ccup 258 ko=259 groups=8 entry=0:1,0:2,0:3,0:4 cid=228 name=Leagues Cup",
    {
        "cid": 228,
        "opts": {"fill": 15, "national": 1, "days": [20], "clubs": [9030, 1247]},
    },
)
ok(
    "ccup_options writes clubs=",
    "clubs=9030,1247" in line and "name=Leagues Cup" in line,
)

shutil.rmtree(T, ignore_errors=True)
print("test_cup_invites: all %d passed" % N)
