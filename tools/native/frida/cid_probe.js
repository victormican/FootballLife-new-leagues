// cid_probe -- what the game's own resolver says about a competition, from outside the menu.
//
// phkind(cid, kind) is the function cupsel_handler uses to filter the list: kind 2 is the group
// phase the Recipe/Regulations screen shows as Draw Size.  owner()+0x48 is the block findrec
// searches for a group id, and +0x14 of the record is its name.
//
// The list below is the cup list after the filter (33,5,8,27,36,34,35,37) plus ours (131).

'use strict';

const MODULE = 'FL_2026.exe';
const CIDS = [33, 5, 8, 27, 36, 34, 35, 37, 131];

const log = (text) => {
  const s = String(text);
  console.log(s);
  send({ kind: 'log', text: s });
};

function main() {
  const exe = Process.enumerateModules().find((m) => m.name.toLowerCase() === MODULE.toLowerCase());
  if (!exe) { log('FL_2026.exe not loaded'); return; }

  const phkind = new NativeFunction(exe.base.add(0x150af30), 'uint64', ['pointer', 'uint64']);
  const owner = new NativeFunction(exe.base.add(0x14b6a60), 'pointer', []);
  const findrec = new NativeFunction(exe.base.add(0x14bc860), 'pointer', ['pointer', 'uint64']);

  const o = owner();
  log('owner=' + o);
  const blk = o.isNull() ? ptr(0) : o.add(0x48).readPointer();
  log('block=' + blk);

  for (const cid of CIDS) {
    const buf = Memory.alloc(4);
    buf.writeU32(cid);
    const kinds = [];
    for (let k = 1; k <= 6; k++) {
      let v = 0;
      try { v = phkind(buf, k).toNumber(); } catch (e) { v = -1; }
      kinds.push('k' + k + '=' + v);
    }
    let g = 0;
    try { g = phkind(buf, 2).toNumber(); } catch (e) { g = -1; }
    let name = '';
    let rec = null;
    if (!blk.isNull() && g !== 0xffff) {
      try {
        rec = findrec(blk, g);
        if (!rec.isNull()) name = rec.add(0x14).readUtf8String(40) || '';
      } catch (e) { name = '<' + e + '>'; }
    }
    log('CID ' + cid + ' ' + kinds.join(' ') + ' rec=' + (rec ? rec.toString() : 'null') +
        ' name="' + name + '"');
  }
  log('done');
}

main();
