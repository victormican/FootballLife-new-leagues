r"""python fix_country_ids.py --world <pesdb dir> --worldfile <fl26world.txt> [--go]

Put the country ids right: the world stores the **flag id** where the game reads a **Country.bin
row**, so Argentina (row 129, flag 144) was read as New Caledonia (row 144, Oceania), Brazil (row
131, flag 146) as Papua New Guinea, and South Sudan (row 213, flag 312) fell outside the table
altogether -- the three symptoms: countries in the wrong section, Oceania full, and a country that
never shows.

What this does:

1. `Team.bin`: the country of every team (9 bits at bit 562) goes from flag id to row.
2. The world file: every `country=<flag>` becomes `country=<row>`.
3. `Country.bin`: the Spanish (slots 0 and 3) and English (slot 2) names are written in title
   case -- "SUDAN DEL SUR" -> "Sudan del Sur", keeping the small words lower case.

The flag id and the row are a one-to-one map (240 rows, 240 different flags), so nothing is lost:
the game builds the flag path from the row's own flag id.

    --go writes the three files (backups *.before-countryids); without it, a dry run.
"""

import argparse
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pesdb

C_REC, C_ES, C_ES419, C_EN = 1420, 148, 148 + 3 * 70, 288
T_REC, T_COUNTRY_BIT, T_BITS = 1532, 562, 9
SMALL = {
    "de",
    "del",
    "la",
    "las",
    "los",
    "el",
    "y",
    "e",
    "da",
    "do",
    "das",
    "dos",
    "van",
    "von",
    "di",
    "du",
    "des",
    "dem",
    "der",
    "o",
    "a",
}


def load(d, n):
    with open(os.path.join(d, n), "rb") as f:
        return bytearray(pesdb.wesys_unpack(f.read()))


def cstr(b):
    return bytes(b).split(b"\0")[0].decode("utf-8", "replace").strip()


def bits(rec, bit, n):
    lo, hi = bit // 8, (bit + n + 7) // 8
    return (int.from_bytes(rec[lo:hi], "little") >> (bit % 8)) & ((1 << n) - 1)


def set_bits(rec, bit, n, v):
    lo, hi = bit // 8, (bit + n + 7) // 8
    x = int.from_bytes(rec[lo:hi], "little")
    m = ((1 << n) - 1) << (bit % 8)
    rec[lo:hi] = ((x & ~m) | ((v << (bit % 8)) & m)).to_bytes(hi - lo, "little")


def titular(name):
    out = []
    for k, w in enumerate(name.split()):
        low = w.lower()
        if k and low in SMALL:
            out.append(low)
        elif w.isupper() or w.islower():
            out.append("-".join(p[:1].upper() + p[1:].lower() for p in low.split("-")))
        else:
            out.append(w)
    return " ".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--world", required=True)
    ap.add_argument("--worldfile", required=True)
    ap.add_argument("--go", action="store_true")
    a = ap.parse_args()

    countries = load(a.world, "Country.bin")
    flag_to_row, rows = {}, {}
    for i in range(len(countries) // C_REC):
        o = i * C_REC
        flag = (int.from_bytes(countries[o : o + 4], "little") >> 10) & 0x1FF
        flag_to_row[flag] = i
        rows[i] = (
            cstr(countries[o + C_ES : o + C_ES + 70]),
            cstr(countries[o + C_EN : o + C_EN + 70]),
            countries[o + 5] & 7,
        )
    print(
        "countries: %d, flag ids: %d (one to one: %s)"
        % (len(rows), len(flag_to_row), len(flag_to_row) == len(rows))
    )

    teams = load(a.world, "Team.bin")
    moved, unknown = {}, 0
    for i in range(len(teams) // T_REC):
        o = i * T_REC
        rec = teams[o : o + T_REC]
        v = bits(rec, T_COUNTRY_BIT, T_BITS)
        if v in flag_to_row and flag_to_row[v] != v:
            moved[flag_to_row[v]] = moved.get(flag_to_row[v], 0) + 1
            set_bits(rec, T_COUNTRY_BIT, T_BITS, flag_to_row[v])
            teams[o : o + T_REC] = rec
        elif v not in flag_to_row:
            unknown += 1
    print(
        "teams remapped: %d (unknown country values: %d)"
        % (sum(moved.values()), unknown)
    )
    print(
        "   top: %s"
        % [
            (rows[r][0] or rows[r][1], n)
            for r, n in sorted(moved.items(), key=lambda kv: -kv[1])[:6]
        ]
    )

    lines = open(a.worldfile, encoding="utf-8", errors="replace").read().splitlines()
    wf_changed = 0
    for i, line in enumerate(lines):

        def sub(m):
            nonlocal wf_changed
            v = int(m.group(1))
            r = flag_to_row.get(v, v)
            if r != v:
                wf_changed += 1
            return "country=%d" % r

        lines[i] = re.sub(r"country=(\d+)", sub, line)
    print("world file: %d country values remapped" % wf_changed)

    names = 0
    for i in range(len(countries) // C_REC):
        o = i * C_REC
        for off in (C_ES, C_ES419, C_EN):
            cur = cstr(countries[o + off : o + off + 70])
            if not cur:
                continue
            new = titular(cur)
            if new != cur:
                b = new.encode("utf-8")[:69]
                countries[o + off : o + off + 70] = b.ljust(70, b"\0")
                names += 1
    print("country names in title case: %d" % names)

    if not a.go:
        print("dry run: nothing written (pass --go)")
        return
    for f, data in (("Team.bin", teams), ("Country.bin", countries)):
        dst = os.path.join(a.world, f + ".before-countryids")
        if not os.path.exists(dst):
            shutil.copy2(os.path.join(a.world, f), dst)
        with open(os.path.join(a.world, f), "wb") as fh:
            fh.write(pesdb.wesys_pack(bytes(data)))
    dst = a.worldfile + ".before-countryids"
    if not os.path.exists(dst):
        shutil.copy2(a.worldfile, dst)
    text = "\n".join(lines) + "\n"
    with open(a.worldfile, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    live = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(a.world)))),
        "fl26world.txt",
    )
    if os.path.abspath(live) != os.path.abspath(a.worldfile):
        with open(live, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
    print("written (backups *.before-countryids)")


if __name__ == "__main__":
    main()
