import io
p = r"D:\SP Football Life 2026 - copia - copia\SiderAddons\modules\fl26swiss.lua"
s = io.open(p, encoding="utf-8").read()
anchor = """          local olen, nopt = 0, 0"""
add = """          -- 2026-11-04: el cid completo en cada registro vivo de regulacion, para que phkind lo
          -- encuentre (el registro solo lleva el byte bajo).  El mapa reg->cid sale del mundo.
          do
            local prc = ffi.C.GetProcAddress(h, "fl26_swiss_regcid")
            if prc == nil then
              log("fl26swiss: this fl26swiss.dll has no fl26_swiss_regcid (rebuild it)")
            else
              local pairs = {}
              for line in io.lines(path) do
                local reg = line:match("^%s*([%a]+)%s+(%d+)")
                local cid = line:match("%scid=(%d+)")
                if cid and (reg == "league" or reg == "ccup") then
                  pairs[#pairs + 1] = tonumber((line:match("^%s*%a+%s+(%d+)")))
                  pairs[#pairs + 1] = tonumber(cid)
                end
              end
              local n = math.floor(#pairs / 2)
              if n > 0 then
                local buf = ffi.new("uint32_t[?]", #pairs)
                for i = 1, #pairs do buf[i - 1] = pairs[i] end
                local m = tonumber(ffi.cast("fl26_swiss_access_t", prc)(buf, #pairs))
                log(string.format("fl26swiss: %d reg->cid pair(s) handed to the DLL", m))
              end
            end
          end
          local olen, nopt = 0, 0"""
assert anchor in s
s = s.replace(anchor, add, 1)
io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("lua enlazado")
