// regfix -- give our regulation a record in the 0x314 table and state 2, which is what the draw
// gate (0x14150d2b0) needs.  Read-only unless WRITE is true.
//
// The table: base = block + 0xc12e9c, count = *(u32*)(block + 0xd0bcf4), stride 0x314, id at +0,
// competition id at +0x80.  The gate walks it and, on a hit, returns the regulation record's
// +0x84; the draw only runs when that is 2.

'use strict';

const WRITE = false;          // true: append the record and set state 2
const REG = 200;              // our regulation
const CID = 50;               // its competition

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
  if (o.isNull()) { log('owner=0 (edit data not loaded)'); return; }
  const block = o.add(0x48).readPointer();
  const count = block.add(0xd0bcf4).readU32();
  const base = block.add(0xc12e9c);
  log('block=' + block + ' count=' + count + ' base=' + base);

  let found = -1;
  for (let i = 0; i < count && i < 2000; i++) {
    const id = base.add(i * 0x314).readU16();
    if (id === REG) { found = i; break; }
  }
  log('reg ' + REG + ' in table: ' + (found >= 0 ? ('slot ' + found) : 'NO'));

  let rec = ptr(0);
  try { rec = findrec(block, REG); } catch (e) { log('findrec error ' + e); }
  if (!rec.isNull()) {
    log('regulation record=' + rec + ' +84=' + rec.add(0x84).readU32());
  } else {
    log('regulation record: null');
  }

  if (!WRITE) { log('read-only (WRITE=false)'); return; }
  if (found >= 0) { log('already has a slot, nothing appended'); }
  else {
    const slot = base.add(count * 0x314);
    // only touch it if it looks empty and readable
    let ok = true;
    try {
      for (let k = 0; k < 0x314; k += 8) {
        if (slot.add(k).readU64().toString() !== '0x0') { ok = false; break; }
      }
    } catch (e) { ok = false; }
    if (!ok) { log('next slot is not empty/readable, not appending'); return; }
    slot.writeU16(REG);
    slot.add(0x80).writeU32(CID);
    block.add(0xd0bcf4).writeU32(count + 1);
    log('appended reg ' + REG + ' at slot ' + count + ' (count -> ' + (count + 1) + ')');
  }
  if (!rec.isNull()) {
    rec.add(0x84).writeU32(2);
    log('regulation +84 -> ' + rec.add(0x84).readU32());
  }
  log('done');
}

main();
