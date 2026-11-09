// slotlinks -- read +0x76/+0x30a of our records by scanning the master table (no findrec).
'use strict';
const log = (s) => { const t = String(s); console.log(t); send({ kind: 'log', text: t }); };
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
    if (![46, 1027, 6, 200, 1071, 36].includes(key)) continue;
    let s = '';
    for (let off = 0x70; off <= 0x80; off += 2) s += ' ' + r.add(off).readU16();
    log('slot ' + i + ' key=' + key + ' cid=' + r.add(0x80).readU32() +
        ' 70..80:' + s + ' 76=' + r.add(0x76).readU16() +
        ' 30a=' + (r.add(0x30a).readU16() & 0x7f));
  }
  log('done');
}
main();
