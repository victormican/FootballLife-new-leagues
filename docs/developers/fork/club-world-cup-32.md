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

## The four-year rule

`cwc_season()` reads the game's calendar year (`season_year()`) and plays when
`(year - year0) % every == 0`, 2026, 2030, 2034. `year=` is the first year; `every=` is the
period (4 by default). `cycle=<season>` forces one season (testing) and `every=1` plays every
season.

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
