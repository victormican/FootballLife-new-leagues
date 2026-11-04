--[[
fl26cupgrow -- mas de 13 copas en Kick Off > Cup, sin depender del heap.

Medido el 2026-11-03: la lista del menu es un vector de items de 12 bytes {cid, 0xffff, 0} con
capacidad 13. Ocho los pone el juego y fl26swiss añade los del mundo hasta llenarla, descartando el
resto. Su propio ensanche (VirtualAlloc) solo actua cuando el array vive dentro del objeto; si el
vector acaba en el heap lo deja quieto, y eso cambia de un arranque a otro.

Esto lo hace determinista: al arrancar se piden 16 buffers de 768 bytes (64 items) al mismo CRT que
usa el juego y se guardan en un anillo. El stub que envuelve el init del menu (slot de la vtable
0x142692d18) toma el siguiente buffer, copia la lista y repunta begin/end/cap. El destructor del
menu libera ese buffer con su propio heap, y cada apertura gasta uno del anillo.

Nada se escribe si el slot de la vtable esta vacio o los buffers no se consiguen.
Necesita luajit.ext.enabled = 1 (ffi global).
--]]

local m = {}

local VT    = 0x142692d18      -- vtable slot de fl26swiss (handler del menu de copas)
local WANT  = 64               -- items por buffer
local RING  = 16               -- buffers del anillo

local STUB = "535657415441554883ec28488bd95241504151" ..
             "488b8398000000482b83900000004885c00f8493000000488b93a0000000482b93900000" ..
             "004881fa000300000f8378000000" ..
             "49beRINGRING" ..
             "498b86800000004883f8100f835d00000049838680000000014d8b24c64d85e40f84" ..
             "48000000" ..
             "4c8bab90000000488b8b980000004c29e94c89ee4c89e7f3a4488b9398000000482b93" ..
             "900000004c89a390000000498d041448898398000000498d842400030000488983a000" ..
             "0000" ..
             "415941585a4889d948b8PREVPREVffd04883c428415d415c5f5e5bc3"

local function bin(h) return (h:gsub("%x%x", function(b) return string.char(tonumber(b, 16)) end)) end
local function u64(v)
  local t = {}
  for i = 0, 7 do t[#t + 1] = string.char(math.floor(v / 2 ^ (8 * i)) % 256) end
  return table.concat(t)
end

function m.init(ctx)
  if ffi == nil then log("fl26cupgrow: global ffi is nil -- set luajit.ext.enabled = 1"); return end
  ffi.cdef([[ void* VirtualAlloc(void*, unsigned long, unsigned long, unsigned long);
              void* LoadLibraryA(const char*);
              void* GetProcAddress(void*, const char*); ]])
  local prev = tonumber(ffi.cast("uint64_t*", VT)[0])
  if not prev or prev == 0 then log("fl26cupgrow: the vtable slot is empty -- nothing written"); return end
  local h = ffi.C.LoadLibraryA("ucrtbase.dll")
  local pm = h ~= nil and ffi.C.GetProcAddress(h, "malloc") or nil
  if pm == nil then log("fl26cupgrow: no ucrtbase malloc -- nothing written"); return end
  local malloc = ffi.cast("void* (*)(unsigned long)", pm)

  local page = nil
  for _, pref in ipairs({ 0x15e100000, 0x15f100000, 0x161100000, 0x171100000 }) do
    page = ffi.C.VirtualAlloc(ffi.cast("void*", pref), 0x2000, 0x3000, 0x40)
    if page ~= nil then break end
  end
  if page == nil then log("fl26cupgrow: no page"); return end
  local base = tonumber(ffi.cast("uint64_t", page))
  local ring, idx, code = base + 0x100, base + 0x180, base + 0x200

  local got = 0
  for i = 0, RING - 1 do
    local b = malloc(WANT * 12)
    if b == nil then break end
    ffi.cast("uint64_t*", ring + i * 8)[0] = ffi.cast("uint64_t", b)
    got = got + 1
  end
  if got < 2 then log(string.format("fl26cupgrow: only %d buffer(s) -- nothing written", got)); return end
  ffi.cast("uint64_t*", idx)[0] = 0

  local bytes = bin((STUB:gsub("RINGRING", function() return u64(ring):gsub(".", function(c) return string.format("%02x", c:byte()) end) end)
                         :gsub("PREVPREV", u64(prev))))
  memory.write(code, bytes)
  memory.write(VT, u64(code))
  if tonumber(ffi.cast("uint64_t*", VT)[0]) ~= code then
    log("fl26cupgrow: the vtable write did not stick"); return
  end
  log(string.format("fl26cupgrow: %d buffers of %d items, menu init wrapped (%#x -> %#x)",
                    got, WANT, prev, code))
end

return m
