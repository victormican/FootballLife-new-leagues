import io
import os
import re
import sys
import unicodedata

T = r"C:\Users\viarm\test-carpeta\pes-2021\tools"
sys.path.insert(0, T)
import pesdb

W = r"D:\SP Football Life 2026 - copia - copia\SiderAddons\livecpk\_FL26MyWorld\common\etc\pesdb"
WF = r"D:\SP Football Life 2026 - copia - copia\SiderAddons\modules\fl26world.txt"


def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()
    return " ".join("".join(c if c.isalnum() else " " for c in s.lower()).split())


def cstr(b):
    return bytes(b).split(b"\0")[0].decode("utf-8", "replace").strip()


regs = pesdb.wesys_unpack(
    open(os.path.join(W, "CompetitionRegulation.bin"), "rb").read()
)
rname = {}
for o in range(0, len(regs) - 2351, 2352):
    rid = int.from_bytes(regs[o + 2 : o + 4], "little")
    rname[rid] = cstr(regs[o + 0x14 : o + 0x14 + 115])

lines = io.open(WF, encoding="utf-8", errors="replace").read().splitlines()
fixed = 0
for i, line in enumerate(lines):
    m = re.match(r"^(league|ccup)\s+(\d+)(.*)name=(.*)$", line)
    if not m:
        continue
    kind, rid, mid, name = m.group(1), int(m.group(2)), m.group(3), m.group(4).strip()
    real = rname.get(rid)
    if not real:
        continue
    if norm(real) != norm(name):
        lines[i] = "%s %d%sname=%s" % (kind, rid, mid, real)
        fixed += 1
        if fixed <= 10:
            print("  %-6s %-5d %-34s -> %s" % (kind, rid, name[:34], real))
print("lineas corregidas:", fixed)

text = "\n".join(lines) + "\n"
dst = WF + ".before-names"
if not os.path.exists(dst):
    import shutil

    shutil.copy2(WF, dst)
io.open(WF, "w", encoding="utf-8", newline="\n").write(text)
live = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(W)))),
    "fl26world.txt",
)
if os.path.abspath(live) != os.path.abspath(WF):
    io.open(live, "w", encoding="utf-8", newline="\n").write(text)
print("escrito en modules y livecpk")
