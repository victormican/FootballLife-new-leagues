import io
# el Lua: sustituir los huecos buscando el valor de relleno, no por offset
for p in (r"D:\SP Football Life 2026 - copia - copia\SiderAddons\modules\fl26cupgrow.lua",
          r"C:\Users\viarm\test-carpeta\pes-2021\sider\experimental\fl26cupgrow.lua"):
    s = io.open(p, encoding="utf-8").read()
    a = s.index("  local s = bin(VSTUB)")
    b = s.index("  memory.write(vstub, s)")
    new = """  local s = bin(VSTUB)
  -- los huecos se localizan por su contenido: el stub cambia de tamano al tocarlo y los
  -- offsets fijos dejaban de caer donde tocaba (crash 0x161100238, 2026-11-04)
  local ring_ph, prev_ph = u64(0x161100100), u64(0x7ffed65551f0)
  local r1 = s:find(ring_ph, 1, true)
  local r2 = s:find(prev_ph, 1, true)
  if not r1 or not r2 then log("fl26cupgrow: no encuentro los huecos del stub"); return end
  s = s:sub(1, r1 - 1) .. u64(ring) .. s:sub(r1 + 8)
  s = s:sub(1, r2 - 1) .. u64(prev) .. s:sub(r2 + 8)
"""
    s = s[:a] + new + s[b:]
    io.open(p, "w", encoding="utf-8", newline="\n").write(s)
    print("lua parcheado", p)
