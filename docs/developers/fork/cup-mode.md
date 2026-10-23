# Cup mode: play the cups a world builds

Kick Off > Cup lists the competitions the game ships. A world's own competitions — the
continental cups of `mkccup.py` (`ccup` lines), the Copa Centroamericana, the league and
pre-season cups — are in the live competition table, but the Cup-select menu builds its list from
the shipped categories, so they were not offered. Since 2026-10-23 they are added to that list.

## How the list works

- The Cup-select menu is `MenuModeCupSelect` (vtable `0x142692c40`); the only Cup flow enters it.
  Master League uses `MenuModeCompeSelect`, a different menu.
- Its init is wrapped by `fl26swiss.dll` (`CUPSEL_VT_RVA 0x2692d18`,
  `CUPSEL_INIT_RVA 0xb1c990`). The list is at `self+0x90` (begin) and `self+0x98` (end), 12-byte
  items with the competition id at `+0`. `self+0xa0` is the end of the storage.
- Before the menu counts its choices, the handler:
  1. removes every competition whose group phase holds more than 32 clubs (GitHub #100: the 36-club
     Champions/Europa/Conference league phases cannot be drawn by Cup mode);
  2. **appends the world's own cups**, one 12-byte item per competition id, copied from an existing
     item so the name/logo lookup has a template. It only appends while the vector has room; the
     log says `Cup mode -- N world cup(s) added, all in` or `no room for the rest`.
- The ids come from the `ccup` lines: `leaguebuilder.ccup_options` writes `cid=<competition id>`
  on every cup line, `fl26swiss.lua` collects them and calls `fl26_swiss_cup_cids`.

## The field Cup mode plays

`mkccup.py` writes `CompetitionEntry` rows: the clubs at the entry positions, a fixed field taken
from the world's leagues at Build time. Cup mode uses those entries and the competition's own
shape (groups of four + knockout, or a straight knockout), so the cup is playable without the
Master League season.

The **Club World Cup** is not in this list yet: `mkcwc.py` writes no entries on purpose (its field
is chosen from league tables by `fl26swiss` in a Master League season), so Cup mode would open an
empty cup. Adding a fixed 32-club entry list for Cup mode is the next step if it is wanted.

## Master League

The same cups are already in a Master League season: the world file's `ccup` lines make
`fl26swiss` fill them from the league tables when the Champions League play-off progresses, draw
the groups, start the knockout and date both. Competition Info and the schedule show them by
their competition id. They are not in Select Team (they are cups, not leagues); a career does not
start in one.

## Test

1. Build a small world with one of the cups, for example the CAF/OFC/CONCACAF recipe of
   [limits-and-formats.md](limits-and-formats.md), into the test copy.
2. Switch the copy to that world (`python tools/leaguebuilder.py on <world> --game <copy>` or Mod
   Studio), start the game, and open **Kick Off > Cup**.
3. The cup should be in the list next to the shipped ones. Pick it, pick a club, and play the
   first match.
4. The `sider.log` lines to check:
   - `fl26swiss: world file -- N cup(s) for Kick Off > Cup, M taken`
   - `fl26swiss: Cup mode -- N world cup(s) added, all in (list X of Y)`
   - if it says `no room for the rest`, the Cup vector is full and the remaining cups are not
     offered; the log gives the size.
