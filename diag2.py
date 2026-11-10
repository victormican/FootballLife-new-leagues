import io
p = r"D:\SP Football Life 2026 - copia - copia\SiderAddons\modules\fl26regcid.lua"
s = io.open(p, encoding="utf-8").read()
old = """  if not told then
    told = true
    log(string.format("fl26regcid: owner=%#x block=%#x", ob, bb))
  end
  local cntb = memory.read(bb + COUNT_OFF, 4)
  if not cntb then return end
  local n = u32(cntb, 0)"""
new = """  local cntb = memory.read(bb + COUNT_OFF, 4)
  if not cntb then return end
  local n = u32(cntb, 0)
  if not told then
    told = true
    local first = memory.read(bb + ARRAY_OFF, 4)
    log(string.format("fl26regcid: owner=%#x block=%#x count=%d firstid=%s", ob, bb, n,
                      first and (first:byte(1) + first:byte(2) * 256) or "?"))
  end"""
assert old in s
s = s.replace(old, new, 1)
io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("diagnostico de cuenta listo")
