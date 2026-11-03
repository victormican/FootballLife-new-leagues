"""python find_shipped_regions.py --game <carpeta del juego> [--regions 22,23,24]

Find the competition ids the game itself uses for a set of menu regions (22 Germany, 23 USA,
24 Japan) so their flag can be given to fl26comptab's ID_COUNTRY table.

The shipped tables are not in dt15: they live in data_s2526*.cpk (the FL26 data pack).  This
extracts Competition.bin from the first one that has it and prints `cid` + region + the code
string, which is what ID_COUNTRY is keyed by.

    python find_shipped_regions.py --game "D:/SP Football Life 2026" --regions 22,23,24
"""

import glob
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cpkread
import pesdb

COMP, CID_OFF, REGION_OFF, CODE_OFF = 36, 5, 3, 8


def main():
    a = sys.argv[1:]
    get = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    game = get("--game")
    if not game:
        print(__doc__)
        return 2
    want = {int(v) for v in get("--regions", "22,23,24").split(",")}

    tmp = os.path.join(os.environ.get("TEMP", "."), "fl26shipped")
    os.makedirs(tmp, exist_ok=True)
    rel = "common/etc/pesdb/Competition.bin"
    path = os.path.join(tmp, *rel.split("/"))
    if not os.path.exists(path):
        cands = sorted(
            glob.glob(os.path.join(game, "Data", "data_s2526*.cpk"))
        ) + sorted(glob.glob(os.path.join(game, "download", "data_s2526*.cpk")))
        for c in cands:
            try:
                cpkread.extract(c, tmp, [rel])
            except Exception:
                continue
            if os.path.exists(path):
                print("leido de", os.path.basename(c))
                break
    if not os.path.exists(path):
        raise SystemExit("no he podido sacar Competition.bin del data pack")

    comp = pesdb.wesys_unpack(open(path, "rb").read())
    print("competiciones: %d" % (len(comp) // COMP))
    found = []
    for i in range(0, len(comp), COMP):
        c = comp[i : i + COMP]
        if c[REGION_OFF] in want:
            code = pesdb.cstr(c[CODE_OFF : CODE_OFF + 12]).strip()
            found.append((c[REGION_OFF], c[CID_OFF], code))
    for region, cid, code in sorted(found):
        print("  region %-4d cid %-4d %s" % (region, cid, code))
    if not found:
        print("  ninguna competicion en esas regiones")
    print()
    print("para fl26comptab.lua:")
    pais = {22: 210, 23: 135, 24: 13}
    for region, cid, code in sorted(found):
        if region in pais:
            print("  ID_COUNTRY[%d] = %d   -- %s" % (cid, pais[region], code))
    return 0


if __name__ == "__main__":
    sys.exit(main())
