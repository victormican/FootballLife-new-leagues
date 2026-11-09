"""Build a small PE with only the FL_2026.exe code regions we need, at their real RVAs.

Ghidra then analyzes ~600 KB instead of 463 MB, and every address matches the retail exe
(image base 0x140000000, same RVAs).  No imports/resources: enough for decompiling the cup
menu, the resolvers, the session loader and the date function.
"""

import struct

SRC = r"D:\SP Football Life 2026 - copia\FL_2026.exe"
DST = r"D:\downloads\FL26-slices.exe"

# original sections (name, VA, vsize, rawptr, rawsize)
d = open(SRC, "rb").read()
pe = struct.unpack_from("<I", d, 0x3C)[0]
nsec = struct.unpack_from("<H", d, pe + 6)[0]
optsz = struct.unpack_from("<H", d, pe + 20)[0]
base = struct.unpack_from("<Q", d, pe + 24 + 24)[0]
secs = []
for i in range(nsec):
    off = pe + 24 + optsz + 40 * i
    name = d[off : off + 8].rstrip(b"\0").decode()
    vsz, va, rsz, rp = struct.unpack_from("<IIII", d, off + 8)
    secs.append((name, va, vsz, rp, rsz))


def raw_at(rva, size):
    for name, va, vsz, rp, rsz in secs:
        if va <= rva < va + max(vsz, rsz):
            start = rp + (rva - va)
            return d[start : start + size], name
    raise SystemExit("rva %x not mapped" % rva)


slices = [
    ("menu", 0x0B10000, 0x30000),
    ("base", 0x0C68000, 0x6000),
    ("keys", 0x0EAC000, 0x6000),
    ("sched", 0x13E0000, 0x10000),
    ("owner", 0x14B5000, 0xC000),
    ("phase", 0x150A000, 0x8000),
    ("draw", 0x1540000, 0x10000),
    ("dates", 0x157F000, 0x2000),
    ("data", 0x339B000, 0x2000),
]

SECT_ALIGN = 0x1000
FILE_ALIGN = 0x200


def align(x, a):
    return (x + a - 1) // a * a


hdr = bytearray(0x400)
hdr[0:2] = b"MZ"
struct.pack_into("<I", hdr, 0x3C, 0x40)
stub = b"This program cannot be run in DOS mode.\r\r\n$"
hdr[0x40 : 0x40 + len(stub)] = stub
hdr[0x80:0x84] = b"PE\0\0"

coff = bytearray(20)
struct.pack_into("<HHIIIHH", coff, 0, 0x8664, len(slices), 0, 0, 0, 0xF0, 0x22)

opt = bytearray(0xF0)
struct.pack_into("<HBBIIIII", opt, 0, 0x20B, 14, 0, 0, 0, 0, 0x1000, 0x1000)
struct.pack_into("<Q", opt, 24, base)
struct.pack_into("<II", opt, 32, SECT_ALIGN, FILE_ALIGN)
struct.pack_into("<HHHHHH", opt, 40, 6, 0, 0, 0, 6, 0)
struct.pack_into("<I", opt, 52, 0)
struct.pack_into("<I", opt, 56, align(max(va + vs for _, va, vs in slices), SECT_ALIGN))
struct.pack_into("<I", opt, 60, 0x400)
struct.pack_into("<H", opt, 68, 3)
struct.pack_into("<H", opt, 70, 0x8160)
struct.pack_into("<Q", opt, 72, 0x100000)
struct.pack_into("<Q", opt, 80, 0x1000)
struct.pack_into("<Q", opt, 88, 0x100000)
struct.pack_into("<Q", opt, 96, 0x1000)
struct.pack_into("<I", opt, 108, 16)
# data directories all zero

out = bytearray()
out += hdr[:0x80]
out += coff
out += opt
# section table (40 bytes each) right after the optional header
sec_table_off = len(out)
out += bytes(40 * len(slices))

file_off = align(len(out), FILE_ALIGN)
out += bytes(file_off - len(out))

sec_headers = bytearray()
for name, va, size in slices:
    raw, src = raw_at(va, size)
    # pad raw to file alignment
    raw = raw + bytes(align(len(raw), FILE_ALIGN) - len(raw))
    ptr = len(out)
    out += raw
    chars = 0x60000020 if name not in ("data",) else 0xC0000040
    h = bytearray(40)
    nm = name.encode()
    h[0 : len(nm)] = nm
    struct.pack_into("<IIII", h, 8, size, va, len(raw), ptr)
    struct.pack_into("<I", h, 36, chars)
    sec_headers += h
    print("%-6s rva %08x size %06x raw %08x (from %s)" % (name, va, size, ptr, src))

out[sec_table_off : sec_table_off + len(sec_headers)] = sec_headers

open(DST, "wb").write(out)
print("wrote", DST, len(out), "bytes")
