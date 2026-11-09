// regs_probe -- every regulation id the game has, and which ones are free.
//
// findrec(block, id) is the game's own lookup (the one cupsel_handler uses).  A null answer means
// the id is not in CompetitionRegulation, so it can be created for a cup.  The record's name is at
// +0x14, the clubs count at +0x30c (7 bits), the format dword at +0x0c.

'use strict';

const MODULE = 'FL_2026.exe';
const FROM = 1;
const TO = 320;

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
  if (o.isNull()) { log('owner=0 (edit data not loaded: enter a mode first)'); return; }
  const blk = o.add(0x48).readPointer();
  log('block=' + blk);

  const free = [];
  for (let id = FROM; id <= TO; id++) {
    let rec;
    try { rec = findrec(blk, id); } catch (e) { log('id ' + id + ' error ' + e); continue; }
    if (rec.isNull()) { free.push(id); continue; }
    let name = '';
    let clubs = -1;
    let fmt = 0;
    try {
      const raw = rec.add(0x14).readByteArray(24);
      const bytes = new Uint8Array(raw);
      for (let i = 0; i < bytes.length; i++) {
        const b = bytes[i];
        if (b < 32 || b >= 127) break;
        name += String.fromCharCode(b);
      }
    } catch (e) { name = '?'; }
    try { clubs = rec.add(0x30c).readU32() & 0x7f; } catch (e) { }
    try { fmt = rec.add(0x0c).readU32(); } catch (e) { }
    log('id ' + id + ' clubs=' + clubs + ' fmt=0x' + fmt.toString(16) + ' name="' + name + '"');
  }
  log('FREE in ' + FROM + '..' + TO + ': ' + free.join(','));
}

main();
