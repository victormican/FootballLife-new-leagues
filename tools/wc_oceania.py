"""python wc_oceania.py --base <pesdb> [--revert] [--dry]

Put Oceania and the non-FIFA selections in the FIFA World Cup's team selector.

Why it is a swap and not an add: the World Cup is a shipped competition of **32 clubs** in eight
groups of four (regulation 34) with a knockout of 16 (regulation 35), and the engine pairs "the
two first of each group" with that knockout. 48 clubs would be twelve groups and 24 qualifiers
for 32 places, and Kick Off > Cup drops any competition whose group phase is over 32 clubs. So
the field stays at 32 and sixteen of the shipped participants give their place to:

  * the eight Oceanian selections that were missing (Fiji, New Caledonia, Papua New Guinea,
    Samoa, Solomon Islands, Tahiti, Tonga, Vanuatu) -- New Zealand was already in;
  * the eight selections of "Selecciones No FIFA" (Martinique, Guadeloupe, French Guiana, Saint
    Martin, Sint Maarten, Bonaire, Catalonia, Padania).

The sixteen that leave (Belgium, Egypt, Saudi Arabia, Cote d'Ivoire, Bolivia, Iran, Jordan, Cabo
Verde, Uzbekistan, Norway, Senegal, Ghana, Tunisia, Ecuador, Qatar, South Africa) keep playing
their confederation's competitions; only their World Cup entry changes.

`--revert` puts the sixteen back.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pesdb
import mkleague as M

WC = 27

OUT = [
    "Belgium",
    "Egypt",
    "Saudi Arabia",
    "Côte D'Ivoire",
    "Bolivia",
    "Iran",
    "Jordan",
    "Cabo Verde",
    "Uzbekistan",
    "Norway",
    "Senegal",
    "Ghana",
    "Tunisia",
    "Ecuador",
    "Qatar",
    "South Africa",
]

IN = [
    "Fiji",
    "New Caledonia",
    "Papua New Guinea",
    "Samoa",
    "Solomon Islands",
    "Tahiti",
    "Tonga",
    "Vanuatu",
    "Martinique",
    "Guadeloupe",
    "French Guiana",
    "Saint Martin",
    "Sint Maarten",
    "Bonaire",
    "Catalonia",
    "Padania",
]


def main():
    a = sys.argv[1:]
    get = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    base = get("--base")
    if not base:
        print(__doc__)
        return 2
    dry = "--dry" in a
    revert = "--revert" in a

    teams = pesdb.wesys_unpack(open(os.path.join(base, "Team.bin"), "rb").read())
    ents = bytearray(
        pesdb.wesys_unpack(
            open(os.path.join(base, "CompetitionEntry.bin"), "rb").read()
        )
    )

    tid_of = {}
    for o in range(0, len(teams), 1532):
        r = teams[o : o + 1532]
        name = pesdb.cstr(r[0x170 : 0x170 + 70]).strip()
        if int.from_bytes(r[0x53:0x54], "little") & 0x80:
            tid_of[name] = int.from_bytes(r[8:12], "little")

    want = OUT if revert else IN
    give = IN if revert else OUT
    for n in want + give:
        if n not in tid_of:
            raise SystemExit("no national team called %r" % n)

    rows = sorted(
        (ents[k + M.E_ORDER], k)
        for k in range(0, len(ents), M.ENT)
        if ents[k + M.E_CID] == WC
    )
    if len(rows) != 32:
        raise SystemExit("the World Cup has %d entries, not 32" % len(rows))
    here = [pesdb.cstr(teams[0:0]) or "" for _ in ()]  # placeholder, kept for clarity
    name_of = {}
    for o in range(0, len(teams), 1532):
        r = teams[o : o + 1532]
        name_of[int.from_bytes(r[8:12], "little")] = pesdb.cstr(
            r[0x170 : 0x170 + 70]
        ).strip()

    slots = []
    for _order, k in rows:
        tid = int.from_bytes(ents[k : k + 4], "little")
        slots.append((k, tid, name_of.get(tid, "?")))

    out_rows = [s for s in slots if s[2] in give]
    if len(out_rows) != len(want):
        raise SystemExit(
            "%d of the %d expected clubs are in the World Cup: %s"
            % (len(out_rows), len(want), ", ".join(s[2] for s in out_rows))
        )
    for (k, _tid, old), new in zip(out_rows, want):
        ents[k : k + 4] = tid_of[new].to_bytes(4, "little")
        print("  %-3d %-18s -> %s" % (ents[k + M.E_ORDER], old, new))

    if dry:
        print("dry run: nothing written")
        return 0
    open(os.path.join(base, "CompetitionEntry.bin"), "wb").write(
        pesdb.wesys_pack(bytes(ents))
    )
    print("World Cup: %d entries, %d replaced" % (len(rows), len(out_rows)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
