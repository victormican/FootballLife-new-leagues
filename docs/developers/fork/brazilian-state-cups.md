# Brazilian state cups (Paulista, Carioca, ...)

The game has no Brazilian state championships. It has the Brazilian league (shipped regulation
163, 20 clubs) and the Brazilian cup (competition 24); a world adds the Third and Fourth
divisions as leagues of its own. The state cups are new competitions the League Builder can add
from a recipe, and they run beside the league in a Master League career.

## The recipe key

```json
"state_cups": [
  { "name": "Campeonato Paulista", "code": "FL_PAUL", "region": 0,
    "teams": [1247, 137, 1255, 1254, 2459, 5767, 2465, 5909],
    "groups": 2, "fill": 20, "days": [20, 27, 34, 41, 48, 55] }
]
```

- **teams**: the state's clubs by team id. A state cup takes a fixed list, not league positions;
  `mkccup.py` writes them as its entries.
- **groups**: 0 for a straight knockout of 2, 4, 8, 16 or 32 clubs; N for N groups of four and a
  knockout of the first two. The real Paulista is 16 clubs in four groups; `groups: 4` with 16
  ids is the closest supported shape.
- **fill**: the day the field is filled, in the season frame (20 = 20 January).
- **days**: the days its rounds are played on (January to April for a state cup).
- **region**: the competition region; 0 is Brazil in the shipped table.

The Builder writes a `ccup` line with `clubs=<the team ids>`, `fill=`, `days=`, `national=1` and
`cid=<competition>`, so `fl26swiss` fills the cup with the invited clubs, draws its groups, runs
its knockout and dates it; Kick Off > Cup offers it too (`cid=`, see [cup-mode.md](cup-mode.md)).

## The selected Brazilian club

Every state cup runs in the season. A club enters only its own state's cup (the team id is on
that cup's list), so a career with a Paulista club shows the Paulista fixtures in its calendar
and a Carioca club shows the Carioca ones. No conditional code is needed: the calendar is the
club's competitions.

## Mapping the game's Brazilian clubs

The shipped Brazilian league (regulation 163) has 20 clubs; the Second Division (competition 90)
20 more. The main states, by the clubs in the game:

| state | clubs (team ids) |
|---|---|
| São Paulo | Corinthians 1247, Palmeiras 137, São Paulo 1255, Santos 1254, Red Bull Bragantino 2459, Mirassol 5767, Ponte Preta 2465, São Bernardo 5909, Novorizontino 5768 |
| Rio de Janeiro | Flamengo 1248, Fluminense 1249, Vasco 136, Botafogo 1246 |
| Minas Gerais | Atlético Mineiro 1245, Cruzeiro 274, América Mineiro 2450, Athletic 5973 |
| Rio Grande do Sul | Grêmio 1250, Internacional 1252, Juventude 5137 |
| Paraná | Athletico Paranaense 1930, Coritiba 1931, Operário 5433, Londrina 5048 |
| Bahia | Bahia 2453, Vitória 1937 |
| Santa Catarina | Chapecoense 4108, Avaí 2452, Criciúma 2460 |
| Goiás | Atlético Goianiense 2451, Goiás 1933, Vila Nova 2468 |
| Ceará | Ceará 2454, Fortaleza 5143 |
| Pernambuco | Sport 1936, Náutico 1935 |
| Pará | Remo 5145 |
| Mato Grosso | Cuiabá 5142 |

A state with fewer than 4 clubs in the game can be topped up with clubs of its lower divisions
(the world's Third/Fourth divisions or NewLife clubs), or left as a smaller knockout.

## What is not exact

- The real Paulista plays its group phase once (16 clubs, four groups, top two); the engine's
  `ccup` groups are home and away, so `groups: 4` plays six group matches per club instead of
  three.
- A real state cup is in the calendar before the national league; the cup's days here are set by
  `days` and can overlap the league, as the real one does, but the season frame is the game's
  (the July turn), so the January dates are tested in a career, not guaranteed by data.
- The state of a club is a property of the recipe's list, not of the game's data.

## Test

The `_FL26Paulista` world built from the sample (8 São Paulo clubs, 2 groups) has the cup at
competition 131, group stage 256, knockout 257, filled on day 20 and played on days
20, 27, 34, 41, 48, 55. Build it into the test copy, switch to it and start a career with one of
the eight clubs: the Paulista fixtures should be in the calendar. Kick Off > Cup should list
"Campeonato Paulista".
