# Generic national teams: 144 -> 211

2026-10-23. `tools/add_nations.py` inserts generic national teams into a world until the count
reaches 211. The test copy already has them.

## What it adds

The game ships **144** national teams (Team.bin rows with the top bit of `+0x53` set). The tool
picks the countries of `Country.bin` that have no national team, **Oceania first** (confederation
7), then the rest by country id, and clones a template national team for each:

- **Team.bin**: a new row with a new team id, the country's name in the twenty name slots (English
  at `+0x170`), a three-letter code, the country id at `+0x46`, the national bit set and the
  template's kit/crest. The template is New Zealand (team 1141) when it has a squad.
- **Player.bin**: 23 players cloned from the template's squad, with new ids, generic names
  ("MONACO Player 01" ...), the country as nationality and the template's attributes.
- **PlayerAssignment.bin**: one row per player with the new national team id, the shirt number and
  squad order of the template.

The new teams use the caps of this branch (4,800 teams, 123,825 players). In the test world:

| | before | after |
|---|---:|---:|
| teams | 2,199 | 2,266 |
| national teams | 144 | **211** |
| players | 61,791 | 63,332 |
| assignments | 56,060 | 57,601 |

The new team ids are 73028..73094 (`CLUB_ID_MAX` is 81919), the new player ids start at 246883.

## Oceania

The eleven OFC countries without a team were added first:

American Samoa 161, Cook Islands 163, Fiji 164, New Caledonia 165, Papua New Guinea 167, Samoa
168, Solomon Islands 169, Tahiti 170, Tonga 171, Vanuatu 172, Palau 184. New Zealand (166) was
already there. They are **national teams under the game's Asia-Oceania slot**, not a separate
"Oceania" heading: the Select Team list has five national-team regions and OFC is merged into
Asia-Oceania. A separate Oceania heading is the option B/C of
[national-teams-and-oceania.md](national-teams-and-oceania.md); nothing here changes that.

## The menu

The teams are in `Team.bin` with the national bit and a country whose confederation is OFC (or
AFC/CAF/...). If the game builds its national-team list from that bit, they appear at once. If it
uses a static list, a module must serve them on slot 4, the way `fl26clubs` serves a league's
club list; that is the thing to measure in the first game start.

## Test

1. Start the game (the test copy already has the tables).
2. **Select Team / Kick Off**: look for the new countries under Asia-Oceania and their
   confederations.
3. Pick one, open its squad (23 generic players), play a match.
4. If they do not appear, the list is static: the next step is a `fl26nations` module for slot 4.

## Rollback

The tables before the insertion are in

`%LOCALAPPDATA%\Temp\opencode\nations-before-<timestamp>\{Team.bin,Player.bin,PlayerAssignment.bin}`

Copy them back to the world's `common\etc\pesdb` and start a new career.
