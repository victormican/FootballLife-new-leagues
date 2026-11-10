import sys, os, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0,"tools")
import pesdb
base = r"D:\SP Football Life 2026 - copia - copia\SiderAddons\livecpk\_FL26MyWorld\common\etc\pesdb"
comp = pesdb.wesys_unpack(open(os.path.join(base,"Competition.bin"),"rb").read())
for cid in (1, 2, 15, 27, 33, 229, 600, 700):
    for i in range(0,len(comp),36):
        r = comp[i:i+36]
        if (r[5] | (r[7]<<8)) == cid:
            print("cid %3d: %s" % (cid, " ".join("%02x"%b for b in r[:0x24])))
            print("        ascii: %r" % r[:0x24].decode("latin1"))
            break
