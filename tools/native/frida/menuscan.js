// menuscan -- find whichever select-mode object is on screen and dump its list/rows.
//
// Kick Off > Cup may be MenuModeCupSelect, MenuModeLeagueSelect (the competition list) or a
// CompeSelect; all of them keep the list at +0x90 and the rows at +0x88, so one scan covers them.

'use strict';

const VTS = {
  0x142692c40: 'CupSelect',
  0x1426745e8: 'LeagueSelect',
  0x142674860: 'LeagueSelectStart',
  0x142677860: 'LeagueSelectCategory',
  0x14268cd40: 'CompeSelect',
  0x142716088: 'CompeSelectBase',
  0x1426ef848: 'EditLgCpMain',
};

const log = (s) => {
  const t = String(s);
  console.log(t);
  send({ kind: 'log', text: t });
};

function dumpOne(self, name) {
  const lb = self.add(0x90).readPointer();
  const le = self.add(0x98).readPointer();
  const rowsObj = self.add(0x88).readPointer();
  log('OBJ ' + name + ' ' + self + ' list=' + lb + '..' + le);
  try {
    if (!lb.isNull() && le.compare(lb) > 0) {
      const n = le.sub(lb).toInt32() / 12;
      const items = [];
      for (let i = 0; i < Math.min(n, 32); i++) {
        const p = lb.add(i * 12);
        items.push(p.readU32() + '(c' + p.add(4).readU8() + ',g' + p.add(5).readU8() + ')');
      }
      log('  items ' + n + ': ' + items.join(' '));
    }
  } catch (e) { log('  items error ' + e); }
  try {
    const rb = rowsObj.add(0x70).readPointer();
    const re = rowsObj.add(0x78).readPointer();
    const nr = rb.isNull() || re.compare(rb) < 0 ? -1 : re.sub(rb).toInt32() / 0x50;
    const vb = rowsObj.add(0x3d0).readPointer();
    const ve = rowsObj.add(0x3d8).readPointer();
    log('  rows ' + nr + '  mount+3d0=' + vb + ' +3d8=' + ve +
        (vb.equals(ve) ? '  <-- VACIO' : ''));
  } catch (e) { log('  rows error ' + e); }
}

function scan() {
  let found = 0;
  for (const r of Process.enumerateRanges('rw-')) {
    for (const vt of Object.keys(VTS)) {
      try {
        const hits = Memory.scanSync(r.base, r.size, ptr(vt).toString().replace('0x', ''));
        for (const h of hits) {
          found++;
          if (found <= 12) dumpOne(h.address, VTS[vt]);
        }
      } catch (e) { /* range not scannable */ }
    }
  }
  log('objects: ' + found);
  return found > 0;
}

if (!scan()) log('no select-mode object found');
