r"""python rename_arg_lower.py --release <NewLife folder> --world <pesdb dir>
                            [--go] [--dry]

Give Argentina's lower divisions their real club names.

The four divisions below the Primera Nacional are filled with placeholders:

    cid 25   Primera B Metropolitana   22 clubs   "Primera B Metropolitana 01..22"
    cid 26   Federal A                 38 clubs   "Federal A 01..38"
    cid 38   Primera C                 28 clubs   "Primera C 01..28"
    cid 99   Torneo Federal            30 clubs   "Torneo Federal 01..30"

The NewLife release carries the real names for those leagues.  This tool writes them into
`Team.bin` in the release's alphabetical order, as many as the division has places; a club with
no name left keeps its numbered placeholder.  The club ids, squads, crests and competitions are
not touched.

    --dry (default) prints the plan; --go writes Team.bin (backup Team.bin.before-argnames).
"""

import argparse
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "modstudio"))
import newlife as NL
import pesdb

T_REC, T_ID, T_NAME, T_NAME_LEN = 1532, 0x08, 0x170, 70
ENT, E_TEAM, E_CID = 12, 0x00, 0x08

DIVISIONS = {
    25: "Argentine Metropolitan B Zone",
    26: "Argentine Torneo Federal A",
    38: "Argentine Metropolitan C Zone",
    99: "Argentine Torneo Regional Federal Amateur",
}


def load(d, n):
    with open(os.path.join(d, n), "rb") as f:
        return bytearray(pesdb.wesys_unpack(f.read()))


def set_name(rec, name):
    b = pesdb.game_text(name).encode("utf-8")[:69]
    b = b.decode("utf-8", "ignore").encode("utf-8")
    rec[T_NAME : T_NAME + T_NAME_LEN] = b.ljust(T_NAME_LEN, b"\0")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--release", required=True)
    ap.add_argument("--world", required=True)
    ap.add_argument("--go", action="store_true")
    a = ap.parse_args()

    rel = NL.Release(a.release)
    names = {}
    for name in DIVISIONS.values():
        names[name] = sorted(
            c["name"] for c in rel.clubs.values() if c.get("league") == name
        )
        print("%-42s %d names in the release" % (name, len(names[name])))

    teams = load(a.world, "Team.bin")
    ents = load(a.world, "CompetitionEntry.bin")
    at = {}
    for i in range(len(teams) // T_REC):
        at[int.from_bytes(teams[i * T_REC + T_ID : i * T_REC + T_ID + 4], "little")] = (
            i * T_REC
        )

    plan, changed = [], 0
    for cid, league in DIVISIONS.items():
        rows = sorted(
            (ents[o + 9], int.from_bytes(ents[o : o + 4], "little"))
            for o in range(0, len(ents) - ENT + 1, ENT)
            if (ents[o + E_CID] | (ents[o + 0x0B] << 8)) == cid
        )
        real = names[league]
        for k, (pos, tid) in enumerate(rows):
            o = at.get(tid)
            if o is None or k >= len(real):
                continue
            cur = (
                bytes(teams[o + T_NAME : o + T_NAME + T_NAME_LEN])
                .split(b"\0")[0]
                .decode("utf-8", "replace")
            )
            if cur == real[k]:
                continue
            plan.append((cid, pos, tid, cur, real[k]))
            set_name(teams[o : o + T_REC], real[k])
            changed += 1

    print("clubs renamed: %d" % changed)
    for cid, pos, tid, old, new in plan[:12]:
        print("   cid %-4d pos %2d %6d  %-28s -> %s" % (cid, pos, tid, old[:28], new))
    if len(plan) > 12:
        print("   ... y %d mas" % (len(plan) - 12))
    if not a.go:
        print("dry run: nothing written (pass --go)")
        return
    dst = os.path.join(a.world, "Team.bin.before-argnames")
    if not os.path.exists(dst):
        shutil.copy2(os.path.join(a.world, "Team.bin"), dst)
    with open(os.path.join(a.world, "Team.bin"), "wb") as f:
        f.write(pesdb.wesys_pack(bytes(teams)))
    print("written (backup Team.bin.before-argnames)")


if __name__ == "__main__":
    main()
