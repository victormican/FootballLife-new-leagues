// cupprobe -- what the game does when our cup is opened.
//
// Hooks only observation points: the draw gate (0x14150d2b0), the draw (0x1415485c0) and the
// session phase table.  Logs the regulation id they are called with and what they return, so
// we can tell "never called" from "called and refused".  Nothing is written.

'use strict';

const log = (s) => { const t = String(s); console.log(t); send({ kind: 'log', text: t }); };

function main() {
  const exe = Process.enumerateModules().find((m) => m.name.toLowerCase().includes('fl_2026'));
  if (!exe) { log('FL_2026.exe not loaded'); return; }
  const b = exe.base;
  const owner = new NativeFunction(b.add(0x14b6a60), 'pointer', []);
  const findrec = new NativeFunction(b.add(0x14bc860), 'pointer', ['pointer', 'uint16']);
  const phkind = new NativeFunction(b.add(0x150af30), 'uint64', ['pointer', 'uint64']);

  const interesting = [200, 46, 36, 11, 130];

  try {
    Interceptor.attach(b.add(0x150d2b0), {
      onEnter(args) {
        this.reg = args[0].readU16() & 0x3ff;
        this.on = interesting.includes(this.reg);
      },
      onLeave(retval) {
        if (this.on || retval.toInt32() === 2)
          log('GATE reg=' + this.reg + ' -> ' + retval.toInt32());
      },
    });
    log('hook gate installed');
  } catch (e) { log('gate hook failed ' + e); }

  try {
    Interceptor.attach(b.add(0x15485c0), {
      onEnter(args) {
        let n = -1;
        try {
          const v = args[1];
          const p = v.readPointer();
          const q = v.add(8).readPointer();
          if (!p.isNull() && q.compare(p) >= 0) n = q.sub(p).toInt32() / 4;
        } catch (e) { }
        log('DRAW reg=' + (args[0].toInt32() & 0xffff) + ' n=' + n);
      },
    });
    log('hook draw installed');
  } catch (e) { log('draw hook failed ' + e); }

  let last = '';
  function tick() {
    try {
      const ctx = owner();
      if (ctx.isNull()) return;
      const block = ctx.add(0x48).readPointer();
      if (block.isNull()) return;
      const mode = block.add(0x183789c).readU32();
      const rows = [];
      for (let i = 0; i < 0x12c; i++) {
        const r = block.add(0xc12e9c).add(i * 0x314);
        const key = r.readU16();
        if (key === 0xffff || key === 0) continue;
        const rid = key & 0x3ff;
        const cid = r.add(0x80).readU32();
        if (interesting.includes(rid) || interesting.includes(cid))
          rows.push(i + ':k=' + key + '/c=' + cid + '/s=' + r.add(0x84).readU32() +
                    '/cl=' + (r.add(0x30c).readU8() & 0x7f));
      }
      const line = 'mode=' + mode + ' [' + rows.join(' ') + ']';
      if (line !== last) { last = line; log(line); }
    } catch (e) { }
  }
  tick();
  setInterval(tick, 1500);

  for (const cid of [131, 36]) {
    const buf = Memory.alloc(4);
    buf.writeU32(cid);
    let ks = '';
    for (let k = 1; k <= 4; k++) ks += ' k' + k + '=' + phkind(buf, k).toNumber();
    log('phkind ' + cid + ks);
  }
  const ctx0 = owner();
  if (!ctx0.isNull()) {
    const blk = ctx0.add(0x48).readPointer();
    for (const reg of [200, 46]) {
      const rec = findrec(blk, reg);
      log('findrec(' + reg + ')=' + rec +
          (rec.isNull() ? '' : ' key=' + rec.readU16() + ' cid=' + rec.add(0x80).readU32() +
           ' state=' + rec.add(0x84).readU32()));
    }
  }
  log('ready');
}

main();
