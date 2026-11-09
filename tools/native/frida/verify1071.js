// verify1071 -- is our cup now one of the game's own ten?  Reads the master record 1071
// (cid/state/clubs), asks phkind for cid 131, then follows the session table and the draw.
'use strict';

const log = (s) => { const t = String(s); console.log(t); send({ kind: 'log', text: t }); };

function main() {
  const exe = Process.enumerateModules().find((m) => m.name.toLowerCase().includes('fl_2026'));
  if (!exe) { log('FL_2026.exe not loaded'); return; }
  const b = exe.base;
  const owner = new NativeFunction(b.add(0x14b6a60), 'pointer', []);
  const findrec = new NativeFunction(b.add(0x14bc860), 'pointer', ['pointer', 'uint16']);
  const phkind = new NativeFunction(b.add(0x150af30), 'uint64', ['pointer', 'uint64']);

  const ctx = owner();
  if (ctx.isNull()) { log('no ctx'); return; }
  const block = ctx.add(0x48).readPointer();
  log('block=' + block + ' mode=' + block.add(0x183789c).readU32() +
      ' count=' + block.add(0xd0bcf4).readU32());

  for (const reg of [1071, 200, 46]) {
    const rec = findrec(block, reg);
    if (rec.isNull()) { log('findrec(' + reg + ')=null'); continue; }
    log('findrec(' + reg + ') cid=' + rec.add(0x80).readU32() +
        ' state=' + rec.add(0x84).readU32() +
        ' clubs=' + (rec.add(0x30c).readU8() & 0x7f));
  }
  for (const cid of [131, 37, 36]) {
    const buf = Memory.alloc(4);
    buf.writeU32(cid);
    let s = '';
    for (let k = 1; k <= 4; k++) s += ' k' + k + '=' + phkind(buf, k).toNumber();
    log('phkind ' + cid + s);
  }

  Interceptor.attach(b.add(0x150d2b0), {
    onEnter(args) { this.reg = args[0].readU16() & 0x3ff; },
    onLeave(retval) { if (this.reg === 1071 || this.reg === 200 || retval.toInt32() === 2) log('GATE reg=' + this.reg + ' -> ' + retval.toInt32()); },
  });
  Interceptor.attach(b.add(0x15485c0), {
    onEnter(args) { log('DRAW reg=' + (args[0].toInt32() & 0xffff)); },
  });

  let last = '';
  function tick() {
    try {
      const c = owner();
      if (c.isNull()) return;
      const blk = c.add(0x48).readPointer();
      if (blk.isNull()) return;
      const mode = blk.add(0x183789c).readU32();
      const cnt = blk.add(0xd0bcf4).readU32();
      const rows = [];
      for (let i = 0; i < 0x12c; i++) {
        const r = blk.add(0xc12e9c).add(i * 0x314);
        const key = r.readU16();
        if (key === 0xffff || key === 0) continue;
        const rid = key & 0x3ff;
        const cid = r.add(0x80).readU32();
        if (rid === 1071 || rid === 200 || cid === 131 || cid === 36)
          rows.push(i + ':k=' + key + '/c=' + cid + '/s=' + r.add(0x84).readU32() +
                    '/cl=' + (r.add(0x30c).readU8() & 0x7f));
      }
      const line = 'mode=' + mode + ' count=' + cnt + ' [' + rows.join(' ') + ']';
      if (line !== last) { last = line; log(line); }
    } catch (e) { }
  }
  tick();
  setInterval(tick, 1500);
  log('ready');
}

main();
