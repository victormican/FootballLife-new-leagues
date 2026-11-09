// regscan -- is our regulation actually in the world's phase table?
//
// The gate that starts a draw walks block+0xc12e9c (0x314-byte records) for a record
// whose key is the regulation id and reads its state at +0x84.  This asks the game's
// own findrec() for our regulation and for the clone's, and lists the slots that carry
// a key we care about.  Nothing is written.

'use strict';

const log = (s) => { const t = String(s); console.log(t); send({ kind: 'log', text: t }); };

function main() {
  const exe = Process.enumerateModules().find((m) => m.name.toLowerCase().includes('fl_2026'));
  if (!exe) { log('FL_2026.exe not loaded'); return; }
  const b = exe.base;

  const owner = new NativeFunction(b.add(0x14b6a60), 'pointer', []);
  const findrec = new NativeFunction(b.add(0x14bc860), 'pointer', ['pointer', 'uint16']);
  const phkind = new NativeFunction(b.add(0x150af30), 'uint64', ['pointer', 'uint64']);

  let ctx;
  try { ctx = owner(); } catch (e) { log('owner threw ' + e); return; }
  log('owner ctx=' + ctx);
  if (ctx.isNull()) return;
  const block = ctx.add(0x48).readPointer();
  log('block=' + block);
  if (block.isNull()) return;

  const count = block.add(0xd0bcf4).readU32();
  const base = block.add(0xc12e9c);
  log('count=' + count + ' base=' + base);

  const want = [200, 46, 36, 131, 11, 130];
  log('--- first slots ---');
  for (let i = 0; i < Math.min(count, 8); i++) {
    const r = base.add(i * 0x314);
    const key = r.readU16();
    log('slot ' + i + ' key=' + key + ' rid=' + (key & 0x3ff) + ' grp=' + (key >> 10) +
        ' cid=' + r.add(0x80).readU32() + ' state=' + r.add(0x84).readU32() +
        ' clubs=' + (r.add(0x30c).readU8() & 0x7f));
  }
  log('--- wanted slots ---');
  for (let i = 0; i < Math.min(count + 4, 400); i++) {
    const r = base.add(i * 0x314);
    const key = r.readU16();
    const rid = key & 0x3ff;
    if (!want.includes(rid)) continue;
    const cid = r.add(0x80).readU32();
    const state = r.add(0x84).readU32();
    const clubs = r.add(0x30c).readU8() & 0x7f;
    log('slot ' + i + ' key=' + key + ' rid=' + rid + ' grp=' + (key >> 10) +
        ' cid=' + cid + ' state=' + state + ' clubs=' + clubs +
        ' name=' + r.add(0x14).readCString(24));
  }

  for (const cid of [131, 36, 130, 46]) {
    const buf = Memory.alloc(4);
    buf.writeU32(cid);
    let ks = '';
    for (let k = 1; k <= 6; k++) {
      try { ks += ' k' + k + '=' + phkind(buf, k).toNumber(); } catch (e) { ks += ' k' + k + '=ERR'; }
    }
    log('phkind cid=' + cid + ks);
  }

  for (const reg of [200, 46, 36, 11]) {
    const rec = findrec(block, reg);
    if (rec.isNull()) { log('findrec(' + reg + ')=null'); continue; }
    log('findrec(' + reg + ')=' + rec + ' key=' + rec.readU16() +
        ' cid=' + rec.add(0x80).readU32() + ' state=' + rec.add(0x84).readU32() +
        ' clubs=' + (rec.add(0x30c).readU8() & 0x7f) +
        ' name=' + rec.add(0x14).readCString(24));
  }
  log('done');
}

main();
