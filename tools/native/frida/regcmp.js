// regcmp -- why is our regulation not in the menu's own list?  Compare the live master
// records of the ten shipped cups with ours on every field the builder reads.
'use strict';

const log = (s) => { const t = String(s); console.log(t); send({ kind: 'log', text: t }); };

function main() {
  const exe = Process.enumerateModules().find((m) => m.name.toLowerCase().includes('fl_2026'));
  if (!exe) { log('FL_2026.exe not loaded'); return; }
  const b = exe.base;
  const owner = new NativeFunction(b.add(0x14b6a60), 'pointer', []);
  const findrec = new NativeFunction(b.add(0x14bc860), 'pointer', ['pointer', 'uint16']);
  const f1 = new NativeFunction(b.add(0x14cf3f0), 'uint32', ['uint32']);
  const f2 = new NativeFunction(b.add(0x1543ea0), 'uint32', ['uint32']);

  const ctx = owner();
  if (ctx.isNull()) { log('no ctx'); return; }
  const block = ctx.add(0x48).readPointer();
  log('block=' + block + ' count=' + block.add(0xd0bcf4).readU32());

  const keys = [1027, 6, 1039, 10, 1058, 1065, 1128, 1068, 46, 1071, 200];
  for (const k of keys) {
    const rec = findrec(block, k);
    if (rec.isNull()) { log('key ' + k + ' -> null'); continue; }
    const st = rec.add(0x84).readU32();
    const f230 = rec.add(0x230).readU32();
    const g30a = rec.readU16 ? rec.add(0x30a).readU16() : 0;
    let extra = '';
    for (let i = 0; i < 15; i++) {
      const w = rec.add(0x2ec + i * 20).readU16();
      if (!w || w === 0xffff) continue;
      extra += ' ' + w;
    }
    let r1 = -1, r2 = -1;
    try { r1 = f1(k); } catch (e) { r1 = -2; }
    try { r2 = f2(k); } catch (e) { r2 = -2; }
    log('key ' + k + ' cid=' + rec.add(0x80).readU32() + ' st84=' + st + ' f230=' + f230 +
        ' g30a=' + (g30a & 0x7f) + ' f1=' + r1 + ' f2=' + r2 + ' list2ec:[' + extra + ' ]' +
        ' name=' + rec.add(0x14).readCString(24));
  }
  log('done');
}

main();
