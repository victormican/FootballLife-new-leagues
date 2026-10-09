"""python tools/test_club_world_cup.py [tables folder]

`club_world_cup: true` in a recipe reshapes the shipped Club World Cup into the 2025 format,
through mkcwc.py, as a Build step.

Two things had to hold for it to be safe, and neither is obvious from mkcwc.py alone:

  - the knockout's regulation id has to be the one fl26swiss.c has compiled in as CWC_KO, or
    the DLL looks for a regulation the world does not have and the knockout rows sit there
    unread. So a recipe asking for another id is refused, and free_comp_ids keeps that id out of
    the pool the continental cups draw from, whether or not the recipe asks for the cup.
  - it is the game's own competition 1, not one of ours: it needs no `ccup` line and none of
    the continental cups' ids, so it must not take any. The build runs it after them.

With a tables folder it also builds a world and reads the rows back, which is the only place
the eight replicas and the one round can be seen.
"""

import json, os, shutil, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import leaguebuilder as B
import mkleague as M
import mkcwc

N = 0


def ok(name, cond):
    global N
    assert cond, name
    N += 1
    print("ok %d - %s" % (N, name))


def plan(ask):
    return B.club_world_cup_plan({"club_world_cup": ask})


def refuses(ask, what):
    try:
        plan(ask)
    except B.BuildError as e:
        ok(what, "club_world_cup" in str(e))
    else:
        ok(what, False)


