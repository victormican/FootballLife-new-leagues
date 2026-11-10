import io
p = r"D:\SP Football Life 2026 - copia - copia\SiderAddons\modules\fl26comptab.lua"
s = io.open(p, encoding="utf-8").read()
marker = """    log(string.format("fl26comptab: name labels cleared on %d rows that had borrowed one, "
                      .. "League Info text on %d", cleared, texts))
  end"""
add = """
  -- PRUEBA TEMPORAL (2026-11-04 17:4x): cuatro copas apuntadas a las cuatro primeras entradas del
  -- bloque de nombres de <idioma>/string/all.str ("League", "Eredivisie", "Spanish League",
  -- "Africa") para ver si OFF_NAME (+0x38) es el indice de ese bloque.
  do
    local probe = { [700] = 0, [701] = 1, [702] = 2, [703] = 3 }
    for id, idx in pairs(probe) do
      local i = byid[id]
      if i then rows[i] = row_set(rows[i], OFF_NAME, u32le(idx)) end
    end
    log("fl26comptab: PRUEBA -- 4 copas con OFF_NAME 0..3")
  end
"""
assert marker in s
s = s.replace(marker, marker + add, 1)
io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("prueba insertada")
