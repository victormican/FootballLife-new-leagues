// findlist -- locate the competition list by its content, not by a vtable.
//
// Every list item is 12 bytes: cid (u32), 0x0000ffff (u32), 0 (u32).  cid 33 (FIFA Club World Cup)
// is in the shipped list, so its bytes are a fingerprint.  From a hit we dump the items and look
// for a pointer to that address, which is the list begin stored in whichever object owns it
// (begin at +0x90 for the select modes, but this finds it even when the class is another one).

'use strict';

const log = (s) => {
  const t = String(s);
  console.log(t);
  send({ kind: 'log', text: t });
};

function items(addr, max) {
  const out = [];
  for (let i = 0; i < max; i++) {
    try {
      const p = addr.add(i * 12);
      const cid = p.readU32();
      const tail = p.add(4).readU32();
      if (tail !== 0xffff) break;
      out.push(cid + '(c' + p.add(4).readU8() + ',g' + p.add(5).readU8() + ')');
    } catch (e) { break; }
  }
  return out;
}

function main() {
  const ranges = Process.enumerateRanges('rw-');
  const pat = '21000000ffff0000';            // cid 33 + 0x0000ffff
  const hits = [];
  for (const r of ranges) {
    try {
      for (const h of Memory.scanSync(r.base, r.size, pat)) hits.push(h.address);
    } catch (e) { /* skip */ }
  }
  log('fingerprint hits: ' + hits.length);

  for (const h of hits.slice(0, 12)) {
    log('LIST? ' + h + ' -> ' + items(h, 40).join(' '));
    // who points at this address (the object's begin field)?
    const p8 = h.toString().replace('0x', '').padStart(16, '0');
    for (const r of ranges) {
      try {
        const found = Memory.scanSync(r.base, r.size, p8);
        for (const f of found) {
          const q = f.address;
          log('  referenced at ' + q + ' -> object ' + q.sub(0x90) +
              ' (if begin is +0x90), or ' + q.sub(0x70) + ' (if rows begin)');
        }
      } catch (e) { /* skip */ }
    }
  }
  log('done');
}

main();
