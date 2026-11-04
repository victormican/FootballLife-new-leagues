--[[
fl26strprobe -- TEMPORAL. Which text files the game asks livecpk for.

The competition names the Cup menu paints are not in the world tables: they come from
`cpk_dat/<lang>/string/all.str` (WESYS + zlib; extracted from data_s2526a.cpk). The exe builds
that path at 0x141497c90-cdd ("cpk_dat/" + "common/string/" | "<lang>/string/" + the file name).
Before rewriting that file we need to know which one this installation actually opens and whether
Sider's livecpk answers it, so this logs every request whose name contains "string" or ".str".
]]

local m = {}
local lines, cap = 0, 200

local function L(s) log("[fl26strprobe] " .. s) end

function m.make_key(ctx, filename)
  if lines >= cap then return nil end
  local name = tostring(filename or "")
  if name:find("string") or name:find("%.str") or name:find("strdata") then
    lines = lines + 1
    L("asked: " .. name)
  end
  return nil
end

function m.init(ctx)
  L("probe on")
  ctx.register("livecpk_make_key", m.make_key)
end

return m
