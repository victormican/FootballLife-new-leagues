// cupfull -- everything we need in one attach: who asks about our ids, the draw gate, the draw,
// and the session table.
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

  function where(p) {
    try {
      const m = Process.findModuleByAddress(p);
      if (m && m.name.toLowerCase().includes('fl_2026')) return '+' + p.sub(m.base).toString(16);
      return m ? m.name + '+' + p.sub(m.base) : p.toString();
    } catch (e) { return '?'; }
  }

  Interceptor.attach(b.add(0x150af30), {
    onEnter(args) {
      this.cid = args[0].readU32();
      this.kind = args[1].toInt32();
      this.want = [131, 36, 130, 11].includes(this.cid);
      this.ret = this.returnAddress;
    },
    onLeave(retval) {
      if (this.want)
        log('phkind cid=' + this.cid + ' k=' + this.kind + ' -> ' + retval.toNumber() +
            ' from=' + where(this.ret));
    },
  });

  Interceptor.attach(b.add(0x14bc860), {
    onEnter(args) {
      this.id = args[1].toInt32() & 0xffff;
      this.want = [200, 46, 36, 11].includes(this.id);
      this.ret = this.returnAddress;
    },
    onLeave(retval) {
      if (this.want)
        log('findrec reg=' + this.id + ' -> ' + (retval.isNull() ? 'null' : 'ok') +
            ' from=' + where(this.ret));
    },
  });

  Interceptor.attach(b.add(0x150d2b0), {
    onEnter(args) { this.reg = args[0].readU16() & 0x3ff; this.on = interesting.includes(this.reg); },
    onLeave(retval) { if (this.on || retval.toInt32() === 2) log('GATE reg=' + this.reg + ' -> ' + retval.toInt32()); },
  });

  Interceptor.attach(b.add(0x15485c0), {
    onEnter(args) { log('DRAW reg=' + (args[0].toInt32() & 0xffff)); },
  });

  log('hooks ready');

  let last = '';
  function tick() {
    try {
      const ctx = owner();
      if (ctx.isNull()) return;
      const block = ctx.add(0x48).readPointer();
      if (block.isNull()) return;
      const mode = block.add(0x183789c).readU32();
      const count = block.add(0xd0bcf4).readU32();
      const rows = [];
      for (let i = 0; i < 0x12c; i++) {
        const r = block.add(0xc12e9c).add(i * 0x314);
        const key = r.readU16();
        if (key === 0xffff || key === 0) continue;
        const rid = key & 0x3ff;
        const cid = r.add(0x80).readU32();
        if (interesting.includes(rid) || interesting.includes(cid))
          rows.push(i + ':k=' + key + '/c=' + cid + '/s=' + r.add(0x84).readU32());
      }
      const line = 'mode=' + mode + ' count=' + count + ' [' + rows.join(' ') + ']';
      if (line !== last) { last = line; log(line); }
    } catch (e) { }
  }
  tick();
  setInterval(tick, 1500);

  const ctx0 = owner();
  if (!ctx0.isNull()) {
    const blk = ctx0.add(0x48).readPointer();
    for (const reg of [200, 46]) {
      const rec = findrec(blk, reg);
      log('findrec(' + reg + ')=' + (rec.isNull() ? 'null' : 'ok') +
          (rec.isNull() ? '' : ' state=' + rec.add(0x84).readU32() +
           ' clubs=' + (rec.add(0x30c).readU8() & 0x7f)));
    }
  }
  log('ready');
}

main();
