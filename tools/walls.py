"""python walls.py --base <world pesdb> --worldfile <fl26world.txt>

Where the world stands against every ceiling that has been measured, in one table:

  players     the array's cap (patches/layout.json), how many the world has, the highest id and
              how many ids are left before the engine's 18-bit player id (262,144)
  teams       the club/team array cap and how many the world has
  competitions  the 255 a one-byte id holds, and how many the world has
  slots       the Select Team slot table (250 with fl26slots250) and the slots the world file
              and the game's own leagues take
  regulations the regulation ids in use

Read-only, no game.  The caps come from patches/layout.json and the exe findings.
"""

import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pesdb
import mkleague as M
import playeredit as E
import fl26world as W

PLAYER_ID_MAX = 262144  # 18 bits: id << 14 | n
SLOTS = 250  # fl26slots250
T_REC, T_ID, T_NATIONAL = 1532, 0x08, 0x53


def main():
    a = sys.argv[1:]
    get = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    base, wf = get("--base"), get("--worldfile")
    if not base:
        print(__doc__)
        return 1
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    lay = json.load(
        open(os.path.join(HERE, "..", "patches", "layout.json"), encoding="utf-8")
    )
    caps = {k: v.get("cap_new") for k, v in lay["arrays"].items()}

    def read(n):
        path = os.path.join(base, n)
        return (
            pesdb.wesys_unpack(open(path, "rb").read()) if os.path.isfile(path) else b""
        )

    teams = read("Team.bin")
    players = read("Player.bin")
    comps = read("Competition.bin")
    regs = read("CompetitionRegulation.bin")

    tids = [
        int.from_bytes(teams[i + T_ID : i + T_ID + 4], "little")
        for i in range(0, len(teams), T_REC)
    ]
    nats = sum(1 for i in range(0, len(teams), T_REC) if teams[i + T_NATIONAL] & 0x80)
    pids = [
        int.from_bytes(players[i + E.P_ID : i + E.P_ID + 4], "little")
        for i in range(0, len(players), E.P_REC)
    ]
    cids = {comps[i + M.CID_OFF] for i in range(0, len(comps), M.COMP)}
    rids = {
        int.from_bytes(regs[i + M.R_ID : i + M.R_ID + 2], "little")
        for i in range(0, len(regs), M.REG)
    }

    lines = (
        io.open(wf, encoding="utf-8", errors="replace").read().splitlines()
        if wf
        else []
    )
    slots = set()
    for l in lines:
        w = l.split()
        if w and w[0] == "league":
            kv = dict(x.split("=", 1) for x in w[2:] if "=" in x)
            if "slot" in kv and int(kv["slot"]) != 123:
                slots.add(int(kv["slot"]))
    game_slots = {s for s in W.DEFAULT_SLOT.values() if s != 123}

    print("player id max in the engine: %d (18 bits)" % PLAYER_ID_MAX)
    top = max(pids) if pids else 0
    print(
        "players   %7d / cap %-7s  highest id %-7d  ids left %d"
        % (len(pids), caps.get("players"), top, PLAYER_ID_MAX - 1 - top)
    )
    print(
        "teams     %7d / cap %-7s  national %d" % (len(tids), caps.get("teams"), nats)
    )
    print(
        "competitions %4d / 255 (a one-byte id)  free %d" % (len(cids), 255 - len(cids))
    )
    print("regulations  %4d / 1024 (the ids the module names)" % len(rids))
    print(
        "slots     %7d of %d used by the world file; %d taken by the game's leagues; %d free"
        % (len(slots), SLOTS, len(game_slots - slots), SLOTS - len(slots | game_slots))
    )
    if players and top >= PLAYER_ID_MAX:
        print("WALL: the player id space is full; no new player can be given an id")
    if len(cids) >= 255:
        print(
            "WALL: every competition id is used; a new competition needs an id above 255"
        )
    if len(slots | game_slots) >= SLOTS:
        print(
            "WALL: every Select Team slot is used; a new league needs a slot above 249"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
