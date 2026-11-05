import io
import os
import shutil
import sys

T = r"C:\Users\viarm\test-carpeta\pes-2021\tools"
sys.path.insert(0, T)
import pesdb

W = r"D:\SP Football Life 2026 - copia - copia\SiderAddons\livecpk\_FL26MyWorld\common\etc\pesdb"
WF = r"D:\SP Football Life 2026 - copia - copia\SiderAddons\modules\fl26world.txt"
LIVE = r"D:\SP Football Life 2026 - copia - copia\SiderAddons\livecpk\_FL26MyWorld\fl26world.txt"
COMP, REG, ENT = 36, 2352, 12

comp = bytearray(
    pesdb.wesys_unpack(open(os.path.join(W, "Competition.bin"), "rb").read())
)
regs = bytearray(
    pesdb.wesys_unpack(open(os.path.join(W, "CompetitionRegulation.bin"), "rb").read())
)
ents = bytearray(
    pesdb.wesys_unpack(open(os.path.join(W, "CompetitionEntry.bin"), "rb").read())
)


def code(row):
    return bytes(row[8:36]).split(b"\0")[0].decode("latin1", "replace")


drop_cids = set()
keep_comp = bytearray()
ncomp = 0
for o in range(0, len(comp) - COMP + 1, COMP):
    row = comp[o : o + COMP]
    cid = row[5] | (row[7] << 8)
    if code(row).startswith("FL_DUP_"):
        drop_cids.add(cid)
        continue
    keep_comp += row
    ncomp += 1

keep_regs = bytearray()
nreg = 0
for o in range(0, len(regs) - REG + 1, REG):
    row = regs[o : o + REG]
    cid = row[8] | (row[0x492] << 8)
    if cid in drop_cids:
        continue
    keep_regs += row
    nreg += 1

keep_ents = bytearray()
nent = 0
for o in range(0, len(ents) - ENT + 1, ENT):
    row = ents[o : o + ENT]
    cid = row[8] | (row[0x0B] << 8)
    if cid in drop_cids:
        continue
    keep_ents += row
    nent += 1

print("competiciones FL_DUP:", len(drop_cids))
print(
    "antes: %d comps, %d regs, %d entradas"
    % (len(comp) // COMP, len(regs) // REG, len(ents) // ENT)
)
print("despues: %d comps, %d regs, %d entradas" % (ncomp, nreg, nent))

for name, old, new in (
    ("Competition.bin", comp, keep_comp),
    ("CompetitionRegulation.bin", regs, keep_regs),
    ("CompetitionEntry.bin", ents, keep_ents),
):
    p = os.path.join(W, name)
    bak = p + ".before-cleanup"
    if not os.path.exists(bak):
        shutil.copy2(p, bak)
    open(p, "wb").write(pesdb.wesys_pack(bytes(new)))

lines = io.open(WF, encoding="utf-8", errors="replace").read().splitlines()
keep = [
    l
    for l in lines
    if not (l.startswith("ccup ") and l.split("name=", 1)[-1].strip().endswith(" II"))
]
text = "\n".join(keep) + "\n"
for p in (WF, LIVE):
    bak = p + ".before-cleanup"
    if not os.path.exists(bak):
        shutil.copy2(p, bak)
    io.open(p, "w", encoding="utf-8", newline="\n").write(text)
print("ccup:", len([l for l in keep if l.startswith("ccup ")]))
