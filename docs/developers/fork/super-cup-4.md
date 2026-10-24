# A four-club super cup: the Supercopa de España as it is played

2026-10-23. `tools/super_cup4.py` turns a shipped two-club super cup into the four-club
version: two semi-finals and a final. It spends no competition id and no regulation id -- the
super cup keeps its row and its cid, and only its bracket grows.

## The shipped row

```
cid 74  SPAIN_SUPER_CUP   region 32  (Spain)
  reg 87  type 3 (knockout)  bracket 2  "Supercopa de España"
```

A super cup is already a **knockout** (type 3); two clubs is just its bracket. The Italian one
(cid 76, reg 89), the French (75/88), the English (73/86) and the rest are the same shape, so
the tool works for any of them. The Spanish places are reg **19** (LaLiga) and reg **25** (Copa
del Rey).

## What it writes

```
ccup 87 ko=87 groups=0 entry=19:1,19:2,25:0,19:3 cid=74 fill=190 national=1 \
     days=7,11 alt=2:19:3,3:19:4 name=Supercopa de España
cupdays 87 7 11
```

- **`entry`** -- LaLiga 1st and 2nd, the Copa del Rey winner (`25:0`, a cup-winner entry), and
  LaLiga 3rd.
- **`alt`** -- the fallbacks, entry by entry (0-based): if the cup winner is already in the
  field (it finished in the top two), entry 2 takes LaLiga 3rd, 4th...; and if the 3rd was
  taken that way, entry 3 takes the 4th. Four distinct clubs, which is the real rule without
  the cup runner-up (the module can only ask for a cup's *winner*).
- **`days=7,11`** -- the semi-finals and the final in early January. The big-league calendar
  has its rounds on days 2, 13, 16, ... so 7 and 11 are free midweek days.
- **`cupdays 87 7 11`** -- tells our leagues' calendars to keep clear; a shipped league such as
  LaLiga dates itself from the game and does not need it, but the line is harmless.
- **`fill=190`** -- the field is chosen at the **start of the season** (day 190, early July),
  because the four places come from the season that has just ended: the league's final table
  and the cup final are still the finished records then. Filled in January, `cup_winner` would
  read a Copa del Rey that is being played, not the one that was won.

The regulation's bracket goes from 2 to 4 (`CompetitionRegulation.bin`, the six-bit count at
`+0x0b`), so the game draws two semi-finals and a final for it.

## Running it

```
python tools/super_cup4.py --base <world pesdb> --worldfile <world> \
    --league 19 --cup 25 --super 87 --name "Supercopa de España"
```

The test copy has it applied (`--dry` first if you want to see the lines). Italy would be
`--league 21 --cup 22 --super 89` (check the ids with `mkleague`/the tables first) and so on
for the other super cups of four in real life.

## What to watch in the first game

The **shipped super cup keeps its own fill**: the game gives a super cup the league champion
and the cup winner by itself, and if it does that at its own date it can overwrite the four.
The module fills the cup on day 190; if the shipped fill comes later, the field goes back to
two. The first career tells: the Supercopa should have **two semi-finals in January** and its
four clubs from the previous season. If it plays in July, or with two clubs, the shipped date
or fill is the thing to move next.

## This is the same shape the continental cups need

The user's goal -- the Intercontinental (annual) and the 32-club Club World Cup (every four
years) filled from **each confederation's competitions**, recopas included -- is the same
mechanism: an entry of `<regulation>:0` is "the winner of that cup". A Recopa Sudamericana is
then a two-club cup with `entry=<Libertadores>:0,<Sudamericana>:0`; the Intercontinental is a
cup whose entries are the continental champions (`<UCL>:0`, `<Libertadores>:0`, and the other
confederations' winners in the earlier rounds). What is missing for those in the test copy is
**free competition ids** (255 of 255 are used), so they belong in a fresh build; and the
32-club CWC still chooses its 32 by league ranking inside `fl26swiss` (`cwc`), which has no
"champion of" entries yet -- that is a DLL change.
