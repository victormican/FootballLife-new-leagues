import io
import os
import re
import shutil
import sys

T = r"C:\Users\viarm\test-carpeta\pes-2021\tools"
sys.path.insert(0, T)
import pesdb

W = r"D:\SP Football Life 2026 - copia - copia\SiderAddons\livecpk\_FL26MyWorld\common\etc\pesdb"
WF = r"D:\SP Football Life 2026 - copia - copia\SiderAddons\modules\fl26world.txt"
LIVE = r"D:\SP Football Life 2026 - copia - copia\SiderAddons\livecpk\_FL26MyWorld\fl26world.txt"
PATH = os.path.join(W, "CompetitionRegulation.bin")
REC = 2352
NEW = 9000

raw = bytearray(pesdb.wesys_unpack(open(PATH, "rb").read()))


def find(rid):
    for o in range(0, len(raw) - REC + 1, REC):
        if int.from_bytes(raw[o + 2 : o + 4], "little") == rid:
            return o
    return None


o111 = find(111)
o115 = find(115)
assert o111 is not None, "no existe la regulacion 111"
assert o115 is not None, "no existe la regulacion 115"
assert find(NEW) is None, "la regulacion %d ya existe" % NEW

ecu = bytearray(raw[o111 : o111 + REC])
bel = bytearray(raw[o115 : o115 + REC])

ecu[2:4] = NEW.to_bytes(2, "little")
bel[2:4] = (111).to_bytes(2, "little")

# Bélgica pasa a la regulacion 111 (la de la fila que apunta al slot 84)
raw[o111 : o111 + REC] = bel
# Ecuador se va a una regulacion nueva, sin fila de fabrica
raw += ecu

bak = PATH + ".before-belg-fix"
if not os.path.exists(bak):
    shutil.copy2(PATH, bak)
open(PATH, "wb").write(pesdb.wesys_pack(bytes(raw)))
print(
    "reg 111 -> Belgica (cid %d, %r)"
    % (bel[8] | (bel[0x492] << 8), pesdb.cstr(bel[0x14 : 0x14 + 115]))
)
print(
    "reg %d -> Ecuador (cid %d, %r)"
    % (NEW, ecu[8] | (ecu[0x492] << 8), pesdb.cstr(ecu[0x14 : 0x14 + 115]))
)

lines = io.open(WF, encoding="utf-8", errors="replace").read().splitlines()
out, ecu_line, bel_line = [], None, None
for line in lines:
    m = re.match(r"^league\s+111(\s.*)$", line)
    if m and "cid=149" in line:
        ecu_line = ("league %d" % NEW) + m.group(1)
        ecu_line = re.sub(r"\bslot=-?\d+", "slot=209", ecu_line)
        out.append(ecu_line)
        bel_line = (
            "league 111 cid=111 region=8 country=197 conf=2 slot=84 tier=1 "
            "promote=0 demote=0 clubs=16 legs=2 kickoff=99 name=Jupiler Pro League"
        )
        out.append(bel_line)
        continue
    if line.strip() == "pool 84 115":
        continue
    out.append(line)

text = "\n".join(out) + "\n"
io.open(WF, "w", encoding="utf-8", newline="\n").write(text)
io.open(LIVE, "w", encoding="utf-8", newline="\n").write(text)
print("world:")
print("  " + bel_line)
print("  " + ecu_line)
print("  pool 84 115 quitada")
