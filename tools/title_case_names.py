"""python title_case_names.py --base <world pesdb> [--team-from 71578] [--country-from 214] [--dry]

Put the names of our own countries and teams in normal case: "ISLAS MARIANAS DEL NORTE" becomes
"Islas Marianas del Norte".  The game's own rows are left alone.

- Team.bin: every row whose team id is at or above `--team-from` gets the name of its 0x170 slot
  rewritten in every language slot, plus the short name after the code at 0x37C.  The three-letter
  code at 0x372 is not touched, and slot 10 keeps its 24-byte limit (see
  abreviatura-de-equipo.md).
- Country.bin: every row from `--country-from` on gets the eighteen language columns and the
  English name rewritten.

Small Spanish/Portuguese particles stay lower case ("Islas Marianas del Norte", "San Pedro y
Miquelon") except in the first word; hyphens capitalize after the dash ("Saint-Pierre").
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pesdb

T_REC, T_ID = 1532, 0x08
T_NATIONAL = 0x53
T_NAME, T_NAME_LEN, T_NAME_SLOTS, T_NAME_STEP = 0x9E, 70, 20, 70
T_ABBR = 0x372
T_SHORT = 0x35A
T_SHORT_MAX = T_ABBR - T_SHORT
T_LONG, T_LONG_LEN = 0x37C, 22
C_REC = 1420
C_NAMES = list(range(148, C_REC - 69, 70))
C_EN = 288

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
    "dos",
    "das",
    "van",
    "von",
    "der",
    "di",
    "du",
    "of",
    "and",
    "the",
}


def title_case(text):
    words = text.lower().split()
    out = []
    for i, w in enumerate(words):
        if i and w in SMALL:
            out.append(w)
            continue
        out.append("-".join(p[:1].upper() + p[1:] for p in w.split("-")))
    return " ".join(out)


def write_slots(row, text):
    b = text.encode("utf-8")
    for k in range(T_NAME_SLOTS):
        o = T_NAME + k * T_NAME_STEP
        if o + T_NAME_LEN > T_REC:
            continue
        limit = T_SHORT_MAX if o == T_SHORT else T_NAME_LEN - 1
        chunk = b[:limit]
        row[o : o + limit] = chunk + bytes(limit - len(chunk))
        if o != T_SHORT:
            row[o + limit] = 0
    if T_LONG + T_LONG_LEN <= T_REC:
        chunk = b[: T_LONG_LEN - 1]
        row[T_LONG : T_LONG + T_LONG_LEN] = chunk + bytes(T_LONG_LEN - len(chunk))
        row[T_LONG + T_LONG_LEN - 1] = 0


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    a = sys.argv[1:]
    get = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    base = get("--base")
    if not base:
        print(__doc__)
        return 2
    dry = "--dry" in a
    team_from = int(get("--team-from", "71578"))
    country_from = int(get("--country-from", "214"))
    all_teams = "--all-teams" in a

    teams = bytearray(
        pesdb.wesys_unpack(open(os.path.join(base, "Team.bin"), "rb").read())
    )
    changed_t = 0
    for o in range(0, len(teams), T_REC):
        if int.from_bytes(teams[o + T_ID : o + T_ID + 4], "little") < team_from:
            continue
        if not all_teams and not teams[o + T_NATIONAL] & 0x80:
            continue
        name = pesdb.cstr(teams[o + T_NAME : o + T_NAME + T_NAME_LEN]).strip()
        if not name:
            continue
        new = title_case(name)
        if new == name:
            continue
        row = teams[o : o + T_REC]
        buf = bytearray(row)
        write_slots(buf, new)
        teams[o : o + T_REC] = buf
        changed_t += 1
        if changed_t <= 8:
            print(
                "  team %-6d %r -> %r"
                % (int.from_bytes(teams[o + T_ID : o + T_ID + 4], "little"), name, new)
            )

    path = os.path.join(base, "Country.bin")
    cty = bytearray(pesdb.wesys_unpack(open(path, "rb").read()))
    changed_c = 0
    for i in range(0, len(cty), C_REC):
        if i // C_REC < country_from:
            continue
        row = cty[i : i + C_REC]
        name = pesdb.cstr(row[148:218]).strip()
        if not name:
            continue
        new = title_case(name)
        if new == name:
            continue
        buf = bytearray(row)
        for off in C_NAMES + [C_EN]:
            b = new.encode("utf-8")[:68]
            buf[off : off + 69] = b + bytes(69 - len(b))
        cty[i : i + C_REC] = buf
        changed_c += 1
        if changed_c <= 8:
            print("  country row %-4d %r -> %r" % (i // C_REC, name, new))

    print("teams changed: %d, countries changed: %d" % (changed_t, changed_c))
    if dry:
        print("dry run: nothing written")
        return 0
    open(os.path.join(base, "Team.bin"), "wb").write(pesdb.wesys_pack(bytes(teams)))
    open(path, "wb").write(pesdb.wesys_pack(bytes(cty)))
    print("written to %s" % base)
    return 0


if __name__ == "__main__":
    sys.exit(main())
