--[[
fl26playercap -- the 30,000-entry player index stops filling instead of writing past its table.

Why: a world with more than ~65,000 players crashed while the game built one of its player
indexes.  Measured 2026-10-24 with Frida (76): the caller at 0x14F4966 inserts player indices
one by one into a structure whose storage is 30,000 dwords and whose count lives at +0x1d510,
and the insert 0x1414d6940 starts by reading that count and comparing it with 0x7530:

    0x1414d6945  mov  r13d, [rcx + 0x1d510]     ; how many entries it holds
    0x1414d6954  cmp  r13d, 0x7530              ; 30000, the table's size
    0x1414d695b  je   0x1414d6b06               ; full -> pop/pop/pop/ret, it does nothing

`je` only catches exactly 30,000.  A world with more players reached 30,001 and the insert
wrote past the table, over the bucket starts/counts that follow it, and the next call read a
garbage count (one dump: r13 = 0x13FF60037) and walked to -1.  This is the "menu-mode object
with a 30,001-dword table ... still not grown" that research-findings.md lists as residual
risk.

What this does: one byte at 0x1414d695c, 0x84 (je) -> 0x83 (jae), so the function returns as
soon as the table is full, at 30,000 or past it.  The players beyond the table's capacity are
simply not in that index -- the same trade the module already makes for the appearance table
(players past 30,023 keep the default look).  Nothing is moved and no count is lowered.

Install:
  1. copy this file to <game>\SiderAddons\modules\
  2. sider.ini: lua.module = "fl26playercap.lua" (next to fl26comptab.lua)
  3. start the game; sider.log says "fl26playercap: ... returns when it reaches 30000"

Requires sider.ini: luajit.ext.enabled = 1 (the global ffi and `memory`), like fl26comptab.
--]]

local m = {}

local CMP, CMP_BYTES = 0x1414d6954, "4181fd30750000"   -- cmp r13d, 0x7530
local JE,  JE_BYTES  = 0x1414d695b, "0f84a50100"       -- je 0x1414d6b06
-- the squad lookup: cmp edx, 0x28 / jge -> null.  edx indexes the block's player array
-- (stride 0x17c), whose cap is 123825, so 40 is not the array's size.

local function hex(s)
  return (s:gsub(".", function(c) return string.format("%02x", c:byte()) end))
end

function m.init(ctx)
  local a = memory.read(CMP, #CMP_BYTES / 2)
  local b = memory.read(JE, #JE_BYTES / 2)
  if a == nil or b == nil then
    log("fl26playercap: cannot read the insert's prologue -- nothing written")
    return
  end
  if hex(a) ~= CMP_BYTES or hex(b) ~= JE_BYTES then
    log(string.format("fl26playercap: bytes at %#x are %s / %s, expected %s / %s -- nothing written",
                      JE, hex(a), hex(b), CMP_BYTES, JE_BYTES))
    return
  end
  memory.write(JE + 1, string.char(0x83))
  log("fl26playercap: the player index returns when it reaches 30000 instead of writing past its table")
end

return m
