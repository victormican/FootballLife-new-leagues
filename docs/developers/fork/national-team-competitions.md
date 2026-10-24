# National-team competitions: what the game has, what we build

2026-10-23. The user's list -- World Cup qualifying, the CONCACAF and UEFA Nations Leagues, the
Gold Cup and the OFC Nations Cup -- against what the game ships and what
`tools/add_nations_cups.py` adds.

## What the game already has (and it is more than it looks)

The shipped tables carry the national competitions **with their entries**, and their
competition rows use a special region and flag:

| cid | code | shape | entries |
|---|---|---|---|
| 27 | `FIFA_WORLD_CUP` | groups, 32 | 32 national teams |
| 28 | `FIFA_WORLD_CUP_EUROPE` | qualifier | 44 |
| 29 | `FIFA_WORLD_CUP_NCAMERICA` | qualifier | 6 |
| 30 | `FIFA_WORLD_CUP_SAMERICA` | qualifier | 10 |
| 31 | `FIFA_WORLD_CUP_ASIA` | qualifier | 10 |
| 32 | `FIFA_WORLD_CUP_AFRICA` | qualifier | 10 |
| 33 | `EURO` | groups, 24 | 24 |
| 34 | `COPA_AMERICA` | groups, 16 | 16 |
| 35 | `AFC_ASIA_CUP` | groups, 16 | 16 |
| 36 | `AFRICA_NATIONS_CUP` | groups, 14 | 14 |

All of them sit on **region 25** (the byte 200; `mkleague.dec_region(200) == 25`) with the
confederation in the low three bits of the flag (`Competition.bin +6`): 2 UEFA, 3 AFC,
4 CONMEBOL, 5 CAF.

**Why this matters:** the module's club lookup (`club_of_id`) searches the live competition
records for a team id. A national team that is in one of those ten competitions **is found**,
so a cup can invite it. That is what makes a national cup buildable at all.

Missing from the game: an OFC qualifier, the Gold Cup, the OFC Nations Cup and both Nations
Leagues.

## What `add_nations_cups.py` builds

```
python tools/add_nations_cups.py --base <world pesdb> --worldfile <fl26world.txt> \
    --countries <pesdb with Country.bin> [--preset gold,ofc,wc-ofc,nl-uefa,nl-concacaf] [--dry]
```

| preset | competition | conf | teams | filled | rounds (days) |
|---|---|---|---|---|---|
| `gold` | CONCACAF Gold Cup | 6 | 16 | day 185 | 190, 193, 196, 199 (July) |
| `ofc` | OFC Nations Cup | 7 | 8 | 150 | 155, 158, 161 (June) |
| `wc-ofc` | OFC World Cup Qualifying | 7 | 8 | 60 | 65, 68, 71 (March) |
| `nl-uefa` | UEFA Nations League | 2 | 16 | 70 | 75, 82, 96, 103 (Sep-Nov) |
| `nl-concacaf` | CONCACAF Nations League | 6 | 16 | 70 | 75, 82, 96, 103 (Sep-Nov) |

Each one is built by `mkccup.py` as a **straight knockout, one match a round** (`like=23`, the
FA Cup's row: the bracket screen draws any field of 2..16, 18, 20, 24, 28, 30, 32 and 44), with:

- a competition row on **region 25** and the confederation in its flag;
- the knockout regulation copied from the FA Cup, bracket = the field;
- **entries = the national teams**, so the tables are coherent;
- a `ccup` line whose `clubs=` names the same teams, so `fl26swiss` fills the cup with exactly
  them (the entries are not what the module reads for a cup).

The teams are the world's own national teams grouped by the confederation of their country. A
preset whose confederation is short is refused with the count, never built half-full.

Verified end to end on a fresh world of 211 national teams (UEFA 56, CONMEBOL 10, CONCACAF 35,
AFC 45, CAF 53, OFC 12): five competitions (cids 131..135, regulations 176..180), 16/8/8/16/16
entries, `buildcheck` and `check_world` clean.

## Why it could not be tested in the test copy

The copy has **255 of 255 competition ids** used, so there is no id for a new competition.
These go in a **fresh world** (`leaguebuilder` recipe + `add_nations.py` + this tool).

## The one C change they need, and it is not built yet

`club_of_id` reported a team only if some competition already held it. That is true of the 144
shipped national teams (cids 27..36) but **not** of the 67 an `add_nations.py` world adds, nor of
clubs that live only in the "Other" pools. `tools/native/fl26swiss.c` now falls back to the
team record itself:

```
  uint32_t nt;
  unsigned char* a = team_array(&nt);
  if (a)
    for (uint32_t i = 0; i < nt; i++) {
      uint32_t v = team_at(a, i);
      if ((v >> 14) == c && (v & 0x3fff) == i) return v;
    }
  return 0;
```

That is the value the engine itself would hold (`id << 14 | row`), and `canon_club` keeps it.
The source is changed; **the DLL is not rebuilt here** -- the repository builds with zig 0.16
and this machine has none (`sh tools/native/build-swiss.sh out/fl26swiss.dll` where `ZIG` is
set). Until it is rebuilt, a cup can only invite the 144 shipped national teams.

## Shapes still missing

- **Groups.** The module's group stages are dated on `CCUP_GROUP_DAYS` (late November to
  February) and `days=` moves only the knockout (`ccup_day`). A Gold Cup or Nations League with
  groups in September or July needs `ccup_day` to use `days` for the group rounds too -- a
  small C change, same rebuild.
- **The qualifiers' fields.** The shipped qualifiers keep their own 44/6/10/10/10 entries; making
  them take the 67 new teams is a rewrite of those competitions, not a new cup.
- **The cycle.** The five cups above are every-season cups (the module fills them each year);
  a four-year World Cup cycle inside the game is the game's own and is not touched.
