import sys, os, io, re, shutil
sys.path.insert(0,"tools")
import pesdb
BASE = r"D:\SP Football Life 2026 - copia - copia\SiderAddons\livecpk\_FL26MyWorld\common\etc\pesdb"
WF   = r"D:\SP Football Life 2026 - copia - copia\SiderAddons\livecpk\_FL26MyWorld\fl26world.txt"
WF2  = r"D:\SP Football Life 2026 - copia - copia\SiderAddons\modules\fl26world.txt"
regs = pesdb.wesys_unpack(open(os.path.join(BASE,"CompetitionRegulation.bin"),"rb").read())
ents = pesdb.wesys_unpack(open(os.path.join(BASE,"CompetitionEntry.bin"),"rb").read())
def teams(rid):
    for i in range(0,len(regs),2352):
        r = regs[i:i+2352]
        if int.from_bytes(r[2:4],"little") == rid: return r[0x0b] & 0x3f
    return None
ids = {}
for i in range(0,len(ents),12):
    t = int.from_bytes(ents[i:i+4],"little")
    if t: ids.setdefault(ents[i+8] | (ents[i+11]<<8), []).append(t)
ls = io.open(WF, encoding="utf-8", errors="replace").read().splitlines()
fixed = 0
for n, l in enumerate(ls):
    if not l.startswith("ccup ") or " clubs=" not in l: continue
    cid = int(re.search(r"\bcid=(\d+)", l).group(1))
    if cid >= 146: continue          # solo las del juego que desbloqueamos
    reg_id = int(l.split()[1])
    want = teams(reg_id) or teams(cid)
    have = [int(x) for x in l.split(" clubs=",1)[1].split()[0].split(",") if x.strip()]
    if not want or len(have) == want: continue
    keep = ids.get(cid, [])[:want]
    if len(keep) < want: continue
    head = re.sub(r" entry=[^ ]*", " entry=" + ",".join("0:%d" % t for t in keep), l.split(" clubs=",1)[0])
    tail = l.split(" clubs=",1)[1].split(" ", 1)[1]
    ls[n] = head + " clubs=" + ",".join(str(t) for t in keep) + " " + tail
    fixed += 1
    print("cid %3d: lista %d -> %d equipos (los de su regulación)" % (cid, len(have), want))
io.open(WF, "w", encoding="utf-8", newline="\n").write("\n".join(ls) + "\n")
shutil.copy2(WF, WF2)
print("lineas ajustadas:", fixed)
