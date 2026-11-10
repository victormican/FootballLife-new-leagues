import sys, os, io, re, shutil
sys.path.insert(0,"tools")
import pesdb
BASE = r"D:\SP Football Life 2026 - copia - copia\SiderAddons\livecpk\_FL26MyWorld\common\etc\pesdb"
WF   = r"D:\SP Football Life 2026 - copia - copia\SiderAddons\livecpk\_FL26MyWorld\fl26world.txt"
WF2  = r"D:\SP Football Life 2026 - copia - copia\SiderAddons\modules\fl26world.txt"
ents = pesdb.wesys_unpack(open(os.path.join(BASE,"CompetitionEntry.bin"),"rb").read())
ids = {}
for i in range(0,len(ents),12):
    t = int.from_bytes(ents[i:i+4],"little")
    if t: ids.setdefault(ents[i+8] | (ents[i+11]<<8), []).append(t)
ls = io.open(WF, encoding="utf-8", errors="replace").read().splitlines()
n_fix = 0
for n, l in enumerate(ls):
    if not l.startswith("ccup ") or " clubs=" not in l: continue
    cid = int(re.search(r"\bcid=(\d+)", l).group(1))
    if cid >= 146: continue
    full = ids.get(cid, [])
    head = re.sub(r" entry=[^ ]*", " entry=" + ",".join("0:%d" % t for t in full), l.split(" clubs=",1)[0])
    tail = l.split(" clubs=",1)[1].split(" ", 1)[1]
    new = head + " clubs=" + ",".join(str(t) for t in full) + " " + tail
    if new != l:
        ls[n] = new; n_fix += 1
io.open(WF, "w", encoding="utf-8", newline="\n").write("\n".join(ls) + "\n")
shutil.copy2(WF, WF2)
print("lineas restauradas:", n_fix)
