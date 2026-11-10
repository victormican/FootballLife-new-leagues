import io
p = r"D:\SP Football Life 2026 - copia - copia\SiderAddons\modules\fl26regcid.lua"
s = io.open(p, encoding="utf-8").read()
old = """  local cntb = memory.read(bb + COUNT_OFF, 4)"""
new = """  if not told then
    told = true
    log(string.format("fl26regcid: owner=%#x block=%#x", ob, bb))
  end
  local cntb = memory.read(bb + COUNT_OFF, 4)"""
assert old in s
s = s.replace(old, new, 1)
s = s.replace("local map, done = nil, false", "local map, done, told = nil, false, false")
io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("diagnostico anadido")
