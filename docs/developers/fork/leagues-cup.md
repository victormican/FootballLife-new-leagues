# Leagues Cup (MLS v Liga MX)

Recipe key `leagues_cup: true` (or `{"mx": "<league name>"}`). The League Builder adds a
competition 17, `FL_LEAGUESCUP`, to the continental cups of the world:

- **32 clubs**: the first 16 of MLS (shipped regulation 51) and the first 16 of the Mexican league
  of the recipe (Mexico has no shipped league in this game; the world adds one, for example
  "Mexican First Division" on regulation 223 in the 91-league test world);
- **eight groups of four**, each group two MLS and two Liga MX clubs, home and away;
- **a knockout of sixteen**, the group winners and runners-up;
- the world file line `ccup <groups> ko=<knockout> groups=8 entry=... cid=<competition> name=Leagues Cup`.

`mkccup.py` writes the entries (the clubs at those league positions) and the two regulation
shapes; `fl26swiss` fills the cup from the league tables at the Champions League play-off,
draws the groups, starts the knockout and dates both. The cup is in **Kick Off > Cup** too
(`cid=` on the `ccup` line; see [cup-mode.md](cup-mode.md)).

## What the real 2025 cup does, and what this does not

The 2025 Leagues Cup had **36 clubs** (18 MLS + 18 Liga MX). Phase One was not a group stage:
every club played three matches against clubs of the other league, and the **top four of each
league** went to the quarter-finals; the semifinals, third-place match and final followed, all
single matches. The top three qualified for the CONCACAF Champions Cup.

The engine plays groups of four, not two 18-club tables with three cross-league matches, so this
build is the closest supported shape: 32 clubs, eight groups, a knockout of sixteen. It keeps
the MLS v Liga MX mix in every group and the single-match knockout, and it fills from the two
leagues' own positions. The exact Phase One needs a new phase shape (two tables, three cross
matches); it is not implemented.

## Test

In the 91-league test world the cup is already added by hand:

- competition **228**, group stage **258**, knockout **259**;
- entries `51:1..16` (MLS) and `223:1..16` (Mexican First Division);
- the `ccup` line is in `SiderAddons\modules\fl26world.txt` and in the world folder.

Start the game, open **Kick Off > Cup**, pick **Leagues Cup**, pick a club and play. In a Master
League career it is filled and played like the other continental cups.

For a new Build, add a Mexican league of 18 clubs to the recipe and `"leagues_cup": true`; the
Build logs `Leagues Cup: competition N, 32 clubs, groups X, knockout Y`.
