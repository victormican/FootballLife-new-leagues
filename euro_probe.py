import sys, os, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0,"tools")
import pesdb
BASE = r"D:\SP Football Life 2026 - copia - copia\SiderAddons\livecpk\_FL26MyWorld\common\etc\pesdb"
regs = pesdb.wesys_unpack(open(os.path.join(BASE,"CompetitionRegulation.bin"),"rb").read())
ents = pesdb.wesys_unpack(open(os.path.join(BASE,"CompetitionEntry.bin"),"rb").read())
import collections
n = collections.Counter(ents[i+8] | (ents[i+11]<<8) for i in range(0,len(ents),12))
for cid, label in ((33,"UEFA EURO"), (34,"Copa America"), (27,"FIFA World Cup"), (2,"Champions"), (96,"Gold Cup"), (250,"OFC Nations")):
    rs = []
    for i in range(0,len(regs),2352):
        r = regs[i:i+2352]
        if (r[8] | (r[0x492]<<8)) == cid:
            rs.append(dict(reg=int.from_bytes(r[2:4],"little"), group=r[0x0a],
                           teams=r[0x0b]&0x3f, type=r[0x09],
                           tier=int.from_bytes(r[0x10:0x14],"little"),
                           name=r[0x14:0x14+0x40].split(b"\x00")[0].decode("utf-8","replace")))
    print("%-16s cid %3d  entradas %2d  regs %d" % (label, cid, n.get(cid,0), len(rs)))
    for x in rs:
        print("     reg %5d group %3d teams %2d type %d tier %08x %r" %
              (x["reg"], x["group"], x["teams"], x["type"], x["tier"], x["name"]))
