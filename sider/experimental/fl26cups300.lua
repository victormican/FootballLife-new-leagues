--[[
fl26cups300 -- the Cup menu's competition resolver only scans 300 regulations.

Measured 2026-11-04 with 488 regulations in the world: the row of every cup of ours showed
the name of the first competition ("FIFA Club World Cup", cid 1) and picking one closed the
game with no draw size.  The resolver 0x14150af30 (phkind, the one that turns a competition
id into its live regulation) walks the live regulation array (records of 0x314 at
block+0xc12e9c) with a hard bound of 300:

    0x14150afb0   81 fb 2c 01 00 00    cmp ebx, 0x12c
    0x14150b00e   81 f9 2c 01 00 00    cmp ecx, 0x12c

Everything stored past index 299 is invisible to it, so a cup there gets no record: no name,
no group size.  fl26regs1200.lua raises the same constant in three other places and the array
is already 1200 records (`fl26caps`), so these two are raised to 1200 the same way.

All-or-nothing: the bytes are read back and compared before anything is written.
Requires sider.ini: luajit.ext.enabled = 1 (the global `memory`).
--]]

local m = {}

local PATCHES = {
  { 0x14150afb0, "81fb2c010000", "81fbb0040000", "the resolver's first scan bound" },
  { 0x14150b00e, "81f92c010000", "81f9b0040000", "the resolver's second scan bound" },
}

local function hex(s)
  return (s:gsub(".", function(c) return string.format("%02x", c:byte()) end))
end
local function bin(h)
  return (h:gsub("%x%x", function(b) return string.char(tonumber(b, 16)) end))
end

function m.init(ctx)
  if memory == nil then log("fl26cups300: sider's memory is nil -- set luajit.ext.enabled = 1"); return end
  for _, p in ipairs(PATCHES) do
    local got = memory.read(p[1], #p[2] / 2)
    if got == nil or hex(got) ~= p[2] then
      log(string.format("fl26cups300: bytes at %#x are %s, expected %s -- nothing written",
                        p[1], tostring(got and hex(got)), p[2]))
      return
    end
  end
  for _, p in ipairs(PATCHES) do memory.write(p[1], bin(p[3])) end
  local n = 0
  for _, p in ipairs(PATCHES) do
    if hex(memory.read(p[1], #p[3] / 2)) == p[3] then n = n + 1 end
  end
  log(string.format("fl26cups300: %d of %d scan bound(s) raised 300 -> 1200 (cups past index 299 resolve)",
                    n, #PATCHES))
end

return m
