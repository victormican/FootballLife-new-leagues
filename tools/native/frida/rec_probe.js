// rec_probe -- what a regulation record holds, from outside the menu.
//
// cupsel_handler filters the cup list by rec[0x30c] & 0x7f (the clubs of the group phase), so the
// record of a regulation is where a cup's teams live.  This dumps the tail of the record for a
// shipped cup (36 -> knockout 46, 33 -> 42, 37 -> 48) and for ours (131 -> 317) so the difference
// shows: a cup with no field to draw cannot start.

'use strict';

const MODULE = 'FL_2026.exe';
const IDS = [46, 42, 48, 317, 317 + 1, 41, 47];

const log = (text) => {
  const s = String(text);
  console.log(s);
  send({ kind: 'log', text: s });
};

function main() {
  const exe = Process.enumerateModules().find((m) => m.name.toLowerCase() === MODULE.toLowerCase());
  if (!exe) { log('FL_2026.exe not loaded'); return; }

  const owner = new NativeFunction(exe.base.add(0x14b6a60), 'pointer', []);
  const findrec = new NativeFunction(exe.base.add(0x14bc860), 'pointer', ['pointer', 'uint64']);

  const o = owner();
  const blk = o.isNull() ? ptr(0) : o.add(0x48).readPointer();
  log('owner=' + o + ' block=' + blk);

  for (const id of IDS) {
    let rec = ptr(0);
    try { rec = findrec(blk, id); } catch (e) { log('rec ' + id + ' findrec error ' + e); continue; }
    if (rec.isNull()) { log('REC ' + id + ' = null'); continue; }
    let count = -1;
    try { count = rec.add(0x30c).readU32(); } catch (e) { count = -2; }
    log('REC ' + id + ' = ' + rec + '  +30c=' + count + ' (clubs ' + (count & 0x7f) + ')');
    try {
      const raw = rec.add(0x2e0).readByteArray(0x60);
      const bytes = new Uint8Array(raw);
      let s = '';
      for (let i = 0; i < bytes.length; i++) {
        const b = bytes[i];
        s += (b >= 32 && b < 127) ? String.fromCharCode(b) : '.';
      }
      log('  ascii ' + s);
    } catch (e) { log('  ascii <' + e + '>'); }
    for (let off = 0x2c0; off <= 0x330; off += 0x10) {
      try {
        const q = rec.add(off);
        log('  +' + off.toString(16) + ' ' + [0, 8].map((k) => q.add(k).readPointer().toString()).join(' '));
      } catch (e) { break; }
    }
    // any qword in the tail that points to a readable block: show 8 dwords of it
    for (let off = 0x2c0; off <= 0x320; off += 8) {
      let p;
      try { p = rec.add(off).readPointer(); } catch (e) { continue; }
      if (p.compare(ptr('0x10000')) < 0) continue;
      try {
        const d = p.readByteArray(32);
        const u = new Uint32Array(d);
        log('    [' + off.toString(16) + '] -> ' + Array.from(u).map((x) => x.toString(16)).join(' '));
      } catch (e) { /* not a pointer we can read */ }
    }
  }
  log('done');
}

main();
