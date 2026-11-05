import io
import os
import re
import sys

T = r"C:\Users\viarm\test-carpeta\pes-2021\tools"
sys.path.insert(0, T)
import pesdb

W = r"D:\SP Football Life 2026 - copia - copia\SiderAddons\livecpk\_FL26MyWorld\common\etc\pesdb"
WF = r"D:\SP Football Life 2026 - copia - copia\SiderAddons\modules\fl26world.txt"
LIVE = r"D:\SP Football Life 2026 - copia - copia\SiderAddons\livecpk\_FL26MyWorld\fl26world.txt"


def bits(rec, bit, n):
    lo, hi = bit // 8, (bit + n + 7) // 8
    return (int.from_bytes(rec[lo:hi], "little") >> (bit % 8)) & ((1 << n) - 1)


def set_bits(rec, bit, n, v):
    lo, hi = bit // 8, (bit + n + 7) // 8
    x = int.from_bytes(rec[lo:hi], "little")
    m = ((1 << n) - 1) << (bit % 8)
    rec[lo:hi] = ((x & ~m) | ((v << (bit % 8)) & m)).to_bytes(hi - lo, "little")


# row -> flag
raw = pesdb.wesys_unpack(open(os.path.join(W, "Country.bin"), "rb").read())
row2flag = {}
for i in range(len(raw) // 1420):
    d = int.from_bytes(raw[i * 1420 : i * 1420 + 4], "little")
    row2flag[i] = (d >> 10) & 0x1FF

# equipos: los que ya existian antes del remapeo recuperan su valor de entonces
old = pesdb.wesys_unpack(
    open(os.path.join(W, "Team.bin.before-countryids"), "rb").read()
)
oldc = {}
for o in range(0, len(old) - 1531, 1532):
    tid = int.from_bytes(old[o + 8 : o + 12], "little")
    oldc[tid] = bits(old[o : o + 1532], 562, 9)

teams = bytearray(pesdb.wesys_unpack(open(os.path.join(W, "Team.bin"), "rb").read()))
seen_old = seen_new = 0
for o in range(0, len(teams) - 1531, 1532):
    rec = teams[o : o + 1532]
    tid = int.from_bytes(rec[8:12], "little")
    cur = bits(rec, 562, 9)
    if tid in oldc:
        want = oldc[tid]
        seen_old += 1
    else:
        want = row2flag.get(cur, cur)
        seen_new += 1
    if want != cur:
        set_bits(rec, 562, 9, want)
        teams[o : o + 1532] = rec

# world file: los paises de las lineas viejas vuelven a su valor de antes
oldlines = {}
for line in io.open(WF + ".before-countryids", encoding="utf-8", errors="replace"):
    p = line.split()
    if p and p[0] == "league":
        m = re.search(r"country=(\d+)", line)
        if m:
            oldlines[p[1]] = int(m.group(1))

lines = io.open(WF, encoding="utf-8", errors="replace").read().splitlines()
out, changed, dropped = [], 0, 0
for line in lines:
    p = line.split()
    if p and p[0] == "league" and p[1] == "115":
        dropped += 1
        continue
    if p and p[0] == "league" and p[1] in oldlines:

        def sub(m):
            global changed
            v = int(m.group(1))
            r = oldlines[p[1]]
            if r != v:
                changed += 1
            return "country=%d" % r

        line = re.sub(r"country=(\d+)", sub, line, count=1)
    elif p and p[0] == "league":

        def sub2(m):
            global changed
            v = int(m.group(1))
            r = row2flag.get(v, v)
            if r != v:
                changed += 1
            return "country=%d" % r

        line = re.sub(r"country=(\d+)", sub2, line, count=1)
    out.append(line)

open(os.path.join(W, "Team.bin"), "wb").write(pesdb.wesys_pack(bytes(teams)))
text = "\n".join(out) + "\n"
io.open(WF, "w", encoding="utf-8", newline="\n").write(text)
io.open(LIVE, "w", encoding="utf-8", newline="\n").write(text)
print("equipos: %d viejos restaurados, %d nuevos mapeados" % (seen_old, seen_new))
print(
    "world: %d valores de pais cambiados, linea belga quitada: %d" % (changed, dropped)
)
