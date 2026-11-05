import os
import sys
import unicodedata

T = r"C:\Users\viarm\test-carpeta\pes-2021\tools"
sys.path.insert(0, T)
sys.path.insert(0, os.path.join(T, "modstudio"))
import newlife as NL
import pesdb

W = r"D:\SP Football Life 2026 - copia - copia\SiderAddons\livecpk\_FL26MyWorld\common\etc\pesdb"
WF = r"D:\SP Football Life 2026 - copia - copia\SiderAddons\modules\fl26world.txt"
TARGETS = [11, 60, 93, 111, 121, 201, 221, 341, 345, 358, 359, 8467, 900]


def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()
    return " ".join("".join(c if c.isalnum() else " " for c in s.lower()).split())


def cstr(b):
    return bytes(b).split(b"\0")[0].decode("utf-8", "replace").strip()


def code(n):
    w = [
        x
        for x in "".join(ch if ch.isalnum() or ch == " " else " " for ch in n).split()
        if x
    ]
    return ("".join(x[0] for x in w[:3]) if len(w) >= 3 else "".join(w)[:3]).upper()[:3]


world = {}
for line in open(WF, encoding="utf-8", errors="replace"):
    p = line.split()
    if p and p[0] == "league":
        d = {"reg": p[1]}
        for tok in p[2:]:
            if "=" in tok:
                k, v = tok.split("=", 1)
                d[k] = v
        d["name"] = line.split("name=", 1)[-1].strip()
        world[d["reg"]] = d

rel = NL.Release(r"C:\Users\viarm\Downloads\Database Newlife")
relc = {}
for c in rel.clubs.values():
    if c.get("league"):
        relc.setdefault(c["league"], []).append(c["name"])

teams = bytearray(pesdb.wesys_unpack(open(os.path.join(W, "Team.bin"), "rb").read()))
ents = pesdb.wesys_unpack(open(os.path.join(W, "CompetitionEntry.bin"), "rb").read())
at = {}
for i in range(len(teams) // 1532):
    o = i * 1532
    at[int.from_bytes(teams[o + 8 : o + 12], "little")] = o

total = 0
for reg in TARGETS:
    d = world[str(reg)]
    cid = int(d["cid"])
    league = next((k for k in relc if norm(k) == norm(d["name"])), None)
    if league is None:
        league = next((k for k in relc if norm(d["name"]) in norm(k)), None)
    if league is None:
        print("reg %-5s %-38s sin liga equivalente" % (reg, d["name"]))
        continue
    names = sorted(relc[league])
    have = {norm(n) for n in names}
    rows = sorted(
        (ents[o + 9], int.from_bytes(ents[o : o + 4], "little"))
        for o in range(0, len(ents) - 11, 12)
        if (ents[o + 8] | (ents[o + 0x0B] << 8)) == cid
    )
    used = set()
    for _p, t in rows:
        o = at.get(t)
        if o is None:
            continue
        n = cstr(teams[o + 0x170 : o + 0x170 + 70])
        used.add(norm(n))
    free = [n for n in names if norm(n) not in used]
    renamed = 0
    for _p, t in rows:
        o = at.get(t)
        if o is None or not free:
            continue
        n = cstr(teams[o + 0x170 : o + 0x170 + 70])
        if norm(n) in have:
            continue
        new = free.pop(0)
        teams[o + 0x170 : o + 0x170 + 70] = (
            pesdb.game_text(new).encode("utf-8")[:69].ljust(70, b"\0")
        )
        teams[o + 0x372 : o + 0x372 + 4] = code(new).encode().ljust(4, b"\0")
        renamed += 1
    total += renamed
    print(
        "reg %-5s %-38s %2d clubes, %d renombrados"
        % (reg, d["name"][:38], len(rows), renamed)
    )

open(os.path.join(W, "Team.bin"), "wb").write(pesdb.wesys_pack(bytes(teams)))
print("total renombrados:", total)
