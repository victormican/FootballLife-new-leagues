import io
p = r"D:\SP Football Life 2026 - copia - copia\SiderAddons\modules\fl26swiss.lua"
s = io.open(p, encoding="utf-8").read()
s = s.replace("    typedef int  (*fl26_swiss_access_t)(const uint16_t*, int);",
              "    typedef int  (*fl26_swiss_access_t)(const uint16_t*, int);\n    typedef int  (*fl26_swiss_regcid_t)(const uint32_t*, int);")
s = s.replace('local m = tonumber(ffi.cast("fl26_swiss_access_t", prc)(buf, #rc))',
              'local m = tonumber(ffi.cast("fl26_swiss_regcid_t", prc)(buf, #rc))')
io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("tipo corregido:", 'fl26_swiss_regcid_t' in s)
