import io
p = r"D:\SP Football Life 2026 - copia - copia\SiderAddons\modules\fl26regcid.lua"
s = io.open(p, encoding="utf-8").read()
s = s.replace("""  if ffi then
    ffi.cdef[[ void* fl26_ctx(void*); ]]
    local fn = ffi.cast("void* (*)(void*)", 0x1414b6a60)""",
"""  if ffi then
    local fn = ffi.cast("void* (*)(void*)", 0x1414b6a60)""")
s = s.replace("""  if ffi == nil then log("fl26regcid: global ffi is nil -- set luajit.ext.enabled = 1"); return end""",
"""  if ffi == nil then log("fl26regcid: global ffi is nil -- set luajit.ext.enabled = 1"); return end
  ffi.cdef[[ void* fl26_ctx(void*); ]]""")
io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("cdef movido a init")
