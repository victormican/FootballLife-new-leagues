# AFC Champions League composition, and duplicate Asian clubs

2026-10-23. What fills the AFC competitions, where a club can enter twice, and the checks added
to find it.

## The three Asian competitions

| competition | regulation | who fills it |
|---|---|---|
| **AFC Champions League** (the game's own, competition 8) | group stage 15, knockout 16 | the game, from its rights table; `fl26swiss` replaces the pool clubs (`POOL_ASIA`, slot 70) with the world's AFC places (`AFCL` in the access list) |
| **AFC Champions League Two** (a cup of ours, `fl26world.CCUPS` number 8) | a copy of the Libertadores group stage + the Europa League knockout | `fl26swiss` from league tables |
| **AFC Challenge League** (a cup of ours, number 15) | the same shapes | `fl26swiss` from league tables |

## Where a club could enter twice

1. **The game's AFC Champions League and our AFC Champions League Two.** The game's field is set
   on day 0; our cup is filled at the Champions League play-off (`r == 2`). `ccup_taken` reads
   the live group stage (reg 15, and the Libertadores' 8/9) and refuses a club already there.
   If the live record is still empty at that moment, the check sees nothing and the club enters
   both. The builder now also holds the places of cups 8 and 15 against the **entry list on
   disk** (`CompetitionEntry` of competition 8) and drops a place whose club is already in it
   (`leaguebuilder.drop_game_places`); the same for the Sudamericana against the Libertadores
   (competition 5).
2. **A cup winner and a league position.** Position 0 is the national cup winner, a different
   club from the league position; `europe_problems` allows both. At runtime `ccup_taken` is the
   check that stops the same club entering twice; the builder cannot always tell (the cup may
   not have a winner yet).
3. **The access list itself.** `cont_build` keeps one list for the three places (Libertadores,
   its qualifying round, AFC Champions League) and skips a club already in `used`, so the same
   club cannot be given two places of the same competition. The builder's `europe_problems`
   refuses the same position twice in a league.
4. **The Club World Cup.** Its quota generator (`cwc_add`) already skips a club already in the
   field, so an Asian champion cannot be added twice.

## The diagnostics

The module now counts duplicates in every field it touches:

- `fl26swiss: AFC Champions League (reg 15, ...) -- ... N duplicate(s)` — the game's own field
  after the pool swaps;
- `fl26swiss: cup 258 -- N duplicate club(s) in its field of M` — one of our cups after filling.

Zero is the normal answer. A non-zero one says which field holds the same club twice, and the
lines above it (`cup N entry ...` / `AFC Champions League: reg ... -> ...`) say which places
produced it.

## What to send

If the duplication is still seen in the game, the `sider.log` lines around the first
`AFC Champions League` of the season:

```
fl26swiss: AFC Champions League (reg 15, ...) -- day ...: 32 clubs, ...
fl26swiss:   AFC Champions League: reg ... position ... -> ...
fl26swiss: cup ... entry ... (AFC Champions League Two)
fl26swiss: cup ... -- ... duplicate club(s)
```

With those, the place that produced the duplicate can be named exactly: a pool club, a league
position, a cup winner, or a place moved up by `ccup_short`.
