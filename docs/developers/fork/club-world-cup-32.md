# Club World Cup with 32 clubs, as a competition of its own

The 2025 format — 32 clubs, eight groups of four played once, then a single-match knockout of
sixteen — is built as a **second competition**, beside the game's annual four-club Club World
Cup (competition 1, which stays untouched). It plays every four years from 2026.

## What the build writes

`tools/mkcwc.py` (called by the League Builder when the recipe has `club_world_cup`):

- a **competition row** copied from competition 1 with a free competition id (from 130 up);
- the **group stage**: the Copa Libertadores group stage (32 clubs, eight replicas) with one
  round per group, replicas at `<reg> + 1024 * (group + 1)`;
- the **knockout**: the shipped competition 1's single-match template with sixteen clubs;
- all twenty name slots copied from the shipped Club World Cup regulation.

The ids are chosen against the world's own tables, so no league or cup id is taken. They are
kept in the world's `leaguebuilder-plan.json` and handed back on a rebuild.

## What the module does

`fl26swiss.dll` reads the world file's line

```
cwc <group stage reg> <knockout reg> year=2026 every=4 host=6
```

`fl26_swiss_cwc` takes the ids and the frequency; `fl26_swiss_cwc_access` takes the ranking (
one `(regulation, confederation)` pair per top division of the world file; the DLL adds the
game's own top flights).

When the Champions League play-off progresses (`r == 2`), in a season the rule says plays:

1. asks each league's final table (kept at the July teardown, the live table, or a table
   counted from the matches) for its clubs;
2. fills the FIFA quotas — **UEFA 12, CONMEBOL 6, AFC 4, CAF 4, CONCACAF 4, OFC 1, host 1** —
   champions first, then runners-up, league by league in the ranking order;
3. drops a third club of the same country (`CWC_PER_COUNTRY 2`);
4. sets the field, runs the game's own group draw, hands the eight groups to `register_all`;
5. when every group is over, puts the winners and runners-up into the knockout in the 2025
   bracket order and starts it.

Dates are borrowed from the World Cup's shapes and moved to `CWC_GROUP_DAYS` / `CWC_KO_DAYS`.

## The confederations' champions come first

The user's rule (2026-10-24): the places are defined by each confederation's competitions. With
the world's own ranking (`fl26_swiss_cwc_access`) the quotas were filled from the leagues' final
tables only; now the world names the cups whose winners take the first places of their
confederation's quota:

```
cwcchamp 4:2,6:2,187:2,10:4,16:3,319:6,320:5,322:3,324:4,325:6,326:7,328:3
```

Pairs of `<knockout regulation>:<confederation>` (2 UEFA, 3 AFC, 4 CONMEBOL, 5 CAF, 6 CONCACAF,
7 OFC). The shipped champions' knockouts are always there -- the Champions League (4), the
Europa League (6), the Conference League (187), the Libertadores (10) and the AFC Champions
League (16) -- and the Builder adds the continental cups it makes (CAF Champions League and
Confederation Cup, AFC Champions League Two and Challenge League, Copa Sudamericana, CONCACAF
Champions Cup, Copa Centroamericana, OFC Champions League). `leaguebuilder.cwc_champs` is what
writes the line, and `fl26_swiss_cwc_champs` is the export that reads it.

The fill adds, for each confederation and before any league place, `cup_winner(reg)` of its
cups (the final of the season just ended), so a CAF Champions League winner is in the Cup even
if its league placed it fifth. The quotas are unchanged: UEFA 12, CONMEBOL 6, AFC 4, CAF 4,
CONCACAF 4, OFC 1, plus the host's one; a country never sends more than two clubs, and if a
confederation has fewer champions than places the rest comes from the leagues as before.

## The four-year rule

`cwc_season()` reads the game's calendar year (`season_year()`) and plays when
`(year - year0) % every == 0`, 2026, 2030, 2034. `year=` is the first year; `every=` is the
period (4 by default). `cycle=<season>` forces one season (testing) and `every=1` plays every
season. The Builder writes `every=4` unless the recipe asks otherwise; the `_FL26All` test
world asks `every: 1` so the format can be seen in the first career.

## The ranking

The world file supplies the ranking: every top division, in the order the League Builder lists
it (the UEFA ranking and the South American places use the same order). The DLL adds the game's
own top flights (Premier League, LaLiga, ...), so a world that only adds lower divisions still
asks the big five. This is the same table the continental cups use when
`continental_rank: true`.

## Limits

- The knockout id must be free; `mkcwc.py` picks one and never uses 255 (the "no league"
  sentinel).
- The group replicas are ids above 1023; `fl26swiss` intercepts their dates, so the date stub's
  1..255 table is not involved.
- A world without the rows is left alone: `cwc_world()` checks the knockout and the first and
  last replica.
