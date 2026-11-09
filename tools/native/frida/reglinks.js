// reglinks -- compare the phase-link fields of the working cups with ours.
'use strict';
const log = (s) => { const t = String(s); console.log(t); send({ kind: 'log', text: t }); };
function main() {
  const exe = Process.enumerateModules().find((m) => m.name.toLowerCase().includes('fl_2026'));
  const b = exe.base;
  const owner = new NativeFunction(b.add(0x14b6a60), 'pointer', []);
  const findrec = new NativeFunction(b.add(0x14bc860), 'pointer', ['pointer', 'uint16']);
  const ctx = owner();
  if (ctx.isNull()) { log('no ctx'); return; }
  const block = ctx.add(0x48).readPointer();
  log('block=' + block + ' count=' + block.add(0xd0bcf4).readU32());
  for (const reg of [46, 1027, 6, 1071, 200, 36, 10]) {
    const rec = findrec(block, reg);
    if (rec.isNull()) { log('reg ' + reg + ' null'); continue; }
    let s = '';
    for (let off = 0x70; off <= 0x80; off += 2) s += ' ' + rec.add(off).readU16();
    log('reg ' + reg + ' cid=' + rec.add(0x80).readU32() + ' 70..80:' + s +
        ' 30a=' + (rec.add(0x30a).readU16() & 0x7f) +
        ' 76=' + rec.add(0x76).readU16());
  }
  log('done');
}
main();
