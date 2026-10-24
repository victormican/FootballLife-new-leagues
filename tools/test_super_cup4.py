r"""python tools/test_super_cup4.py

The four-club super cup (Supercopa de España, Supercoppa Italiana):

  - the super cup's regulation keeps its id and cid and only its bracket grows to four;
  - the world gets one `ccup` line (league 1-2, cup winner with a league fallback, league 3rd)
    and one `cupdays` line, dated in January and filled at the start of the season;
  - a second run replaces the lines instead of adding a second pair;
  - a regulation that is not a knockout, or a bracket already bigger than four, is refused.

A fake world folder in a temp directory. No game.
"""

import io
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.environ.pop("FL26_DIR", None)

import pesdb
import mkleague as M
import super_cup4 as S

N = 0


def ok(name, cond):
    global N
    N += 1
    print("%2d %s -- %s" % (N, "ok" if cond else "FAIL", name))
    if not cond:
        raise SystemExit(1)


def regulation(rid, cid, kind, teams, name):
    g = bytearray(M.REG)
    g[M.R_ID : M.R_ID + 2] = rid.to_bytes(2, "little")
    g[M.R_CID] = cid
    g[M.R_TYPE] = kind
    g[M.R_TEAMS] = (g[M.R_TEAMS] & 0xC0) | teams
    b = name.encode("utf-8")
    g[M.R_NAME : M.R_NAME + len(b)] = b
    return g


T = tempfile.mkdtemp(prefix="sc4-")
DB = os.path.join(T, "pesdb")
os.makedirs(DB)
WF = os.path.join(T, "fl26world.txt")
regs = bytearray()
regs += regulation(19, 11, 4, 20, "LaLiga")
regs += regulation(25, 17, 3, 20, "Copa del Rey")
regs += regulation(87, 74, 3, 2, "Supercopa de Espa\u00f1a")
open(os.path.join(DB, "CompetitionRegulation.bin"), "wb").write(
    pesdb.wesys_pack(bytes(regs))
)
io.open(WF, "w", encoding="utf-8", newline="\n").write("league 19 cid=11 name=LaLiga\n")


def run(name=None, **kw):
    argv = ["super_cup4.py", "--base", DB, "--worldfile", WF,
            "--league", kw.get("league", "19"), "--cup", kw.get("cup", "25"),
            "--super", kw.get("super", "87")]
    if name:
        argv += ["--name", name]
    if kw.get("dry"):
        argv.append("--dry")
    if "days" in kw:
        argv += ["--days", kw["days"]]
    old = sys.argv
    sys.argv = argv
    try:
        return S.main()
    finally:
        sys.argv = old


def text():
    return io.open(WF, encoding="utf-8").read()


def bracket():
    raw = pesdb.wesys_unpack(
        open(os.path.join(DB, "CompetitionRegulation.bin"), "rb").read()
    )
    for i in range(0, len(raw), M.REG):
        if int.from_bytes(raw[i + M.R_ID : i + M.R_ID + 2], "little") == 87:
            return raw[i + M.R_TEAMS] & 0x3F
    return None


ok(
    "the dry run changes nothing",
    run("Test", dry=True) == 0 and bracket() == 2 and "ccup" not in text(),
)
ok(
    "the regulation keeps its id and grows to four",
    run("Test") == 0 and bracket() == 4,
)
line = [l for l in text().splitlines() if l.startswith("ccup ")]
ok(
    "one ccup line, with the four places",
    len(line) == 1 and "entry=19:1,19:2,25:0,19:3" in line[0] and "cid=74" in line[0],
)
ok(
    "the cup winner falls back to the league, and the 3rd to the 4th",
    "alt=2:19:3,3:19:4" in line[0],
)
ok("its rounds are the two January days", "days=7,11" in line[0])
ok("it is filled at the start of the season", "fill=190" in line[0])
ok("the cupdays line tells the leagues the days", "cupdays 87 7 11" in text())
run("Test")
line2 = [l for l in text().splitlines() if l.startswith("ccup ")]
days2 = [l for l in text().splitlines() if l.startswith("cupdays 87 ")]
ok("a second run replaces, not duplicates", len(line2) == 1 and len(days2) == 1)
ok("the league line is untouched", "league 19 cid=11 name=LaLiga" in text())

# the refusals
ok("a smaller bracket is refused", run("Test", days="7") == 1)
raw = bytearray(
    pesdb.wesys_unpack(open(os.path.join(DB, "CompetitionRegulation.bin"), "rb").read())
)
for i in range(0, len(raw), M.REG):
    if int.from_bytes(raw[i + M.R_ID : i + M.R_ID + 2], "little") == 19:
        raw[i + M.R_TYPE] = 3
open(os.path.join(DB, "CompetitionRegulation.bin"), "wb").write(
    pesdb.wesys_pack(bytes(raw))
)
ok(
    "a regulation that is not a knockout is refused",
    run("Test", super="19") == 1,
)

shutil.rmtree(T, ignore_errors=True)
print("test_super_cup4: all %d passed" % N)
