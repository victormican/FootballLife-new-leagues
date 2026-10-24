r"""python tools/test_uecl_holder.py

The title holders' places in the UEFA access list (2026-10-23), as the game and this branch
have them:

  the Champions League winner  -> the next Champions League   (reg 4   0 -> comp 0)
  the Europa League winner     -> the next Champions League   (reg 6   0 -> comp 0)
  the Conference League winner -> the next Europa League      (reg 187 0 -> comp 1)

The user asked for the last one ("ganar la Conference League te clasifica para la Europa
League").  It is in the module's compiled table AND in the builder's shipped list, so a world
with uefa lines keeps it. This checks all three places in both tables and that uefa_places()
does not drop them when a world adds a place of its own (the Carabao Cup).

Read-only: the module source and fl26world's table. No game.
"""

import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.environ.pop("FL26_DIR", None)

import fl26world as W

N = 0
WANT = {(4, 0, 0), (6, 0, 0), (187, 0, 1)}


def ok(name, cond):
    global N
    N += 1
    print("%2d %s -- %s" % (N, "ok" if cond else "FAIL", name))
    if not cond:
        raise SystemExit(1)


shipped = {(e[0], e[1], e[2]) for e in W.SHIPPED_ACCESS}
ok("the builder's shipped list has the three holder places", WANT <= shipped)
ok(
    "the Conference League winner goes to the Europa League (reg 187, comp 1)",
    (187, 0, 1) in shipped,
)

src = io.open(
    os.path.join(HERE, "native", "fl26swiss.c"), encoding="utf-8", errors="replace"
).read()
for token, what in ((r"\{\s*R_UCLKO\s*,\s*0\s*,\s*UCL\s*,", "Champions League holder to the Champions League"),
                    (r"\{\s*R_UELKO\s*,\s*0\s*,\s*UCL\s*,", "Europa League holder to the Champions League"),
                    (r"\{\s*UECL_KO\s*,\s*0\s*,\s*UEL\s*,", "Conference League holder to the Europa League")):
    ok("the module's compiled list has the " + what, re.search(token, src) is not None)

# adding a world's own place keeps the shipped ones
uefa, _over = W.uefa_places([[900, 0, 2, 17]], (), True)
got = {(e[0], e[1], e[2]) for e in uefa}
ok("a world's own place keeps the three holder places", WANT <= got)
ok("... and adds the world's place", (900, 0, 2) in got)

# and a world whose own place is the Conference League winner to the Europa League reads the same
uefa, _over = W.uefa_places([[187, 0, 1, 17]], (), True)
ok(
    "a world can list the Conference League holder place itself",
    (187, 0, 1) in {(e[0], e[1], e[2]) for e in uefa},
)

print("test_uecl_holder: all %d passed" % N)
