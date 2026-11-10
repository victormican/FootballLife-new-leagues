import sys, os, io, re, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0,"tools")
import pesdb
BASE = r"D:\SP Football Life 2026 - copia - copia\SiderAddons\livecpk\_FL26MyWorld\common\etc\pesdb"
WF   = r"D:\SP Football Life 2026 - copia - copia\SiderAddons\livecpk\_FL26MyWorld\fl26world.txt"
regs = pesdb.wesys_unpack(open(os.path.join(BASE,"CompetitionRegulation.bin"),"rb").read())
ents = pesdb.wesys_unpack(open(os.path.join(BASE,"CompetitionEntry.bin"),"rb").read())
def reg(rid):
    for i in range(0,len(regs),2352):
        r = regs[i:i+2352]
        if int.from_bytes(r[2:4],"little") == rid:
            return dict(type=r[9], group=r[0x0a], teams=r[0x0b]&0x3f,
                        name=r[0x14:0x14+0x73].split(b"\x00")[0].decode("utf-8","replace"))
    return None
n_ent = collections.Counter(ents[i+8] | (ents[i+11]<<8) for i in range(0,len(ents),12))
rows = []
for line in io.open(WF, encoding="utf-8", errors="replace").read().splitlines():
    if not line.startswith("ccup ") or line.lstrip().startswith("#"): continue
    w = line.split()
    reg_id = int(w[1]); ko = int(re.search(r"ko=(\d+)", line).group(1)); groups = int(re.search(r"groups=(\d+)", line).group(1))
    cid = int(re.search(r"\bcid=(\d+)", line).group(1)) if "cid=" in line else 0
    like = re.search(r"like=(\d+)", line)
    name = line.split("name=",1)[1]
    rg, rk = reg(reg_id), reg(ko)
    e = n_ent.get(cid, 0)
    issue = []
    if not rg: issue.append("reg %d NO existe" % reg_id)
    if not rk: issue.append("ko %d NO existe" % ko)
    if rg and rg["teams"] != e and groups == 0: issue.append("reg dice %d equipos, hay %d entradas" % (rg["teams"], e))
    if rg and groups and rg["group"] != 255: issue.append("reg de grupos con group=%d" % rg["group"])
    if rk and rk["type"] not in (2,3): issue.append("ko tipo %d" % rk["type"])
    rows.append((name, cid, reg_id, ko, groups, like.group(1) if like else "-", e, rg, rk, issue))
print("%-34s %4s %4s %4s %2s %4s %3s %s" % ("copa","cid","reg","ko","gr","like","ent","avisos"))
bad = 0
for name, cid, reg_id, ko, groups, like, e, rg, rk, issue in rows:
    if issue:
        bad += 1
        print("%-34s %4d %4d %4d %2d %4s %3d %s" % (name[:34], cid, reg_id, ko, groups, like, e, "; ".join(issue)))
print("\ncopas: %d | con aviso: %d" % (len(rows), bad))
