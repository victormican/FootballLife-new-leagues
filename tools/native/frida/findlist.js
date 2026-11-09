// findlist -- which master record carries the hardcoded list of the ten cup regulations?
// The builder compares each regulation key against up to 15 u16 entries at rec+0x2ec
// (20-byte stride).  Scan the live table for the record that lists 46 / 1071.
'use strict';

const log = (s) => { const t = String(s); console.log(t); send({ kind: 'log', text: t }); };

function main() {
  const exe = Process.enumerateModules().find((m) => m.name.toLowerCase().includes('fl_2026'));
  if (!exe) { log('FL_2026.exe not loaded'); return; }
  const b = exe.base;
  const owner = new NativeFunction(b.add(0x14b6a60), 'pointer', []);
  const ctx = owner();
  if (ctx.isNull()) { log('no ctx'); return; }
  const block = ctx.add(0x48).readPointer();
  const count = block.add(0xd0bcf4).readU32();
  log('block=' + block + ' count=' + count);

  for (let i = 0; i < Math.min(count, 400); i++) {
    const rec = block.add(0xc12e9c).add(i * 0x314);
    const key = rec.readU16();
    if (key === 0xffff) continue;
    let list = [];
    let hit = false;
    for (let j = 0; j < 15; j++) {
      const w = rec.add(0x2ec + j * 20).readU16();
      list.push(w);
      if (w === 46 || w === 1071 || w === 1027) hit = true;
    }
    if (hit) {
      log('record slot ' + i + ' key=' + key + ' cid=' + rec.add(0x80).readU32() +
          ' list=[' + list.join(',') + ']');
    }
  }
  log('done');
}

main();
