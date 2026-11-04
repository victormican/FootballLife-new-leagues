--[[
fl26cupfree -- el menu de copas ya no libera su lista al destruirse.

La cadena del destructor (medida 2026-11-04):

  0x140b1c810   destructor del menu: pone vtables, libera +0xd0 y +0xb8, salta a la base
  0x140c6b1e0   destructor base: rdx=[rcx+0x90]; si no es 0 -> pool_free(&2, rdx) y despues
                +0x90/+0x98/+0xa0 = 0
  0x1403fb5b0   pool_free: desc = tabla[id<<6]; desc->free(p), que desengancha el bloque de un
                arbol rojo-negro leyendo su cabecera en [p-8]

La lista vive DENTRO del objeto (begin = self+0x1c0, cap = self+0x25c, 13 huecos), asi que ese
"free" lee una cabecera que nunca fue un bloque del pool: corrompe el arbol.  Cuando fl26swiss la
ensancha a 43 items le pasa al destructor un buffer de VirtualAlloc, que tampoco tiene cabecera, y
el desmontaje revienta en FL_2026+0x3fd5db (mov [rax+0x18], rcx) o +0x3fd2b2 (mov r14,[rbx-8]).

Parche: los siete bytes de 0x140c6b207 (mov rdx, [rcx+0x90]) pasan a ser xor edx, edx + cinco
nops, de modo que el destructor base toma la rama nula y no libera la lista.  No se toca nada mas:
la lista solo se lee y el objeto se esta yendo.  Coste: el buffer se filtra una vez por
destruccion del menu (156 B, o 516 B cuando fl26swiss lo ensancho).

Nada se escribe si los bytes no son los esperados.
Necesita sider.ini: luajit.ext.enabled = 1 (ffi y memory globales).
--]]

local m = {}

local AT, WANT, NEW = 0x140c6b207, "488b9190000000", "31d29090909090"

local function hex(s)
  return (s:gsub(".", function(c) return string.format("%02x", c:byte()) end))
end
local function bin(h)
  return (h:gsub("%x%x", function(b) return string.char(tonumber(b, 16)) end))
end

function m.init(ctx)
  if memory == nil then log("fl26cupfree: no memory library"); return end
  local got = memory.read(AT, #WANT / 2)
  if got == nil or hex(got) ~= WANT then
    log("fl26cupfree: 0x140c6b207 is not the expected code -- nothing written")
    return
  end
  memory.write(AT, bin(NEW))
  local after = memory.read(AT, #NEW / 2)
  if after == nil or hex(after) ~= NEW then
    log("fl26cupfree: the patch did not stick")
    return
  end
  log("fl26cupfree: the cup list is no longer freed by the menu destructor (0x140c6b207)")
end

return m
