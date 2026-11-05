--[[
fl26cupgrow -- mas de 13 copas en Kick Off > Cup.

Autopsia (2026-11-03): cupsel_handler (fl26swiss) quita las copas con grupos de mas de 32 clubes,
AÑADE las del mundo y solo al final llama al init del menu. Por eso el init llega tarde: cuando
corre, las que no cupieron ya se descartaron.

Se envuelve el slot de la vtable (0x142692d18), donde fl26swiss dejo su handler. El stub mueve la
lista (los 8 items que ya puso el juego) a un buffer de 64 items del anillo y SALTA al handler
(tail call: sin marco propio, sin call, rsp intacta). El handler encuentra sitio y añade las 19.

El destructor (0x140b1c810) anula begin/end/cap antes de que la clase base libere la lista: free(NULL)
no hace nada y no se libera un buffer ajeno.

Los buffers son 16 x 768 B de VirtualAlloc. Nada se escribe si los bytes no son los esperados.
Necesita luajit.ext.enabled = 1 (ffi global).
--]]

local m = {}

local VT = 0x142692d18
local DTOR, DTOR_NEXT = 0x140b1c810, 0x140b1c824
local DTOR_OLD = "40574883ec3048c7442420feffffff48895c2448488bf9"
local WANT, RING = 256, 16

-- 181 bytes: crece la lista y salta al handler previo.
--   begin se guarda en rdx (push/pop) porque rax pasa a ser el indice del anillo;
--   con el begin en rax el rep movsb copiaba desde la direccion 0 (crash 0x16110026f);
--   el SIB de [r10+rax*8] pedia REX.X y leia [r10+r8*8].
--   Huecos: anillo en 53, prev en 171.
local VSTUB =               "5152565741574989cf48b8402c694201000000483b010f85c5000000498b87900000004885c00f84b5000000" ..
              "498b8f980000004885c90f84a50000004d8b9fa00000004d85db0f8495000000483bc10f838c0000004c3bd9" ..
              "0f86830000004889c24929c34981fb000400000f837000000049ba0001106101000000498b82800000004883" ..
              "f8100f835500000049838280000000014d8b1cc24d85db0f84400000004889d6498b8f980000004829d14c89" ..
              "dff3a4498b8798000000492b87900000004d899f90000000498d0c0349898f98000000498d8b000c00004989" ..
              "8fa0000000415f5f5e5a5948b8f05155d6fe7f0000ffe0"

-- 60 bytes: prologo del destructor y anulacion de la lista
local DSTUB = "40574883ec3048c7442420feffffff48895c2448488bf9" ..
              "48c7819000000000000000" .. "48c7819800000000000000" ..
              "48c781a000000000000000" .. "e900000000"

local function bin(h) return (h:gsub("%x%x", function(b) return string.char(tonumber(b, 16)) end)) end
local function u32(v)
  v = v % 0x100000000
  return string.char(v % 256, math.floor(v / 256) % 256,
                     math.floor(v / 65536) % 256, math.floor(v / 16777216) % 256)
end
local function u64(v)
  local t = {}
  for i = 0, 7 do t[#t + 1] = string.char(math.floor(v / 2 ^ (8 * i)) % 256) end
  return table.concat(t)
end
local function hex(s) return (s:gsub(".", function(c) return string.format("%02x", c:byte()) end)) end

function m.init(ctx)
  if ffi == nil then log("fl26cupgrow: global ffi is nil -- set luajit.ext.enabled = 1"); return end
  ffi.cdef([[ void* VirtualAlloc(void*, unsigned long, unsigned long, unsigned long); ]])
  local prev = tonumber(ffi.cast("uint64_t*", VT)[0])
  if not prev or prev == 0 then log("fl26cupgrow: the vtable slot is empty -- nothing written"); return end
  local b = memory.read(DTOR, #DTOR_OLD / 2)
  if b == nil or hex(b) ~= DTOR_OLD then
    log("fl26cupgrow: the menu destructor is not the expected code -- nothing written"); return
  end

  local page = nil
  for _, pref in ipairs({ 0x15e100000, 0x15f100000, 0x161100000, 0x171100000 }) do
    page = ffi.C.VirtualAlloc(ffi.cast("void*", pref), 0x2000, 0x3000, 0x40)
    if page ~= nil then break end
  end
  if page == nil then log("fl26cupgrow: no page"); return end
  local base = tonumber(ffi.cast("uint64_t", page))
  local ring, idx, vstub, dstub = base + 0x100, base + 0x180, base + 0x200, base + 0x400

  local n = 0
  for i = 0, RING - 1 do
    local bufp = ffi.C.VirtualAlloc(nil, WANT * 12, 0x3000, 0x04)
    if bufp == nil then break end
    ffi.cast("uint64_t*", ring + i * 8)[0] = ffi.cast("uint64_t", bufp)
    n = n + 1
  end
  if n < 2 then log(string.format("fl26cupgrow: only %d buffer(s)", n)); return end
  ffi.cast("uint64_t*", idx)[0] = 0

  local s = bin(VSTUB)
  -- los huecos se localizan por su contenido: el stub cambia de tamano al tocarlo y los
  -- offsets fijos dejaban de caer donde tocaba (crash 0x161100238, 2026-11-04)
  local ring_ph, prev_ph = u64(0x161100100), u64(0x7ffed65551f0)
  local r1 = s:find(ring_ph, 1, true)
  local r2 = s:find(prev_ph, 1, true)
  if not r1 or not r2 then log("fl26cupgrow: no encuentro los huecos del stub"); return end
  s = s:sub(1, r1 - 1) .. u64(ring) .. s:sub(r1 + 8)
  s = s:sub(1, r2 - 1) .. u64(prev) .. s:sub(r2 + 8)
  memory.write(vstub, s)
  memory.write(VT, u64(vstub))

  local d = bin(DSTUB)
  d = d:sub(1, 56) .. u32(DTOR_NEXT - (dstub + 60)) .. d:sub(61)
  memory.write(dstub, d)
  memory.write(DTOR, "\233" .. u32(dstub - (DTOR + 5)))

  if tonumber(ffi.cast("uint64_t*", VT)[0]) ~= vstub or memory.read(DTOR, 1):byte(1) ~= 0xE9 then
    log("fl26cupgrow: a patch did not stick"); return
  end
  log("fl26cupgrow: " .. n .. " buffers of " .. WANT .. " items; vtable wrapped (0x"
      .. string.format("%x", prev) .. " -> 0x" .. string.format("%x", vstub)
      .. "), destructor neutralised")
end

return m
