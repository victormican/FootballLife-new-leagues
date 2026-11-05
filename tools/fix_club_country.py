r"""python fix_club_country.py --world <pesdb dir> [--go] [--all]

Repair the clubs whose country is not a Country.bin id.

`Team.bin` keeps a club's country in 9 bits at bit 562; `Country.bin` has 240 records, so an id
of 240 or more is no country at all: the club shows no flag and the game files it by a value it
does not know (Wales 241, Gibraltar 245, Uzbekistan 240, Kosovo 311, Montenegro 304 ...).  This
world had 91 such clubs.

Where the right country comes from: `Competition.bin +3` holds the competition's region, and
`fl26catlist.lua`'s COUNTRY table (the one the game uses) turns a region into a country.  A club
gets the country of the first competition it plays that has one.

    --go writes Team.bin (backup Team.bin.before-country); without it, a dry run.
    --all also changes clubs whose country is valid but does not match their league (a bigger
    hammer: 1.470 clubs in this world).
"""

import argparse
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pesdb
from mkleague import COMP, REGION_OFF, CID_OFF, E_TEAM, E_CID, ENT, dec_region

T_REC, T_ID, T_NAT_BIT, NAT_BITS = 1532, 0x08, 562, 9
GAME_REGIONS = {
    2: 204,
    3: 208,
    4: 236,
    5: 215,
    6: 228,
    7: 224,
    8: 197,
    9: 230,
    10: 238,
    11: 227,
    12: 203,
    13: 237,
    14: 226,
    15: 232,
    16: 146,
    17: 144,
    18: 147,
    19: 148,
    20: 124,
    21: 7,
    27: 190,
    28: 36,
}
CATLIST = os.path.join(HERE, "..", "sider", "fl26catlist.lua")


def load(d, n):
    with open(os.path.join(d, n), "rb") as f:
        return bytearray(pesdb.wesys_unpack(f.read()))


def bits(rec, bit, n):
    lo, hi = bit // 8, (bit + n + 7) // 8
    return (int.from_bytes(rec[lo:hi], "little") >> (bit % 8)) & ((1 << n) - 1)


def set_bits(rec, bit, n, v):
    lo, hi = bit // 8, (bit + n + 7) // 8
    x = int.from_bytes(rec[lo:hi], "little")
    m = ((1 << n) - 1) << (bit % 8)
    rec[lo:hi] = ((x & ~m) | ((v << (bit % 8)) & m)).to_bytes(hi - lo, "little")


def region_countries():
    out = dict(GAME_REGIONS)
    src = open(CATLIST, encoding="utf-8").read()
    body = src[src.index("local COUNTRY = {") :]
    body = body[: body.index("\n}")]
    for rid, cc in re.findall(r"\[(\d+)\]\s*=\s*(\d+)", body):
        out[int(rid)] = int(cc)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--world", required=True)
    ap.add_argument("--go", action="store_true")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--worldfile", default="")
    a = ap.parse_args()

    teams = load(a.world, "Team.bin")
    comps = load(a.world, "Competition.bin")
    ents = load(a.world, "CompetitionEntry.bin")
    rc = region_countries()

    comp_country = {}
    for i in range(len(comps) // COMP):
        c = comps[i * COMP : (i + 1) * COMP]
        cc = rc.get(dec_region(c[REGION_OFF]))
        if cc is not None:
            comp_country[c[CID_OFF]] = cc

    league_country = {}
    if a.worldfile:
        with open(a.worldfile, encoding="utf-8", errors="replace") as f:
            for line in f:
                p = line.split()
                if not p or p[0] != "league":
                    continue
                d = {}
                for tok in p[2:]:
                    if "=" in tok:
                        k, v = tok.split("=", 1)
                        d[k] = v
                if d.get("country", "").isdigit() and d.get("slot", "-1") != "-1":
                    league_country[int(d["cid"])] = int(d["country"])

    comps_of = {}
    for i in range(len(ents) // ENT):
        e = ents[i * ENT : (i + 1) * ENT]
        comps_of.setdefault(
            int.from_bytes(e[E_TEAM : E_TEAM + 4], "little"), []
        ).append(e[E_CID])

    changed, seen = [], 0
    for i in range(len(teams) // T_REC):
        r = teams[i * T_REC : (i + 1) * T_REC]
        tid = int.from_bytes(r[T_ID : T_ID + 4], "little")
        if r[0x53] & 0x80:
            continue
        old = bits(r, T_NAT_BIT, NAT_BITS)
        if old < 240 and old != 0 and not a.all:
            continue
        want = sorted(
            {comp_country[c] for c in comps_of.get(tid, ()) if c in comp_country}
        )
        if len(want) != 1:
            continue
        seen += 1
        if want[0] != old:
            set_bits(r, T_NAT_BIT, NAT_BITS, want[0])
            changed.append((tid, old, want[0]))

    print("clubs looked at: %d, changed: %d" % (seen, len(changed)))
    for tid, old, new in changed[:10]:
        print("   %6d  %d -> %d" % (tid, old, new))
    if len(changed) > 10:
        print("   ... y %d mas" % (len(changed) - 10))
    if not a.go:
        print("dry run: nothing written (pass --go)")
        return
    dst = os.path.join(a.world, "Team.bin.before-country")
    if not os.path.exists(dst):
        shutil.copy2(os.path.join(a.world, "Team.bin"), dst)
    with open(os.path.join(a.world, "Team.bin"), "wb") as f:
        f.write(pesdb.wesys_pack(bytes(teams)))
    print("written (backup Team.bin.before-country)")


if __name__ == "__main__":
    main()
