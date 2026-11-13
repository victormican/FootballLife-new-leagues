"""Toggles a *single* variable in the built world so a boot test can name the culprit.

    python tools/world_variant.py --dir <pesdb> --backup
    python tools/world_variant.py --dir <pesdb> --drop-countries [--restore]

--backup            snapshot the tables into <pesdb>\\_bak-<stamp>
--drop-countries     truncate Country.bin back to its original row count and point the
                     invented teams at an existing country, so the game never sees a
                     country row or a team->country link it did not ship with.
--restore           put the snapshot back
"""

import os
import shutil
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pesdb  # noqa: E402

TABLES = [
    "Team.bin",
    "Country.bin",
    "Player.bin",
    "PlayerAssignment.bin",
    "Competition.bin",
    "CompetitionRegulation.bin",
    "CompetitionEntry.bin",
]

T_REC, T_ID, T_COUNTRY = 1532, 0x08, 0x46
C_REC = 1420
BASE_COUNTRIES = 214
INVENTED_TEAM_FROM = 71597


def load(base, name):
    return bytearray(pesdb.wesys_unpack(open(os.path.join(base, name), "rb").read()))


def save(base, name, blob):
    open(os.path.join(base, name), "wb").write(pesdb.wesys_pack(bytes(blob)))


def main():
    a = sys.argv[1:]
    base = a[a.index("--dir") + 1]
    bak = os.path.join(base, "_bak")

    if "--restore" in a:
        if not os.path.isdir(bak):
            print("no snapshot in", bak)
            return 1
        for name in TABLES:
            src = os.path.join(bak, name)
            if os.path.exists(src):
                shutil.copy2(src, os.path.join(base, name))
                print("restored", name)
        return 0

    if "--backup" in a:
        os.makedirs(bak, exist_ok=True)
        for name in TABLES:
            shutil.copy2(os.path.join(base, name), os.path.join(bak, name))
        print("snapshot ->", bak)
        return 0

    if "--drop-countries" in a:
        cty = load(base, "Country.bin")
        teams = load(base, "Team.bin")
        rows = len(cty) // C_REC
        if rows <= BASE_COUNTRIES:
            print("Country.bin already has %d rows, nothing to drop" % rows)
            return 1
        keep = BASE_COUNTRIES * C_REC
        dropped = rows - BASE_COUNTRIES

        have = {
            ((int.from_bytes(cty[o : o + 4], "little") >> 10) & 0x1FF)
            for o in range(0, keep, C_REC)
        }
        moved = 0
        for i in range(len(teams) // T_REC):
            o = i * T_REC
            tid = struct.unpack_from("<I", teams, o + T_ID)[0]
            if tid < INVENTED_TEAM_FROM:
                continue
            old = int.from_bytes(teams[o + T_COUNTRY : o + T_COUNTRY + 2], "little")
            if ((old >> 2) & 0x1FF) not in have:
                teams[o + T_COUNTRY : o + T_COUNTRY + 2] = (
                    (old & ~(0x1FF << 2)) | (1 << 2)
                ).to_bytes(2, "little")
                moved += 1

        save(base, "Team.bin", teams)
        open(os.path.join(base, "Country.bin"), "wb").write(
            pesdb.wesys_pack(bytes(cty[:keep]))
        )
        bad = [
            struct.unpack_from("<I", teams, i * T_REC + T_ID)[0]
            for i in range(len(teams) // T_REC)
            if (
                (
                    int.from_bytes(
                        teams[i * T_REC + T_COUNTRY : i * T_REC + T_COUNTRY + 2],
                        "little",
                    )
                    >> 2
                )
                & 0x1FF
            )
            not in have
        ]
        print(
            "dropped %d country rows (%d left), repointed %d invented teams to country 1"
            % (dropped, BASE_COUNTRIES, moved)
        )
        print(
            "teams still pointing at a missing country after patch: %d %s"
            % (len(bad), bad[:5])
        )
        return 0

    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main())
