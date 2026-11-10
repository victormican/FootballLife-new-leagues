import io
p = r"D:\SP Football Life 2026 - copia - copia\SiderAddons\modules\fl26swiss.lua"
s = io.open(p, encoding="utf-8").read()
old = """              local pairs = {}
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
              end"""
new = """              local wpath = ctx.sider_dir:gsub("[/" .. sep .. "]+$", "") .. sep .. "modules" .. sep .. "fl26world.txt"
              local rc = {}
              local wf = io.open(wpath, "r")
              if wf then
                for line in wf:lines() do
                  local kind, rid = line:match("^%s*([%a]+)%s+(%d+)")
                  local cid = line:match("%scid=(%d+)")
                  if cid and (kind == "league" or kind == "ccup") then
                    rc[#rc + 1] = tonumber(rid)
                    rc[#rc + 1] = tonumber(cid)
                  end
                end
                wf:close()
              end
              if #rc > 0 then
                local buf = ffi.new("uint32_t[?]", #rc)
                for i = 1, #rc do buf[i - 1] = rc[i] end
                local m = tonumber(ffi.cast("fl26_swiss_access_t", prc)(buf, #rc))
                log(string.format("fl26swiss: %d reg->cid pair(s) handed to the DLL", m))
              end"""
assert old in s
s = s.replace(old, new, 1)
io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("bloque corregido (wpath propio, sin shadow de pairs)")
