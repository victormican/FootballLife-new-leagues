# Test world, 2026-10-23

The copy `D:\SP Football Life 2026 - copia - copia` is set for a full test. This is what is in it
and what to look at. The world is `_FL26MyWorld` (91 leagues); the modules are this branch's
`fl26swiss.dll` / `.lua`.

## What the world carries

| item | where | expected |
|---|---|---|
| **Others Africa** | `Team.bin` club 9030 (Wydad) now filed in pool 7; `nopool` no longer lists it; slot 75 is free | "Other Clubs (Africa)" in Select Team / Kick Off, with Wydad |
| **Other European / Other / Other Latin American / Classic** | slots 69/71/73 and 5/6 are not used by a league | all four groups in Select Team |
| **Last league** | `id 180` (Spanish Federation First Division B) moved from slot 75 to slot 188 | the league is still listed, and slot 75 is free |
| **Club World Cup** | `cwc 176 177 every=1` (test line; a real Build writes `year=2026 every=4`) | filled at the Champions League play-off in a Master League career, 32 clubs, 8 groups, KO16 |
| **Leagues Cup** | competition 228, groups 258, knockout 259, 16 MLS + 16 Liga MX | Kick Off > Cup; in a career it fills from the leagues |
| **Campeonato Paulista** | comp 229, reg 260, 8 São Paulo clubs, single match, filled day 15, played 20/27/34 | calendar of a Paulista club; Kick Off > Cup |
| **Campeonato Carioca** | comp 230, reg 261, 4 clubs | as above |
| **Campeonato Mineiro** | comp 231, reg 262, 4 clubs | as above |
| **Campeonato Gaucho** | comp 232, reg 263, 2 clubs (final) | as above |
| **Campeonato Paranaense** | comp 233, reg 264, 4 clubs | as above |
| **Campeonato Baiano** | comp 234, reg 265, 2 clubs | as above |
| **Campeonato Cearense** | comp 235, reg 266, 2 clubs | as above |
| **Campeonato Pernambucano** | comp 236, reg 267, 2 clubs | as above |

The eight state cups are `ccup` lines with `clubs=` (the invited clubs), `fill=15`,
`national=1`, `days=...`, `like=23` (FA Cup shape, one match a round) and `cid=` for Cup mode. A
club enters only its own state's list; the others run in parallel.

## Test order

1. **Select Team / Kick Off > League**
   - "Other Clubs (Africa)" is there (Wydad), and so are Other European, Other, Other Latin
     American and Classic Teams.
   - "Spanish Federation First Division B" is still in the list (slot 188).
2. **Kick Off > Cup**
   - Leagues Cup and the eight state cups are in the list.
   - Pick one, pick a club, play a match.
   - `sider.log`: `world file -- N cup(s) for Kick Off > Cup`, `Cup mode -- N world cup(s) added`.
3. **Master League, Brazilian club**
   - Start with one of the eight São Paulo clubs (e.g., Corinthians) and advance to January: the
     Paulista should be filled and played on days 20/27/34.
   - Start with Flamengo for the Carioca, Atlético Mineiro for the Mineiro, Grêmio for the Gaúcho.
   - The state cup is a knockout of 8/4/2; the real Paulista group phase is not replicated.
4. **Master League, Club World Cup**
   - Advance to the Champions League play-off (`r == 2`). `sider.log`:
     `Club World Cup: season ... plays this season`, `our own competition ... filled`,
     32 `Club World Cup N: conf ...`, `groups ... handed to register_all`, `knockout reg ... 16`.
5. **Others Africa note**
   - Wydad is still in the Moroccan league; the Master League may give it the pool slot instead
     of its league. That is the known cost of the quick pool patch; the group visibility is what
     this test checks. A proper new club in pool 7 is the next step if the duplicate matters.

## Logs to send

`SiderAddons\sider.log`, the lines with `fl26swiss:`, `fl26comptab:`, `fl26clubs:` and
`fl26slotnames:` after the first career and after the first Cup mode entry.