def regulations(db):
    regs = M.load(db, "CompetitionRegulation.bin")
    out = {}
    for i in range(len(regs) // M.REG):
        o = i * M.REG
        out[int.from_bytes(regs[o + 2 : o + 4], "little")] = (
            regs[o + M.R_CID],
            regs[o + M.R_TYPE],
            regs[o + 0x0A],
            regs[o + M.R_TEAMS] & 0x3F,
            (int.from_bytes(regs[o + 0x10 : o + 0x14], "little") >> 12) & 7,
            int.from_bytes(regs[o + 0x06 : o + 0x08], "little"),
        )
    return out


def build(tmp, base, recipe):
    root = os.path.join(tmp, "game")
    f = os.path.join(tmp, "recipe.json")
    open(f, "w", encoding="utf-8").write(json.dumps(recipe))
    B.build(B.plan(B.load_recipe(f), base), base, root, log=lambda s: None)
    return os.path.join(
        root, "SiderAddons", "livecpk", recipe["world"], "common", "etc", "pesdb"
    )


LEAGUE = {"name": "Checks CWC Test", "country": "Albania", "clubs": 16, "legs": 2}


def main():
    # what turns it on, and what does not
    ok("true: the knockout is the id the module has", plan(True)["ko"] == mkcwc.KO)
    ok(
        "true: every season, which is what the game's own does",
        plan(True)["cycle"] == 0,
    )
    ok("a cycle: that season and no other", plan({"cycle": 3})["cycle"] == 3)
    ok("a cycle of 0 means every season", plan({"cycle": 0})["cycle"] == 0)
    refuses({"cycle": -1}, "a negative cycle is refused")
    refuses({"cycle": 101}, "a cycle past 100 is refused")
    refuses({"cycle": "third"}, "a cycle that is not a number is refused")
    # the quadrennial rule, counted on the game's calendar year rather than on a tally of days
    ok("a year: the real four-year rule", plan({"year": 2026})["year"] == 2026)
    refuses({"year": 1989}, "a year before 1990 is refused")
    refuses({"year": 1899}, "a year the game's date could not hold is refused")
    refuses({"year": 2201}, "a year past 2200 is refused")
    refuses({"year": "two thousand"}, "a year that is not a number is refused")
    refuses({"year": 2026, "cycle": 3}, "a year and a cycle together is refused")
    refuses({"year": 2026, "every": 4}, "a year and every together is refused")
    ok(
        '{"ko": 200}: the same id, asked for by name',
        plan({"ko": mkcwc.KO})["ko"] == mkcwc.KO,
    )
    ok("absent: off", plan(None) is None)
    ok("false: off", plan(False) is None)
    ok("an empty object: off", plan({}) is None)

    # what must not be accepted
    refuses(
        {"ko": mkcwc.KO + 1},
        "another regulation id is refused, and the module is named",
    )
    refuses({"ko": "x"}, '"ko" that is not a number is refused')
    refuses("yes", "a string where true or an object was wanted is refused")
    refuses(5, "a number where true or an object was wanted is refused")

    # the id stays out of the continental cups' pool, cup or no cup
    base = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("FL26_PESDB")
    if not base or not os.path.isdir(base):
        print("skip - no tables folder, the build checks need the game's tables")
    else:
        ids = B.free_comp_ids(base)[1]
        ok("the Club World Cup's id is never handed to a cup", mkcwc.KO not in ids)

        tmp = tempfile.mkdtemp()
        try:
            # off: competition 1 is left as shipped, one row, a four-club knockout
            db = build(tmp, base, {"world": "_FL26CwcOff", "leagues": [LEAGUE]})
            shipped = [r for r, v in regulations(db).items() if v[0] == 1]
            ok("off: competition 1 keeps its one shipped row", len(shipped) == 1)

            # on: eight groups of four played once, then a knockout of sixteen
            db = build(
                tmp,
                base,
                {"world": "_FL26CwcOn", "club_world_cup": True, "leagues": [LEAGUE]},
            )
            rows = regulations(db)
            # the ten ids are mkcwc's own choice, so they are read out of a second build rather
            # than guessed: what matters is that the rows it wrote are the ones it named
            c_row, c_regs = mkcwc.build(base, None, None, mkcwc.KO, None)
            cid = c_row[M.CID_OFF]
            master = mkcwc.rid(c_regs[0])
            mine = {r: v for r, v in rows.items() if v[0] == cid}
            ok("on: ten new regulation rows", len(mine) == 10)
            ok(
                "on: they are the ids mkcwc named",
                sorted(mine) == sorted(mkcwc.rid(g) for g in c_regs),
            )
            ok(
                "on: the group stage is 32 clubs in 8 groups, played once round",
                mine[master][1] == 2
                and mine[master][2] == mkcwc.NO_GROUP
                and mine[master][3:5] == (32, 1),
            )
            ok(
                "on: the replicas sit at +1024 a group, all pointing back at the master",
                sorted(r for r in mine if r > 1024)
                == [mkcwc.rep_id(master, g) for g in range(mkcwc.GROUPS)]
                and all(
                    mine[mkcwc.rep_id(master, g)][5] == master
                    for g in range(mkcwc.GROUPS)
                ),
            )
            ok(
                "on: the knockout is 16 clubs and is a single-match knockout",
                mine[mkcwc.KO][1] == 3 and mine[mkcwc.KO][3] == 16,
            )
            ok(
                "on: every new row hangs off the new competition",
                cid != mkcwc.CWC_CID and len({v[0] for v in mine.values()}) == 1,
            )
            ok(
                "on: the game's own Club World Cup is untouched, still its one row",
                len([r for r, v in rows.items() if v[0] == mkcwc.CWC_CID]) == 1,
            )
            comp = M.load(db, "Competition.bin")
            n_on = len({comp[i + M.CID_OFF] for i in range(0, len(comp), M.COMP)})
            off_db = build(tmp, base, {"world": "_FL26CwcCount", "leagues": [LEAGUE]})
            off_comp = M.load(off_db, "Competition.bin")
            n_off = len(
                {off_comp[i + M.CID_OFF] for i in range(0, len(off_comp), M.COMP)}
            )
            ok(
                "on: exactly one competition more than the same world without it",
                n_on == n_off + 1,
            )
            ok(
                "and it carries the Club World Cup's own code, not a placeholder",
                bytes(c_row[M.CODE_OFF : M.CODE_OFF + 8]) == b"FIFA_CLU",
            )
            ok(
                "on: no other competition lost a row",
                len(rows)
                > len(
                    regulations(
                        build(tmp, base, {"world": "_FL26CwcOff2", "leagues": [LEAGUE]})
                    )
                ),
            )
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    print("1..%d" % N)


if __name__ == "__main__":
    main()
