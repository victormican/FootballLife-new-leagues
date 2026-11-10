import sys, os, io, zlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0,"tools")
import pesdb
f = r"C:\Users\viarm\AppData\Local\Temp\opencode\cpktext\eng\string\all.str"
b = pesdb.wesys_unpack(open(f,"rb").read())
print("descomprimido:", len(b), b[:32].hex(" "))
i = b.find(b"FIFA Club World Cup")
print("FIFA Club World Cup en", i)
if i >= 0:
    print("contexto:", b[max(0,i-48):i+40].hex(" "))
    print("ascii:", b[max(0,i-48):i+40].decode("latin1"))
j = b.find(b"FIFA Club World Cup".decode("utf-16-le").encode("utf-16-le"))
print("utf16 en", j)
open(r"C:\Users\viarm\AppData\Local\Temp\opencode\eng.str","wb").write(b)
