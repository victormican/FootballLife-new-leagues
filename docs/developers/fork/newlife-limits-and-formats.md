# NewLife against the game's limits, and the formats that fit

2026-10-23. The numbers of NewLife 1.5b12, the caps of the game with fl26caps, and what can be
built from them. `tools/newlife_limits.py` prints the same table for any release and world.

## The caps and the world in use

The 91-league test world (`_FL26MyWorld`) against the caps of a 0.2.4 build:

| table | cap | used | free |
|---|---|---|---|
| teams | 2,400 | 2,199 | **201** |
| players | 61,905 | 61,791 | **114** |
| coaches | 3,400 | 405 | 2,995 |
| competitions | 255 | 183 | 72 |
| regulations | 600 | 308 | 292 |
| Select Team slots | 97 | 91 | 6 |

A new club takes 22-30 players. **114 players is five squads of 22**: the current world cannot
take another 20-club league (20 teams and 440 players), let alone a division. The player cap is
the first wall in a world this size; the team cap is the second.

## NewLife 1.5b12

Ten zips, `newlife-classics/out`:

| part | clubs | players | coaches |
|---|---|---|---|
| Africa | 1,730 | 39,159 | 4 |
| Asia | 1,967 | 42,522 | 18 |
| Europe | 8,954 | 200,129 | 186 |
| North America | 1,051 | 21,166 | 1 |
| South America | 2,124 | 54,087 | 121 |
| Oceania | 474 | 4,687 | 60 |
| Selections | 610 | 10,523 | 0 |
| Classics | 166 | 2,988 | 12 |
| Fantasy | 88 | 1,584 | 0 |
| Free agents | 0 | 262,484 | 0 |
| **total** | **17,164** | **639,329** | **402** |

Of the 17,164 clubs, **622 are already in the game; 16,542 are new**. The team cap is **6.9x**
short and the player cap **10.3x** short. The full NewLife database does not fit, and no amount
of Build options changes that: the arrays themselves are 7-10 times too small.

## The first divisions alone

Taking the first league of each country in file order (the release lists them that way):

- **188 countries**, **2,340 clubs**, **1,979 new** (361 are game clubs);
- 106 countries have fewer than 10 clubs, 106 have 10-24, 1 has 25-30, 1 has more than 30;
- the new clubs need about **43,538 players** at 22 each.

From the shipped game (749 clubs, 29,492 players) that is **2,722 teams** and **73,030 players**
with the shipped squads. The team cap is **322 over** (2,400 -> about 2,750) and the player cap
is **11,125 over** (61,905, with only 32,413 free). So the first divisions need **both caps
raised**. The team cap is a relocation of the team array (the 750 -> 2,400 work); the player cap
is at the player array's ceiling (the array starts at offset 0 and can grow to about 60,745, the
season calendar), so going to 74,000 needs the calendar/upper arrays moved as well. That is a
larger job than the team cap, not a constant.

The current 2,400 world (2,199 teams) has no room for them at all: that world would have to be
replaced, not extended.

## What fits today: NewLife Lite

From the shipped game there are **1,651 team slots** and **32,413 player slots**. At 22 players
a club that is **1,473 clubs** (about 70 leagues of 20, with a few players to spare). The team
cap is then 2,222 of 2,400. This is the largest NewLife subset that builds and plays with the
current caps; `tools/newlife_limits.py --world <base tables>` prints it as "1,473 squads of 22".

A 20-club league fits today in a clean game (20 teams, 440 players). In the 91-league test world
it does not: that world has 114 players free.

The 106 countries under 10 clubs need either a smaller minimum than the builder's 10 (the engine
plays 2-club leagues in cups, but league code has only been tested from 10) or game clubs to fill
the field.

## The 211 national teams

The game has **144** national teams (see [national-teams-and-oceania.md](national-teams-and-oceania.md)).
Reaching **211** means **67 new teams**:

- teams: 67 of the 201 free slots — fits;
- players: 67 x 22 = **1,474**, but only 114 free in this world — needs about 1,360 players freed
  (a rebuild with 29-man squads frees 2,199) or a clean game, where the player array is far from
  full;
- data: names, short names, flags, kits and squads, and the national-team menu work; the NewLife
  `Selections-Teams` zip already has 610 teams and 10,523 players to draw from (156 countries,
  up to 8 teams each).

The **NewLife selections alone** (610 teams, 10,523 players) fit the caps of a clean game
(743 + 610 = 1,353 teams, ~40k players with the shipped squads), but not beside a full club
world.

## Formats that fit

### National teams (211)

| competition | field | shape | engine |
|---|---|---|---|
| World Cup 32 | 32 | 8 groups of four, top two + a knockout of 16 | supported (the shipped shape) |
| Copa América 16 | 16 | 4 groups of four, top two + a knockout of 8 | supported |
| Gold Cup 16 | 16 | 4 groups of four, top two + a knockout of 8 | supported |
| OFC Nations Cup 8 | 8 | 2 groups of four, top two + a final | supported |
| Euro 24 | 24 | 6 groups of four, top two + the four best thirds + a knockout of 16 | **not supported**: the group stage sends the top two only (12 clubs), and the best-thirds rule is not a shape the engine has |
| World Cup 48 | 48 | 12 groups of four, top two + the eight best thirds + a knockout of 32 | **not supported** for the same reason (24 clubs after the groups) |
| AFC Asian Cup 24 / AFCON 24 | 24 | 6 groups of four + the best thirds + a knockout of 16 | **not supported**; a 16-team version is |
| qualifiers | 211 | home-and-away groups | the August `qround` machinery is for clubs; national-team qualifiers need a competition of their own |

The capacity fits all of these once the teams exist. The 16- and 32-team shapes are the
`ccup`/group shapes already used by the continental cups. A 24- or 48-team field needs a new
progression (the best thirds), which no cup of ours has today.

### Clubs and leagues

| format | supported | notes |
|---|---|---|
| 10-30 clubs, 1-4 legs | yes | 30 is new (Argentina); 31-63 fit the six-bit club count but have no calendar work |
| split, 2-3 groups | yes | Ecuador 16x2 + 6/6/4 is the tested shape |
| Apertura/Clausura, playoff 8/4/0 | yes | Colombia's 2x4 groups and Argentina's zones are not shapes the engine draws |
| national cup 2-44 | yes | bracket sizes the screen draws |
| continental cup groups 1-8 | yes | groups of four + knockout |
| 188 first divisions | **not in 2,400 teams** | 2,722 needed; the player cap fits |
| full NewLife | **no** | 16,542 clubs, 639,329 players |

## What to do with this

1. **Full NewLife: no.** The arrays are 7-10x too small; this is not a Build problem.
2. **First divisions: both caps.** ~2,750 teams and ~73,000 players. The team array is a
   relocation like 750 -> 2,400; the player array is at its ceiling (~60,745) and needs the
   calendar/upper arrays moved as well. Not a recipe, and not a small patch.
3. **211 national teams: fits.** 67 teams and 1,474 players; in a clean game the 32,413 free
   players cover them, and in the full 91-league world about 1,360 players have to be freed.
4. **A NewLife Lite world** of about 1,473 clubs (32,406 players) fits **today**, from the shipped
   game: 2,222 of 2,400 teams. That is the build to test the pipeline with the current caps.
5. **Full NewLife: no.** 16,542 new clubs and 639,329 players; the arrays would have to grow 7x
   and 10x.

`python tools/newlife_limits.py` prints all of it for the release and world in use.
