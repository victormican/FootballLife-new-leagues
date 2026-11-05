r"""python other_pools.py --world <pesdb dir> [--go] [--dry]

Put the clubs of the game's "Other ..." competitions back in their group.

The game files a club into an "Other ..." section by the high nibble of `Team.bin +0x4f`:
2 = Other European, 3 = Other Asia-Oceania, 6 = Other Latin American (Concacaf included),
7 = Other Africa, 1 = Classic Teams, 0 = none.  A club inside a league gets it cleared (a club
that plays a league must not be listed twice), and that is what happened to the five
containers of this world -- "Other Clubs (Africa)", "Otros Concacaf", "Other Clubs (Asia)",
"Other European Leagues" and "Other Latin American Teams" -- all of them with their clubs:

    cid 165  "Other Clubs (Africa)"          48 clubs   nibble 0 in 48
    cid 221  "Otros Concacaf"                48 clubs   nibble 0 in 48
    cid 254  "Other Clubs (Asia)"             48 clubs   nibble 3 in 26, 0 in 22
    cid 98   "Other European Leagues"         29 clubs   nibble 2 in 17, 0 in 12
    cid 95   "Other Latin American Teams"     40 clubs   nibble 6 in 4,  0 in 36

So the menus come out hidden (Africa, Concacaf) or half empty (Asia, Europe, LatAm).

    --dry (default) counts; --go writes Team.bin, after copying it to
    Team.bin.before-otherpools.
"""

import argparse
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pesdb

T_REC, T_ID, T_POOL, T_NATIONAL = 1532, 0x08, 0x4F, 0x53
POOLS = {
    165: (7, "Other Clubs (Africa)"),
    221: (6, "Otros Concacaf"),
    254: (3, "Other Clubs (Asia)"),
    98: (2, "Other European Leagues"),
    95: (6, "Other Latin American Teams"),
}


def load(d, n):
    with open(os.path.join(d, n), "rb") as f:
        return bytearray(pesdb.wesys_unpack(f.read()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--world", required=True)
    ap.add_argument("--worldfile", default="")
    ap.add_argument("--go", action="store_true")
    a = ap.parse_args()

    teams = load(a.world, "Team.bin")
    ents = load(a.world, "CompetitionEntry.bin")
    clubs = {}
    for o in range(0, len(ents) - 11, 12):
        cid = ents[o + 8] | (ents[o + 0x0B] << 8)
        clubs.setdefault(cid, []).append(int.from_bytes(ents[o : o + 4], "little"))
    at = {}
    for o in range(0, len(teams) - T_REC + 1, T_REC):
        at[int.from_bytes(teams[o + T_ID : o + T_ID + 4], "little")] = o

    changed = 0
    for cid, (nib, name) in POOLS.items():
        ids = clubs.get(cid) or []
        was = {}
        todo = []
        for t in ids:
            o = at.get(t)
            if o is None:
                continue
            have = teams[o + T_POOL] >> 4
            was[have] = was.get(have, 0) + 1
            if have != nib:
                todo.append(o)
        print(
            "%-30s cid %-4d %2d clubs  before %s -> %d  change %d"
            % (name, cid, len(ids), was, nib, len(todo))
        )
        for o in todo:
            teams[o + T_POOL] = (teams[o + T_POOL] & 0x0F) | (nib << 4)
        changed += len(todo)

    print("clubs moved: %d" % changed)

    # a club that plays a listed league must not carry a group: the game would show it twice
    if a.worldfile:
        listed = set()
        with open(a.worldfile, encoding="utf-8", errors="replace") as f:
            for line in f:
                if line.startswith("league "):
                    for tok in line.split():
                        if tok.startswith("cid=") and tok[4:].isdigit():
                            listed.add(int(tok[4:]))
        league_of = {}
        for o in range(0, len(ents) - 11, 12):
            cid = ents[o + 8] | (ents[o + 0x0B] << 8)
            if cid in listed:
                league_of.setdefault(int.from_bytes(ents[o : o + 4], "little"), cid)
        cleared = 0
        for t, cid in league_of.items():
            o = at.get(t)
            if o is not None and teams[o + T_POOL] >> 4:
                teams[o + T_POOL] &= 0x0F
                cleared += 1
        print("clubs in a listed league back to no group: %d" % cleared)

    # clubs in no competition at all that still belong to a group, by name: the OFC pool clubs,
    # the USL and the Brazilian state pools, the two African placeholders.  The Old Boys, the
    # World Selection, the leftover "Generic League" clubs and the Copa Argentina placeholders
    # are left alone (they are not a league's bench, they are spare slots)
    RULES = (
        ("Liga Pro OFC", 3),
        ("Brazil State Pool", 6),
        ("Other Clubs (Africa) Club", 7),
        ("Moroccan Premier Division Club", 7),
        ("Ligue Professionnelle 1 Club", 7),
        ("Sacramento Republic", 6),
        ("Indy Eleven", 6),
        ("Louisville City", 6),
        ("Tampa Bay Rowdies", 6),
        ("Phoenix Rising", 6),
        ("San Antonio FC", 6),
        ("Detroit City", 6),
        ("Birmingham Legion", 6),
        ("New Mexico United", 6),
        ("Pittsburgh Riverhounds", 6),
    )
    in_any = set()
    for o in range(0, len(ents) - 11, 12):
        in_any.add(int.from_bytes(ents[o : o + 4], "little"))
    placed = 0
    for o in range(0, len(teams) - T_REC + 1, T_REC):
        t = int.from_bytes(teams[o + T_ID : o + T_ID + 4], "little")
        if t in in_any or teams[o + T_NATIONAL] & 0x80 or teams[o + T_POOL] >> 4:
            continue
        name = (
            bytes(teams[o + 0x170 : o + 0x170 + 70])
            .split(b"\0")[0]
            .decode("utf-8", "replace")
        )
        for prefix, nib in RULES:
            if name.startswith(prefix):
                teams[o + T_POOL] = (teams[o + T_POOL] & 0x0F) | (nib << 4)
                placed += 1
                break
    print("clubs with no competition given a group: %d" % placed)
    if not a.go:
        print("dry run: nothing written (pass --go)")
        return
    dst = os.path.join(a.world, "Team.bin.before-otherpools")
    if not os.path.exists(dst):
        shutil.copy2(os.path.join(a.world, "Team.bin"), dst)
    with open(os.path.join(a.world, "Team.bin"), "wb") as f:
        f.write(pesdb.wesys_pack(bytes(teams)))
    print("written (backup Team.bin.before-otherpools)")


if __name__ == "__main__":
    main()
