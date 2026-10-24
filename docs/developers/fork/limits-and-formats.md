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

Past the slots the next wall is the **club and player tables**: `fl26caps` gives the game 2,400
clubs and 61,905 players; a clean game has 749 clubs and 29,492 players, so 1,473 new clubs at 22
players fit. A 158-league world of 10 clubs needs 1,580 clubs and ~34,760 players, which is
~2,700 players over the cap; about 145 leagues of 10 fit. Raising the team array alone does not
help while the player array is the wall.

## Club sizes

`leaguebuilder.CLUBS_MAX` was 24 ("the range seasons have been played with"). It is **30** now,
because Argentina's Primera División has 30 clubs. 30 clubs on one round (29 rounds) fits the
38-date league calendar; the build is verified, the season is not played yet. 31..63 would fit
the record's six-bit club count but no calendar work has been done for them.

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
