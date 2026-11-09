// scanall -- dump every slot the session phase table has right now.
'use strict';

const log = (s) => { const t = String(s); console.log(t); send({ kind: 'log', text: t }); };

function main() {
  const exe = Process.enumerateModules().find((m) => m.name.toLowerCase().includes('fl_2026'));
  if (!exe) { log('FL_2026.exe not loaded'); return; }
  const b = exe.base;
  const owner = new NativeFunction(b.add(0x14b6a60), 'pointer', []);
  const ctx = owner();
  log('ctx=' + ctx);
  if (ctx.isNull()) return;
  const block = ctx.add(0x48).readPointer();
  log('block=' + block);
  if (block.isNull()) return;
  const mode = block.add(0x183789c).readU32();
  const count = block.add(0xd0bcf4).readU32();
  log('mode=' + mode + ' count=' + count);
  const base = block.add(0xc12e9c);
  for (let i = 0; i < 0x12c; i++) {
    const r = base.add(i * 0x314);
    const key = r.readU16();
    const cid = r.add(0x80).readU32();
    if ((key === 0 && cid === 0) || key === 0xffff) continue;
    log('slot ' + i + ' key=' + key + ' rid=' + (key & 0x3ff) + ' grp=' + (key >> 10) +
        ' cid=' + cid + ' state=' + r.add(0x84).readU32() +
        ' clubs=' + (r.add(0x30c).readU8() & 0x7f) +
        ' b0c=' + r.add(0x0c).readU32());
  }
  log('done');
}

main();
