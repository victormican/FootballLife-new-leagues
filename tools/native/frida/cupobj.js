// cupobj -- what Cheat Engine would show for the Cup screen, without Cheat Engine.
//
// The menu object of Kick Off > Cup is whatever object has MenuModeCupSelect's vtable at +0.
// This scans writable memory for that pointer, then dumps:
//   +0x88 rows vector   (begin/end/cap, 0x50-byte rows)
//   +0x90 item list     (begin/end/cap, 12-byte items: cid, clubs, has_group, f6..f8)
// which is exactly the state that decides whether the screen can advance.
//
// Run it while the Cup screen is open; every pass prints one line per object found.

'use strict';

const EXE = 'FL_2026.exe';
const VT = 0x142692c40;          // MenuModeCupSelect
const VT_EDIT = 0x1426ef848;     // MenuEditLgCpMain (for comparison)

const log = (s) => {
  const t = String(s);
  console.log(t);
  send({ kind: 'log', text: t });
};

function main() {
  const exe = Process.enumerateModules().find((m) => m.name.toLowerCase() === EXE);
  if (!exe) { log('FL_2026.exe not loaded'); return; }
  const targets = [VT, VT_EDIT].map((v) => ptr(v));

  const found = [];
  for (const r of Process.enumerateRanges('rw-')) {
    for (const vt of targets) {
      try {
        const hits = Memory.scanSync(r.base, r.size, vt.toString().replace('0x', ''));
        for (const h of hits) found.push({ at: h.address, vt });
      } catch (e) { /* range not scannable */ }
    }
  }
  log('objects found: ' + found.length);
  for (const f of found.slice(0, 8)) {
    const self = f.at;
    const rows = self.add(0x88).readPointer();
    const lb = self.add(0x90).readPointer();
    const le = self.add(0x98).readPointer();
    const lc = self.add(0xa0).readPointer();
    log('OBJ ' + self + ' vt=' + f.vt + ' rows=' + rows + ' list=' + lb + '..' + le +
        ' cap=' + lc);
    try {
      if (!lb.isNull() && le.compare(lb) > 0) {
        const n = le.sub(lb).toInt32() / 12;
        const cids = [];
        for (let i = 0; i < Math.min(n, 24); i++) {
          const p = lb.add(i * 12);
          cids.push(p.readU32() + '(' + p.add(4).readU8() + ',' + p.add(5).readU8() + ')');
        }
        log('  items ' + n + ': ' + cids.join(' '));
      }
    } catch (e) { log('  items error ' + e); }
    try {
      if (!rows.isNull()) {
        const rb = rows.add(0x70).readPointer();
        const re = rows.add(0x78).readPointer();
        const nr = rb.isNull() || re.compare(rb) < 0 ? -1 : re.sub(rb).toInt32() / 0x50;
        log('  rows ' + nr + ' begin=' + rb);
      }
    } catch (e) { log('  rows error ' + e); }
  }
  log('done');
}

main();
