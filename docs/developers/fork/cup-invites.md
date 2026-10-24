# Choosing a cup's first-round clubs: the "Other" groups and the game's own

2026-10-23. How to name the clubs that play a cup's first round one by one, instead of asking
each league for the club at a position. This is what lets a cup take clubs of the **Other**
groups (slots 69/71/73/75) and clubs **the game already has**.

## What the module already supported

`fl26swiss` reads `clubs=<team id>,...` on a `ccup` line into `c.opts.clubs`
(`fl26_swiss_ccup_opts`, `tools/native/fl26swiss.c`). In the fill (`ccup_fill`):

```
if (c->nc) {                                   /* invited by name */
  club = canon_club(full_club(c->clubs[i]));
  ...
  logf("fl26swiss:   cup %u entry %2u: team %u -> %08x (invited)", ...)
```

and the option reader refuses a list whose length is not the cup's field:

```
if (c->nc && c->nc != c->n) { "the invitations are dropped" }
```

`n` is the number of `entry=` pairs of the `ccup` line (or `groups * 4`). The Brazilian state
cups of the test world already use it with game clubs (`clubs=1247,137,...`).

## Three ways to set it

1. **In the world file**, by hand: add `clubs=<id>,<id>,...` to the `ccup` line.
2. **With the tool**, by name or id:

   ```
   python tools/cup_invites.py --base <pesdb> --worldfile <fl26world.txt> --cup "Campeonato Paulista" --show
   python tools/cup_invites.py --base <pesdb> --worldfile <fl26world.txt> --cup "Campeonato Paulista" \
       --clubs 1247,137,1255,1254,2459,5767,2465,Wydad
   ```

   Names are matched against `Team.bin +0x170` (the English name), case-insensitive; a name
   with more than one team is reported with its candidates. The tool refuses a list that is
   not exactly the cup's field size, which is the rule the module enforces.
3. **In a recipe**, so a Build reproduces it:

   ```json
   "cup_clubs": {
     "Campeonato Paulista": [1247, 137, 1255, 1254, 2459, 5767, 2465, 9030]
   }
   ```

   Values are a team id of the game or `"<league name>/<place>"` (the same reference syntax as
   `preseason_cups`). `leaguebuilder.home_cups` turns them into `opts.clubs`, which
   `ccup_options` writes as `clubs=`. The key is in `RECIPE_SETTINGS`, so it survives
   `recipe_from_plan` (editing a ready world and building again keeps it).

## Limits

- **Exact count.** A cup of 8 takes 8 names; a group cup of 32 takes 32. Anything else is
  dropped with a log line ("%u invited clubs for a field of %u").
- **The club must be known to the season.** `club_of_id` looks for the team id in the 600 live
  competition records (leagues and cups), and **falls back to the team record itself** when no
  competition holds it (`fl26swiss.c`, 2026-10-23) -- so an Other-pool club and a national team
  the game has not entered anywhere now resolve too. That fallback is in the source but **needs
  the DLL rebuilt** (zig); until then, a club in no competition is still dropped with
  "is not in any league of this season".
- **Cups, not the Club World Cup.** The CWC (`cwc` line) fills its 32 from the ranking quotas
  inside `fl26swiss` and has no invite list; adding one is a DLL change.
- A cup whose field is a league's clubs (`entry=<reg>:<position>`) stops following the league
  table once `clubs=` is there: the same clubs play every season.

## In the test copy

The Campeonato Paulista (cid 229, knockout 260, 8 clubs) now invites **Wydad Casablanca
(9030)** in place of São Bernardo, next to seven Brazilian clubs of the game. Its first round
is where to look for it.
