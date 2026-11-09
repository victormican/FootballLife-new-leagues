// findlist2 -- just the list: scan for an item fingerprint and print the 12-byte items.
// Fast: no pointer scan.

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
  const pats = ['21000000ffff0000', '05000000ffff0000'];
  let found = 0;
  for (const r of Process.enumerateRanges('rw-')) {
    for (const pat of pats) {
      try {
        for (const h of Memory.scanSync(r.base, r.size, pat)) {
          found++;
          if (found <= 6) log('LIST ' + h.address + ' -> ' + items(h.address, 40).join(' '));
        }
      } catch (e) { }
    }
  }
  log('lists found: ' + found);
}

main();
