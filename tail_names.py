import sys, os, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0,"tools")
import pesdb
base = r"D:\SP Football Life 2026 - copia - copia\SiderAddons\livecpk\_FL26MyWorld\common\etc\pesdb"
comp = pesdb.wesys_unpack(open(os.path.join(base,"Competition.bin"),"rb").read())
regs = pesdb.wesys_unpack(open(os.path.join(base,"CompetitionRegulation.bin"),"rb").read())
rows = {}
for i in range(0,len(comp),36):
    r = comp[i:i+36]; rows[r[5] | (r[7]<<8)] = r
rname = {}
for i in range(0,len(regs),2352):
    r = regs[i:i+2352]; rname.setdefault(r[8] | (r[0x492]<<8), r[0x14:0x14+0x73].split(b"\x00")[0].decode("utf-8","replace"))
last = sorted(rows)[-12:]
for c in last:
    r = rows[c]
    print("cid %3d  code %-10r  +0x14 %-18r reg %r" % (c, r[8:36].split(b"\x00")[0].decode("latin1"), r[0x14:0x24].split(b"\x00")[0].decode("utf-8","replace"), rname.get(c)))
