# Select Team limits, club sizes and the South American formats

Written 2026-10-23 on `cwc-next`, after the 0.2.4.2 update. What the builder can do today, what
it cannot, and the numbers behind each answer. A recipe that exercises every case is at the end.

## Select Team: how many leagues fit

The Select Team / Kick Off list is built from **competition slots**. A league with a slot is
listed; a league on slot 123 is not. The shipped game has 123 slots and 750 club ids per slot;
`fl26slots250.lua` raises the slots to 250 and gives each a capacity of its own (324 clubs, 750
for the region and merge slots, 2600 for the two aggregate slots).

The builder hands out regulation ids in this order (`leaguebuilder.plan` + `fl26world.id_rank`):

| block | ids | slots | leagues |
|---|---|---|---|
| shipped ids with their own slot | 11, 49, 60, ... 190 | 22, 28, 29, 40, ... 113 | 32 (145 and 190 share slot 112) |
| limits branch | 254 down to 197 | 124..181 | 58 |
| seven spares | 174, 176, 179, 180, 183, 184, 185 | 185..188 and 182..184 | 7 |
| second limits step (new) | 256..316 | 189..249 | 61 |
| total | | | **158** |

The four ids that used to borrow the game's "other clubs" groups now take slots 182..188:
174 -> 185, 176 -> 186, 179 -> 187, 180 -> 188, 183 -> 182, 184 -> 183, 185 -> 184. **Slots 69,
71, 73 and 75 are never handed out**, so "Other European Leagues", "Other", "Other Latin American
Teams" and "Other Clubs (Africa)" stay in Select Team. Slots 4, 5 and 6 stay protected for the
Asia-Oceania national teams and the two Classic Teams entries.

The world in `D:\SP Football Life 2026 - copia - copia` has 91 leagues, so every one of them is
listed and no group is hidden. The 158 is the ceiling of this layout.

The second step needs a date for ids above 255: `datecave.py` now sends every id from 256 up to
the big-league calendar shifted by `id & 7`, without a per-id table entry. The shipped
`fl26caps.lua` was regenerated with it; the stub is the only patch that changed. `fl26slots250`
already allows slots to 249 and `fl26slot7` makes a league slot a whole byte.

With the doubled caps (4,800 teams, 6,800 coaches, 1,200 regulations, 123,825 players) a clean
game has 749 clubs and 29,492 players, so about **4,051 new clubs** fit at 22 players. The
Select Team slots (158) and the competition ids (255) are now the walls: a 188-league world needs
188 slots and 279 competition ids with the shipped 91.

## Club sizes

`leaguebuilder.CLUBS_MAX` was 24 ("the range seasons have been played with"), then 30 for
Argentina's 30-club Primera Division, and is **38** now. The number is the calendar, not the
record: a league of ours plays on the big-league calendar, which has **38 dates**
(`BIG_LEAGUE_DAYS`), so a single round-robin tops out at 38 clubs (37 rounds); 39 clubs would
need 39. The record's own club count is six bits (63) and is not what binds.

The builder now **refuses** a plain league whose rounds do not fit, instead of writing a league
that is never dated and never plays:

```
Big 30x2: 30 clubs meeting 2 time(s) are 58 rounds, a season has 38 dates -- at most 20 clubs
at 2 leg(s); legs: 1 is 29 rounds for 30 clubs
```

