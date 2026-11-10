import io
p = r"D:\SP Football Life 2026 - copia - copia\SiderAddons\modules\fl26regcid.lua"
s = io.open(p, encoding="utf-8").read()
old = """        local cnt = memory.read(bval + COUNT_OFF, 4)
        local first = memory.read(bval + ARRAY_OFF, 4)"""
new = """        local cnt = memory.read(bval + COUNT_OFF, 4)
        local first = memory.read(bval + ARRAY_OFF, 4)
        if not dumped then
          dumped = true
          local function hexdump(off, n, tag)
            local b = memory.read(bval + off, n)
            if not b then log("fl26regcid: " .. tag .. " sin memoria"); return end
            local t = {}
            for i = 0, math.min(n, 32) - 1, 4 do
              t[#t + 1] = string.format("%08x", u32(b, i))
            end
            log(string.format("fl26regcid: %s +%#x: %s", tag, off, table.concat(t, " ")))
          end
          hexdump(COUNT_OFF - 0x20, 32, "count-0x20")
          hexdump(COUNT_OFF, 32, "count")
          hexdump(ARRAY_OFF, 32, "array")
        end"""
assert old in s
s = s.replace(old, new, 1)
s = s.replace("local map, done, told = nil, false, false", "local map, done, told, dumped = nil, false, false, false")
io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("volcado anadido")
