// findmenu -- locate the live MenuModeCupSelect object and dump its item list.
//
// The object starts with its vtable pointer 0x142692c40.  Scan private readable/writable
// ranges for that qword, keep the hits whose +0x90/+0x98/+0xa0 look like a 12-byte vector,
// and print every item plus the descriptor vector at +0xd0.

'use strict';

const log = (s) => { const t = String(s); console.log(t); send({ kind: 'log', text: t }); };

function main() {
  const exe = Process.enumerateModules().find((m) => m.name.toLowerCase().includes('fl_2026'));
  if (!exe) { log('FL_2026.exe not loaded'); return; }
  const vt = exe.base.add(0x2692c40);
  const pat = '40 2c 69 42 01 00 00 00';
  log('vtable=' + vt);

  let hits = 0;
  const ranges = Process.enumerateRanges('rw-');
  for (const r of ranges) {
    if (r.size > 64 * 1024 * 1024) continue;
    let found;
    try { found = Memory.scanSync(r.base, r.size, pat); } catch (e) { continue; }
    for (const f of found) {
      const o = f.address;
      try {
        const b = o.add(0x90).readPointer();
        const e = o.add(0x98).readPointer();
        const c = o.add(0xa0).readPointer();
        if (b.isNull() || e.compare(b) < 0) continue;
        const n = e.sub(b).toInt32() / 12;
        if (n < 0 || n > 64) continue;
        if (!c.isNull() && c.compare(b) < 0) continue;
        hits++;
        log('object ' + o + ' items=' + n + ' begin=' + b + ' end=' + e + ' cap=' + c);
        for (let i = 0; i < n; i++) {
          const p = b.add(i * 12);
          const cid = p.readU32();
          const bytes = new Uint8Array(p.readByteArray(12));
          log('  item ' + i + ' cid=' + cid + ' bytes=' + Array.from(bytes).map((x) => x.toString(16).padStart(2, '0')).join(''));
        }
        const d0 = o.add(0xd0);
        try {
          const d0b = d0.readPointer(), d0e = d0.add(8).readPointer(), d0c = d0.add(0x10).readPointer();
          log('  d0 begin=' + d0b + ' end=' + d0e + ' cap=' + d0c);
          if (!d0b.isNull() && d0e.compare(d0b) >= 0) {
            const dn = d0e.sub(d0b).toInt32();
            log('  d0 bytes=' + dn);
          }
        } catch (e2) { }
      } catch (e) { }
    }
  }
  log('objects found: ' + hits + ' ranges=' + ranges.length);
}

main();
