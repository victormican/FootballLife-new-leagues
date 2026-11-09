import ctypes
import struct
import sys

pid = int(sys.argv[1])
k = ctypes.windll.kernel32
PROCESS_VM_READ = 0x10
PROCESS_QUERY_INFORMATION = 0x400

h = k.OpenProcess(PROCESS_VM_READ | PROCESS_QUERY_INFORMATION, False, pid)
if not h:
    raise SystemExit("OpenProcess failed %d" % ctypes.get_last_error())

BASE = 0x140000000


def rd(addr, size):
    buf = ctypes.create_string_buffer(size)
    n = ctypes.c_size_t()
    ok = k.ReadProcessMemory(h, ctypes.c_void_p(addr), buf, size, ctypes.byref(n))
    if not ok:
        raise SystemExit(
            "ReadProcessMemory %x failed %d" % (addr, ctypes.get_last_error())
        )
    return buf.raw[: n.value]


def u64(addr):
    return struct.unpack("<Q", rd(addr, 8))[0]


def u32(addr):
    return struct.unpack("<I", rd(addr, 4))[0]


owner = u64(BASE + 0x3705E10)
print("owner", hex(owner))
if owner:
    block = u64(owner + 0x48)
    print(
        "block",
        hex(block),
        "mode",
        u32(block + 0x183789C),
        "count",
        u32(block + 0xD0BCF4),
    )
    rows = []
    for i in range(0x12C):
        r = block + 0xC12E9C + i * 0x314
        key = struct.unpack("<H", rd(r, 2))[0]
        if key in (0, 0xFFFF):
            continue
        cid = u32(r + 0x80)
        if cid == 131 or key in (200, 1071, 46):
            rows.append((i, key, cid, u32(r + 0x84)))
    print("slots", rows)

state_obj = u64(BASE + 0x36FED48)
print("state_obj", hex(state_obj))
if state_obj:
    print("state [obj+0x78]", u32(state_obj + 0x78))
