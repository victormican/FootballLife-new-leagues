# Generic leagues to test the Select Team slots

2026-10-23. `tools/add_generic_leagues.py` inserts generic leagues into a built world so the
Select Team list can be filled and the slots measured. The test copy already has nineteen.

## What it adds

- **19 leagues** (the free high competition ids 237..255 of the 91-league world), ten clubs each.
- **190 clubs** cloned from a template club with 22 players, generic names
  ("Generic League 01 Club 01"), country 200 (Croatia), region 29, so no new region is needed.
- **4,180 players** cloned with generic names and the country as nationality.
- Competition rows, regulations (ids 317..335), entries and the world file's `league` lines.
- Slots **189..207**: the new part of the Select Team layout (ids 256+). Slots 69/71/73/75 are
  never used, so "Other Clubs (Africa)" and the other groups stay.

The test world after the insertion:

| | before | after |
|---|---:|---:|
| teams | 2,266 | 2,456 |
| national teams | 211 | 211 |
| players | 63,332 | 67,512 |
| competitions | 193 | 212 |
| regulations | 336 | 355 |
| leagues | 91 | 110 |

## The competition cap

The world had 193 competitions; the free high ids are **237..255 (19)**. The count cap is 255,
so 62 more competitions would be the absolute maximum, but the remaining 43 would need the low
safe ids (`mkworld.CID_SAFE_LOW`, `FL26_LOW_CIDS`) or the competition-id high byte, which is not
built. **19 is what the high ids allow without touching the low ones.**

The slots 208..249 are free but have no competition to put there. That is the next wall, not the
slot table: the slots exist, the competition ids do not.

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