So 20 clubs twice (38) is the largest two-leg league, 12 clubs three times (33) the largest
three-leg one, and `regress018/big_league_38` builds and checks a 38-club single round. A split
league is exempt: it has its own budget (`SPLIT_MAX_ROUNDS` 46, the Championship's calendar).
The season of a 38-club league has not been played yet; the build and the dates are what is
verified.

## The four formats (2025)

### Colombia — Liga BetPlay Dimayor

- 20 clubs.
- **Apertura** and **Finalización**, each: 20 fechas (every other club once, plus the clásico
  date), top eight into **two groups of four** played home and away (6 fechas), the two group
  winners into a **two-leg final**.
- Relegation by the average table.

Builder today: `apertura` gives two tournaments and an optional knockout of 8 or 4, but the eight
go into a **knockout**, not two groups of four, and the final is one match. A 20-club
Apertura/Clausura also needs 38 dates and the split line offers 35 (38 minus the three dates a
late-joining league cannot use). **Not replicable yet**: needs a "knockout of 8 -> 2 groups of 4"
phase and three more dates.

### Argentina — Liga Profesional de Fútbol

- 30 clubs, drawn into **two zones of 15**.
- Each zone plays a single round-robin (14 matches) plus **two interzonal matches**.
- The top eight of each zone go to a **round of 16, quarter-finals, semi-finals and final**, all
  single-leg.
- **Apertura** and **Clausura**; an aggregate table decides the "Campeón de Liga" and the
  Libertadores places.

Builder today: the 30-club size now builds and dates (29 rounds). Zones, interzonal matches and a
16-team knockout inside a zone are **not supported**; `apertura` also caps at 18 clubs because it
needs two 38-date tournaments. A plain 30-club single round-robin is the closest supported shape.

### Uruguay — Liga AUF Uruguaya

- 16 clubs.
- **Apertura** (15 rounds) and **Clausura** (15 rounds).
- **Torneo Intermedio**: two groups of eight (7 rounds) and a final between the group winners.
- Championship: a **semi-final** between the Apertura and Clausura winners, then a **final**
  against the annual-table leader (or the annual leader is champion directly when it also won a
  tournament).

Builder today: `apertura` with `playoff: 4` approximates the Apertura/Clausura and a final four;
the Intermedio and the annual-leader final are **not supported**. `playoff: 0` gives the two
tournaments and no final.

### Ecuador — LigaPro Serie A

- 16 clubs.
- **Fase Inicial**: double round-robin, 30 matches.
- Top six to the **Fase Final I** (hexagonal, 10 matches, points carried), 7th-12th to the
  **Fase Final II** (another hexagonal, 10 matches), 13th-16th to the **Grupo Descenso**
  (6 matches).
- No final: the Fase Final I winner is champion; the groups keep every point from the initial
  phase.

Builder today: **supported**. A split with a double round-robin and three groups:

```json
{ "name": "Ecuadorian Serie A", "country": "Ecuador", "clubs": 16, "legs": 2,
  "split": { "legs": 2, "groups": [6, 6, 4], "group_legs": 2 } }
```

It writes regular 16 (reg 191), groups 6, 6 and 4 (192, 193, 194), 30 + 10 + 10 + 6 rounds, and
keeps the points (`carry` on by default). Verified with a build; not played in the game yet.

## What is still missing in the formats, and the cheapest way in

Written 2026-10-23, after raising the plain-league cap to 38 clubs. These are the three shapes
of the four above that the builder cannot write yet, with the piece that would carry each.

**Argentina: two zones of 15 plus a round of 16.** A zone is a table of its own, so it is a
regulation of its own: two regulations on the *same* competition id, 15 clubs each, one leg
(14 rounds) -- the same relationship the five twin leagues of the test world have, but with
disjoint clubs. The pieces that do not exist yet: (a) the two interzonal matches, which make
the zone calendars touch, so both regulations need the same dates and two shared days; (b) the
round of 16 fed by the top eight of *both* zones, which is a `ccup` whose entries are positions
of two regulations -- `entry=` already takes `<reg>:<position>` pairs, so the cup side may
already be there; (c) what Master League does with two regulations on one competition id (the
same open question as the twins). **Cheapest experiment:** build a world with two 15-club
regulations on one cid and one ccup of 16, and look at the two tables and the cup in a career
before writing any builder key for it.

**Colombia: eight into two groups of four.** The `split` takes *every* club of the league into
its groups; Colombia takes only the top eight, and the other twelve stop. A split cannot cut,
and the knockout is a knockout, not two groups. The shape that would carry it is a `ccup` of 8
with `groups=2` (the group machinery is the Club World Cup's), fed by positions 1..8 of the
league, with its two winners into a two-leg final. The gate is the same as the Intermedio below:
a cup of two groups of four, mid-season, on dates the league leaves free.

**Uruguay: the Intermedio.** Two groups of eight (7 rounds) between the Apertura and the
Clausura, then a final. The ccup code already draws groups (`groups=8` for the CWC, the
`ccup_rep` replicas at `<reg> + 1024 * (g + 1)`), so two groups of eight is a smaller case of
something that works. What is missing is the *window*: the ccup dates are its own
(`CCUP_GROUP_DAYS`), fixed late November to mid February, and the Intermedio sits in the middle
of an August-May season. A `days=` list on the ccup line already moves a knockout's rounds
(`fl26_swiss_ccup_opts`), so a group cup with its own days is the first thing to try.

None of the three needs new record formats: they need a second regulation on a competition, a
group cup with its own days, or both. The 38-club cap and the date check above are the part
that is done.

## Continental cups by confederation ranking (opt-in)

Recipe key `continental_rank: true`. `leaguebuilder.continental_rank` gives places from the
world's own top divisions, in the order the world file lists them (the League Builder order, the
same one the Club World Cup ranking uses):

| cup | place | leagues |
|---|---|---|
| CAF Champions League | 1st | first 16 CAF leagues |
| CAF Confederation Cup | 2nd | first 8 CAF leagues |
| CONCACAF Champions Cup | 1st | first 8 CONCACAF leagues (MLS fills the rest) |
| Copa Centroamericana | 1st | first 16 Central American leagues |
| OFC Champions League | 1st | first 8 OFC leagues |

The **Copa Centroamericana** (competition 16, `FL_CENTAM`) is built as the qualifier the real
Champions Cup has for Central America: its winner takes the last place of the CONCACAF Champions
Cup (the entry `256:0` in the world file). It is built before the Champions Cup so the regulation
id resolves. A world with only two Central American leagues gets a cup of four (the cup-short
rule tops it up).

The cups still obey their own size rules: 4, 8, 16 or 32 clubs, groups of four when 8 or more,
a straight knockout for the CONCACAF Champions Cup.

## Recipes to try

All three are small worlds (no players, empty names). Build them with:

```
python tools/leaguebuilder.py build <recipe.json> ^
  --base %APPDATA%\FL26ModStudio\tables\common\etc\pesdb ^
  --game <a folder with FL_2026.exe or a scratch folder>
```

- **Ecuador**: one league, 16 clubs, `legs: 2`, `split: {legs: 2, groups: [6,6,4], group_legs: 2}`.
- **Argentina**: one league, 30 clubs, `legs: 1` (the new club cap).
- **CAF/OFC/CONCACAF**: three or more leagues in Senegal, Ghana, Fiji, Costa Rica, Honduras,
  Panama, with `"continental_rank": true`.

## Test in the game

The prepared copy is `D:\SP Football Life 2026 - copia - copia`. It has the 91-league world, the
DLL built from this branch, and a test Club World Cup line. Start the game, open Select Team, and
check the four "other clubs" groups and the last league of the list. For the formats, build one
of the recipes above into the copy with `--game "D:\SP Football Life 2026 - copia - copia"` and
start a Master League career in that league: the split's phases, the group tables and the final
are the things to watch.

## Filling an "Other Clubs" group that the game never fills (2026-10-24)

The heading of slot 75 is "Other Clubs (Africa)" (switch at `0x140ea08e0`), but its list is built
by a filler the repository measured as *never filled* for a foreign club (`fl26clubs.c`, slots
72/75/80). A club in no competition -- Wydad 9030, the only African one, plus Esperance 9033 --
therefore showed under nothing at all.

`fl26clubs.dll` already replaces the two readers of those lists (`0x1414d62c0`,
`0x1414d6290`) and answers a slot from the regulation of the league the world names for it, so
the group only needs a competition of its own. **A league cannot sit on slot 75**, though: the
exe ships a competition there, and `fl26comptab` aborts the whole Select Team table when one of
ours lands on an occupied slot (`slot 75 is already competition N -- not free`).

The world file therefore has a second key:

```
league 197 cid=92 region=25 country=200 conf=5 slot=123 serve=75 tier=1 ... clubs=2 name=Other Clubs (Africa)
```

`slot=123` puts the parameter row on the hidden slot (the league plays, and counts, but asks for
no Select Team row), and **`serve=75`** tells `fl26clubs` to answer slot 75 from regulation 197.
`fl26slotnames` leaves the shipped heading alone because no league of ours *sits* on 75, so the
group is drawn with the exe's own name and our two clubs. `tools/mk_other_africa.py` builds it.

### 2026-10-24, measured: `serve=` on a pool slot crashes the boot

The `serve=75` above was tried in the 135x20 world and **the game crashed** at start-up:
`FL_2026.exe+0x14d6aa0`, `0xc0000005`, inside the sorted insert that moves a slot's club list
(the function at RVA `0x14d6961`, whose per-bucket starts and counts sit at `+0x1d4c0` and
`+0x1d4e8`). `fl26clubs` replaces the two readers but not that insert, so a slot answered from
our regulation (2 clubs) and then written by the exe mixes two counts. The key is therefore
**not** safe on a slot the game itself fills; the line was removed and the world boots again.

If the Africa group is wanted, the insert has to be replaced as well (or the group served from a
slot the exe never writes), not just the readers.
