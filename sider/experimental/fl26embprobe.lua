--[[
fl26embprobe -- TEMPORAL. Log which emblem/crest file the game asks livecpk for.

The league rows of Kick Off -> Select Team paint a competition emblem. Our eight leagues
(cid 258..265) show shipped cup badges (Europa, Supercup, Libertadores, Champions...) even
though common/render/symbol/emblemLc/emb_0258_*.png exists in the active root, so either the
game asks for another id, or it does not ask livecpk at all. This logs every request whose name
looks like an asset, capped so the log stays readable.
]]

local log = function(s) print("[fl26embprobe] " .. s) end
local m = {}
local lines, cap = 0, 400
local any, anycap = 0, 20

local function interesting(name)
  name = tostring(name or "")
  return name:find("emb") ~= nil or name:find("emblem") ~= nil
      or name:find("symbol") ~= nil or name:find("flag") ~= nil
      or name:find("%.png") ~= nil
end

function m.make_key(ctx, filename)
  if any < anycap then
    any = any + 1
    log("first asks (" .. any .. "): " .. tostring(filename))
  end
  if lines >= cap then return nil end
  if not interesting(filename) then return nil end
  lines = lines + 1
  log("livecpk asked: " .. tostring(filename))
  return nil
end

function m.init(ctx)
  log("probe on (cap " .. cap .. " lines)")
  ctx.register("livecpk_make_key", m.make_key)
end

return m
