"""python nations.py [--base <world pesdb>] [--countries <pesdb with Country.bin>] [--json]

Read the national teams out of Team.bin and group them by the confederation of their country
(Country.bin +5: 2 UEFA, 3 AFC, 4 CONMEBOL, 5 CAF, 6 CONCACAF, 7 OFC).  Read-only: it writes
nothing.  It exists to answer "how many national teams does this world have, and which ones are
Oceania?" before anyone plans a new region or a new national team.

The game ships 144 national teams (Team.bin rows with the national bit, +0x53 bit 7), not the
211 associations FIFA has.  Only one of them is OFC: New Zealand (team 1141, country 166).  The
other eleven OFC country ids in Country.bin have no national team at all.

The Select Team / Kick Off list groups them by competition slot, not by this table: slots 0..4
are Europe, Africa, North & Central America, South America and Asia-Oceania.  There is no sixth
national-team slot; see docs/developers/fork/national-teams-and-oceania.md.
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pesdb
import mkflags
import leaguebuilder as B

T_REC = 1532
T_ID = 0x08
T_NATIONAL = 0x53
T_COUNTRY = 0x46
T_NAME = 0x170
T_ABBR = 0x372
CONF = {2: "UEFA", 3: "AFC", 4: "CONMEBOL", 5: "CAF", 6: "CONCACAF", 7: "OFC"}


def text(b):
    return b.split(b"\0")[0].decode("utf-8", "replace")


def read(base, countries):
    raw = pesdb.wesys_unpack(open(os.path.join(base, "Team.bin"), "rb").read())
    cty = mkflags.countries(mkflags.table("Country", [countries or base]))
    conf = B.confederations(countries or base)
    out = []
    for i in range(len(raw) // T_REC):
        r = raw[i * T_REC : (i + 1) * T_REC]
        if not r[T_NATIONAL] & 0x80:
            continue
        fid = (int.from_bytes(r[T_COUNTRY : T_COUNTRY + 2], "little") >> 2) & 0x1FF
        out.append(
            {
                "id": int.from_bytes(r[T_ID : T_ID + 4], "little"),
                "name": text(r[T_NAME : T_NAME + 70]),
                "abbr": text(r[T_ABBR : T_ABBR + 4]),
                "country": fid,
                "country_name": (cty.get(fid) or ("?",))[0],
                "conf": conf.get(fid),
                "conf_name": CONF.get(conf.get(fid), "none"),
            }
        )
    return out


def main():
    a = sys.argv[1:]
    get = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    base = get("--base") or os.path.join(
        os.environ.get("APPDATA", ""),
        "FL26ModStudio",
        "tables",
        "common",
        "etc",
        "pesdb",
    )
    countries = get("--countries") or base
    nats = read(base, countries)
    counts = {}
    for n in nats:
        counts[n["conf_name"]] = counts.get(n["conf_name"], 0) + 1
    if "--json" in a:
        print(
            json.dumps(
                {"total": len(nats), "by_confederation": counts, "teams": nats},
                indent=1,
                ensure_ascii=False,
            )
        )
        return 0
    print("%d national teams in %s" % (len(nats), os.path.join(base, "Team.bin")))
    for k in ("UEFA", "CONMEBOL", "CONCACAF", "AFC", "CAF", "OFC", "none"):
        if counts.get(k):
            print("  %-9s %3d" % (k, counts[k]))
    print("\nOFC national teams:")
    for n in nats:
        if n["conf"] == 7:
            print(
                "  team %-5d %-22s country %-3d %s"
                % (n["id"], n["name"], n["country"], n["country_name"])
            )
    return 0


if __name__ == "__main__":
    sys.exit(main())
