"""rtti_vtables -- class name -> vtable -> virtual slots, straight from the shipped exe.

The exe keeps MSVC RTTI: every polymorphic class has a TypeDescriptor (".?AVName@@"), a
CompleteObjectLocator pointing at it, and a vtable whose slot -1 points at the locator.  That is
enough to walk from a class name to its virtual functions without a full disassembly:

    python rtti_vtables.py MenuModeCupSelect TeamSelectCommon MenuEditMenu ...

For each class it prints the vtable address and one line per slot (address, and whether the target
lands in the code section).  The slot number is the offset the DLLs use (0xd8, 0x20, ...).
"""

import re
import struct
import sys

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


def to_off(secs, va):
    r = va - IMG
    for name, sva, vsize, roff, rsize in secs:
        if sva <= r < sva + max(vsize, rsize):
            return roff + (r - sva)
    return None


def to_va(secs, off):
    for name, sva, vsize, roff, rsize in secs:
        if roff <= off < roff + rsize:
            return IMG + sva + (off - roff)
    return None


def section_of(secs, off):
    for name, sva, vsize, roff, rsize in secs:
        if roff <= off < roff + rsize:
            return name
    return None


def find_class(d, secs, name):
    """Find the TypeDescriptor of a class by (possibly partial) name.

    Names are namespace-qualified ("MenuModeCupSelect@menu"), so a bare "MenuModeCupSelect" is
    matched against the whole RTTI name, not against a fixed suffix.
    """
    best = None
    for m in re.finditer(rb"\.\?AV[A-Za-z0-9_@?$]{3,90}@@", d):
        full = m.group(0)[4:-2].decode("ascii", "replace")
        base = full.split("@")[0]
        if full == name or base == name or name in full:
            best = m.start()
            if base == name:
                break
    if best is None:
        return None, None
    td_va = to_va(secs, best) - 16  # TypeDescriptor: vfptr, spare, name
    return best, td_va


def find_vtable(d, secs, td_va):
    td_rva = struct.pack("<I", td_va - IMG)
    rdata = [s for s in secs if s[0] == ".rdata"]
    for name, sva, vsize, roff, rsize in rdata:
        blob = d[roff : roff + rsize]
        k = 0
        while True:
            k = blob.find(td_rva, k)
            if k < 0:
                break
            col_off = roff + k - 12
            if col_off >= roff:
                sig, off, cd = struct.unpack_from("<III", d, col_off)
                if sig == 1:
                    col_va = to_va(secs, col_off)
                    q = struct.pack("<Q", col_va)
                    j = 0
                    while True:
                        j = blob.find(q, j)
                        if j < 0:
                            break
                        vt_va = to_va(secs, roff + j) + 8
                        if vt_va:
                            return vt_va
                        j += 1
            k += 1
    return None


def dump(d, secs, name):
    pos, td_va = find_class(d, secs, name)
    if td_va is None:
        print("%-28s <no RTTI>" % name)
        return
    vt = find_vtable(d, secs, td_va)
    if vt is None:
        print("%-28s td %x" % (name, td_va))
        return
    off = to_off(secs, vt)
    print("%s  td %x  vtable %x" % (name, td_va, vt))
    for i in range(0, 0x180, 8):
        try:
            slot = struct.unpack_from("<Q", d, off + i)[0]
        except struct.error:
            break
        if slot == 0:
            print("  +%03x 0" % i)
            continue
        where = section_of(secs, to_off(secs, slot)) if to_off(secs, slot) else None
        if where is None:
            print("  +%03x %x  (outside)" % (i, slot))
        else:
            print("  +%03x %x  (+%x) %s" % (i, slot, slot - IMG, where))


if __name__ == "__main__":
    d, secs = load()
    for name in sys.argv[1:]:
        dump(d, secs, name)
