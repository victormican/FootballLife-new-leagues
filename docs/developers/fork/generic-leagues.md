# Generic leagues to test the Select Team slots

2026-10-23. `tools/add_generic_leagues.py` inserts generic leagues into a built world so the
Select Team list can be filled and the slots measured. The test copy has **62**: 19 on slots
189..207 and 43 more on 208..249 and 182.

## What it adds

- **62 leagues**, ten clubs each: 19 on slots 189..207 (competition ids 237..255) and 43 on slots
  208..249 plus 182 (the free low ids, see below).
- **620 clubs** cloned from a template club with 22 players, generic names
  ("Generic League 01 Club 01"), country 200 (Croatia), region 29, so no new region is needed.
- **13,640 players** cloned with generic names and the country as nationality.
- Competition rows, regulations (ids 317..335 and 336..378), entries and the world file's `league`
  lines.
- Slots **182, 189..249**. Slots 69/71/73/75 are never used, so "Other Clubs (Africa)" and the
  other groups stay. **Five slots (183..187) remain free**: the competition cap is reached.

The test world after the insertion:

| | before | after |
|---|---:|---:|
| teams | 2,266 | 2,886 |
| national teams | 211 | 211 |
| players | 63,332 | 76,972 |
| competitions | 193 | **255** |
| regulations | 336 | 398 |
| leagues | 91 | 153 |

## The competition cap

The world had 193 competitions. The first 19 took the free high ids 237..255. The next 43 took
the free low ids: the 28 `CID_SAFE_LOW`, the 9 `CID_COSMETIC_LOW`, and the six the game never
uses (6, 7, 48, 65, 91, 92) as the last six. That is **255 of 255 competitions**. Five slots
(183..187) have no competition id left: the next step is the competition-id high byte (256..511),
which is designed but not built.

## Test

1. Start the game.
2. **Select Team / Kick Off**: "Other Clubs (Africa)" must be there (Wydad), and so must the four
   other "Other" groups; the 19 "Generic League" rows are under Croatia/Europe, slots 189..207.
3. Start a career in one of them, or just scroll the list: the point is that every slot appears.
4. If the list stops at 207 or a group disappears, `sider.log` has the `fl26comptab` and
   `fl26slotnames` lines; send them.

## Rollback

`%LOCALAPPDATA%\Temp\opencode\leagues-before-<timestamp>\` holds Team.bin, Player.bin,
PlayerAssignment.bin, Competition.bin, CompetitionRegulation.bin, CompetitionEntry.bin and the
world file before the insertion.
