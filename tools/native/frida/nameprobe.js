// nameprobe -- read the live regulation names as UTF-16 (record +0x14).
'use strict';
const log = (s) => { const t = String(s); console.log(t); send({ kind: 'log', text: t }); };
function u16z(p, max) {
  let s = '';
  for (let i = 0; i < max; i++) {
    const c = p.add(i * 2).readU16();
    if (!c) break;
    s += String.fromCharCode(c);
  }
  return s;
}
function main() {
  const exe = Process.enumerateModules().find((m) => m.name.toLowerCase().includes('fl_2026'));
  const b = exe.base;
  const owner = new NativeFunction(b.add(0x14b6a60), 'pointer', []);
  const ctx = owner();
  if (ctx.isNull()) { log('no ctx'); return; }
  const block = ctx.add(0x48).readPointer();
  const count = block.add(0xd0bcf4).readU32();
  log('block=' + block + ' count=' + count);
  for (let i = 0; i < Math.min(count, 400); i++) {
    const r = block.add(0xc12e9c).add(i * 0x314);
    const key = r.readU16();
    if (![46, 1071, 200].includes(key)) continue;
    log('slot ' + i + ' key=' + key + ' cid=' + r.add(0x80).readU32() +
        ' name16="' + u16z(r.add(0x14), 40) + '"' +
        ' name8="' + r.add(0x14).readCString(40) + '"');
  }
  log('done');
}
main();
