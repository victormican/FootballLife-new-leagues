# The confederations' cups, their recopas, and the two world competitions

2026-10-23. What a build can put under each confederation, what a "recopa" is in this engine,
and what still stands between the continental champions and the Intercontinental and the
32-club Club World Cup.

## What exists, confederation by confederation

| confederation | cups | recopa / super cup |
|---|---|---|
| UEFA | Champions League, Europa League, Conference League (the game's own, reshaped to the league phase) | UEFA Super Cup (the game's own, cid 4 / reg 7) |
| CONMEBOL | Copa Libertadores (the game's own: qualifiers reg 8, groups reg 9, knockout reg 10); Copa Sudamericana (built, `ccup` number 9) | **Recopa Sudamericana** (built, `recopa_sudamericana: true`) |
| CAF | CAF Champions League and Confederation Cup (built, numbers 6 and 7) | CAF Super Cup (built, `caf_super_cup`, default on) |
| AFC | AFC Champions League (the game's own, cid 8); AFC Champions League Two and Challenge League (built, numbers 8 and 15) | -- (none in real life) |
| CONCACAF | CONCACAF Champions Cup (built, number 13); Copa Centroamericana (built, number 16) | -- |
| OFC | OFC Champions League (built, number 14) | -- |
| FIFA | Club World Cup 32 (our own, `club_world_cup`) | Intercontinental -- **not built** |

All the built ones are `ccup` lines of the world file; the module `fl26swiss` fills them,
dates them and runs them (`fl26_swiss_ccup`).

## How a place from a cup is written

A `ccup` entry is `<regulation>:<position>`. Position `0` is **the winner of that cup**:

```
entry=10:0,318:0       the winner of reg 10 (the Libertadores' knockout) and of reg 318
                       (the Sudamericana's knockout this build made)
alt=2:19:3,3:19:4      the fallbacks, entry by entry, when that club is already in the field
```

That is the whole mechanism the recopas and the world competitions need: a place that is "the
champion of X" is just `X:0`, and `alt=` gives the next club of a league when the champion
already qualified another way.

## The Recopa Sudamericana

`recopa_sudamericana: true` in a recipe adds a two-club cup (number 18, code `FL_RECOPA`):

```
ccup 319 ko=319 groups=0 entry=10:0,318:0 cid=132 fill=15 national=1 days=50,53,56 \
     name=Recopa Sudamericana
```

- entries: the Libertadores knockout's winner (reg 10, the game's own row) and the
  Sudamericana's knockout (the cup this build made, resolved by number);
- filled on day 15 (mid-January), when both finals (November) are known, and played in late
  February (`days=50,53,56`);
- `national=1`, so a club that also plays the Libertadores this season is allowed;
- built only when the world has a Sudamericana; otherwise the build says so in its notes.

`regress018/recopa` builds it and passes the four build checks. It needs a free competition
id, which a fresh world has and the test copy does not (255 of 255 used).

## What is missing for the two world competitions

**The Intercontinental (annual).** It is a cup whose entries are the continental champions:
UEFA's and CONMEBOL's in the final, the other four in the earlier rounds (the 2024 format), or
the classic two-club Europe v South America. In this engine that is another `ccup` of six
clubs (bracket 6, byes for the top two) with `entry=<UCL knockout>:0,<Libertadores knockout>:0,
<caf>:0,<afc>:0,<concacaf>:0,<ofc>:0`. It is not built: it needs its own competition id (free
in a fresh world), a name and a date, and the same "champions only" gate as the recopas. The
pieces are all there; what is not is a recipe key.

**The 32-club Club World Cup (every four years).** `fl26swiss` fills it today from the world's
**league ranking** (UEFA 12, CONMEBOL 6, AFC 4, CAF 4, CONCACAF 4, OFC 1, host 1,
`club-world-cup-32.md`). To take the continental champions first -- the user's rule -- the
module has to read `cup_winner(reg)` of each continental knockout and put those clubs at the
top of their confederation's quota before filling the rest from the tables. That is a change
inside `fl26swiss.c` (`cwc_field`), which needs a compiler: the repository builds its DLLs with
**zig 0.16** and this machine has none. The data side (every cup built and its knockout reg
known) is what the table above and the Recopa now provide.

## Order to build them in

1. A fresh world (free ids) with `continental_rank: true` and the new leagues' `europe` places
   in the cups of their confederation -- that builds the cups themselves.
2. `caf_super_cup` (default) and `recopa_sudamericana: true`.
3. The Intercontinental as a further `ccup` once its key exists.
4. The CWC takes its champions when `fl26swiss` can read them.
