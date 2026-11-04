"""Rebuild the fl26cupgrow vtable stub with sanity guards.

The stub grows the Cup menu's list to 256 items, but the same vtable slot is reached from the
cup detail screens with a different object: without guards it copied `end - begin` bytes from
whatever those fields were and closed the game (0x161efa600 = inside the stub, 2026-11-04).

Guards: begin, end and cap must be non-null; begin < end; end <= cap; and the list must be
smaller than 85 items before it is grown.  Anything else tail-calls the previous handler
untouched.
"""

import struct, textwrap, io

RING = 0x161100100
PREV = 0x7FFED65551F0
BASE = 0x161100200
CAP = 0xC00  # 256 items x 12 bytes

items = []


def B(h, label=None):
    items.append(("b", bytes.fromhex(h), label))


def J(cc, label):
    items.append(("j", cc, label))


def L(label):
    items.append(("l", label))


B("51")  # push rcx
B("52")  # push rdx
B("56")  # push rsi
B("57")  # push rdi
B("4157")  # push r15
B("4989cf")  # mov r15, rcx
B("48b8402c694201000000")            # mov rax, 0x142692c40 (vtable MenuModeCupSelect)
B("483b01"); J("85", "done")             # cmp rax,[rcx] ; jne done
B("498b8790000000")  # mov rax, [r15+0x90]      begin
B("4885c0")
J("84", "done")  # test rax,rax ; jz done
B("498b8f98000000")  # mov rcx, [r15+0x98]      end
B("4885c9")
J("84", "done")  # test rcx,rcx ; jz done
B("4d8b9fa0000000")  # mov r11, [r15+0xa0]      cap
B("4d85db")
J("84", "done")  # test r11,r11 ; jz done
B("483bc1")
J("83", "done")  # cmp rax,rcx ; jae done    begin >= end
B("4c3bd9")
J("86", "done")  # cmp r11,rcx ; jbe done    cap <= end
B("4889c2")  # mov rdx, rax              keep begin
B("4929c3")  # sub r11, rax              cap - begin
B("4981fb00040000")
J("83", "done")  # cmp r11, 0x400 ; jae done  already grown
B("49ba")
B(struct.pack("<Q", RING).hex())  # mov r10, ring
B("498b8280000000")  # mov rax, [r10+0x80]       index
B("4883f810")
J("83", "done")  # cmp rax,16 ; jae done
B("4983828000000001")  # add qword [r10+0x80], 1
B("4d8b1cc2")  # mov r11, [r10+rax*8]      buffer
B("4d85db")
J("84", "done")  # test r11,r11 ; jz done
B("4889d6")  # mov rsi, rdx              src = begin
B("498b8f98000000")  # mov rcx, [r15+0x98]       end
B("4829d1")  # sub rcx, rdx              len
B("4c89df")  # mov rdi, r11
B("f3a4")  # rep movsb
B("498b8798000000")  # mov rax, [r15+0x98]
B("492b8790000000")  # sub rax, [r15+0x90]
B("4d899f90000000")  # mov [r15+0x90], r11       begin = buffer
B("498d0c03")  # lea rcx, [r11+rax]        end
B("49898f98000000")  # mov [r15+0x98], rcx
B("498d8b" + struct.pack("<I", CAP).hex())  # lea rcx, [r11+CAP]
B("49898fa0000000")  # mov [r15+0xa0], rcx       cap
L("done")
B("415f")  # pop r15
B("5f")  # pop rdi
B("5e")  # pop rsi
B("5a")  # pop rdx
B("59")  # pop rcx
B("48b8")
B(struct.pack("<Q", PREV).hex())  # mov rax, prev
B("ffe0")  # jmp rax

addr = {}
cur = BASE
for it in items:
    if it[0] == "b":
        cur += len(it[1])
    elif it[0] == "j":
        cur += 6
    else:
        addr[it[1]] = cur
out = b""
cur = BASE
for it in items:
    if it[0] == "b":
        out += it[1]
        cur += len(it[1])
    elif it[0] == "j":
        out += bytes([0x0F, int(it[1], 16)]) + struct.pack(
            "<i", addr[it[2]] - (cur + 6)
        )
        cur += 6
print("stub bytes:", len(out))
h = out.hex()
lines = textwrap.wrap(h, 88)
body = ",\n".join('              "%s"' % l for l in lines).replace('",\n', '" ..\n')

for p in (
    r"D:\SP Football Life 2026 - copia - copia\SiderAddons\modules\fl26cupgrow.lua",
    r"C:\Users\viarm\test-carpeta\pes-2021\sider\experimental\fl26cupgrow.lua",
):
    s = io.open(p, encoding="utf-8").read()
    a = s.index("local VSTUB =")
    b = s.index("-- 60 bytes:")
    s = s[:a] + "local VSTUB = " + body + "\n\n" + s[b:]
    s = s.replace("local WANT, RING = 64, 16", "local WANT, RING = 256, 16")
    io.open(p, "w", encoding="utf-8", newline="\n").write(s)
    print("escrito", p)
open("vstub_guard.bin", "wb").write(out)
