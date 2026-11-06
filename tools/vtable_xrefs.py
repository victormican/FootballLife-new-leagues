"""vtable_xrefs -- who builds an object of this class, and what that constructor does.

The constructor stores the class vtable into the object (`lea rax, [rip+vt]` + `mov [rcx], rax`),
so finding the rip-relative references to the vtable gives the constructor (and every other place
that names the class: factories, RTTI helpers).  Each hit is printed with the function it belongs
to and the calls it makes, which is how a menu's item list is read: every "add item" is a call
with a text id.

    python vtable_xrefs.py MenuEditLgCpMain 0x1426ef848
"""

import struct
import sys

import capstone

EXE = r"D:\SP Football Life 2026 - copia\FL_2026.exe"
IMG = 0x140000000


def load():
    d = open(EXE, "rb").read()
    pe = struct.unpack_from("<I", d, 0x3C)[0]
    nsec = struct.unpack_from("<H", d, pe + 6)[0]
    opt = pe + 24
    sec = opt + struct.unpack_from("<H", d, pe + 20)[0]
    secs = []
    for i in range(nsec):
        o = sec + i * 40
        name = d[o : o + 8].rstrip(b"\0").decode("ascii", "replace")
        vsize, va, rsize, roff = struct.unpack_from("<IIII", d, o + 8)
        secs.append((name, va, vsize, roff, rsize))
    return d, secs


def foff(secs, va):
    r = va - IMG
    for name, sva, vsize, roff, rsize in secs:
        if sva <= r < sva + rsize:
            return roff + (r - sva)
    return None


def main():
    name = sys.argv[1]
    vt = int(sys.argv[2], 16)
    d, secs = load()
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
    md.detail = True
    nm, tva, tvs, tro, trs = secs[0]
    blob = d[tro : tro + trs]
    hits = []
    for ins in md.disasm(blob, tva):
        for op in ins.operands:
            if (
                op.type == capstone.x86.X86_OP_MEM
                and op.mem.base == capstone.x86.X86_REG_RIP
            ):
                tgt = ins.address + ins.size + op.mem.disp
                if tgt == vt - IMG:
                    hits.append(ins.address)
    print("%s vtable 0x%x: %d reference(s)" % (name, vt, len(hits)))
    for h in hits:
        print("  at %x (+%x)" % (h + IMG, h))


if __name__ == "__main__":
    main()
