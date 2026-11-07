// cmprec -- compare the regulation records of the working clone (46) and ours (200).

'use strict';

const log = (s) => {
  const t = String(s);
  console.log(t);
  send({ kind: 'log', text: t });
};

function main() {
  const exe = Process.enumerateModules().find(
    (m) => m.name.toLowerCase().includes('fl_2026'));
  if (!exe) { log('FL_2026.exe not loaded'); return; }
  const owner = new NativeFunction(exe.base.add(0x14b6a60), 'pointer', []);
  const findrec = new NativeFunction(exe.base.add(0x14bc860), 'pointer', ['pointer', 'uint64']);
  const o = owner();
  if (o.isNull()) { log('owner=0'); return; }
  const block = o.add(0x48).readPointer();

  const recs = {};
  for (const id of [46, 200]) {
    try { recs[id] = findrec(block, id); } catch (e) { recs[id] = ptr(0); }
    log('reg ' + id + ' -> ' + recs[id]);
  }
  // campos interesantes
  const offs = [0x00, 0x02, 0x08, 0x0a, 0x0b, 0x0c, 0x10, 0x14, 0x84, 0x300, 0x304, 0x30c];
  for (const id of [46, 200]) {
    const r = recs[id];
    if (!r || r.isNull()) continue;
    const parts = [];
    for (const off of offs) {
      try { parts.push('+' + off.toString(16) + '=' + r.add(off).readU32().toString(16)); }
      catch (e) { parts.push('+' + off.toString(16) + '=?'); }
    }
    log('reg ' + id + ': ' + parts.join(' '));
  }
  // tabla 0x314: en que slot esta cada una
  const count = block.add(0xd0bcf4).readU32();
  const base = block.add(0xc12e9c);
  for (const id of [46, 200]) {
    let slot = -1;
    for (let i = 0; i < count && i < 1000; i++) {
      if (base.add(i * 0x314).readU16() === id) { slot = i; break; }
    }
    log('table: reg ' + id + ' slot ' + slot + ' (count ' + count + ')');
    if (slot >= 0) {
      const r = base.add(slot * 0x314);
      const parts = [];
      for (const off of [0x00, 0x02, 0x04, 0x08, 0x0c, 0x80, 0x84]) {
        try { parts.push('+' + off.toString(16) + '=' + r.add(off).readU32().toString(16)); } catch (e) { }
      }
      log('  row: ' + parts.join(' '));
    }
  }
  log('done');
}

main();
