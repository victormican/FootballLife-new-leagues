// trace_resolve -- what cid does the cup menu resolve, and which regulation keys does the
// session builder use?  Hooks the per-item resolver (0x140b1cda0), the key-list resolver
// (0x140eadca0) and phkind (0x14150af30).

'use strict';

const log = (s) => { const t = String(s); console.log(t); send({ kind: 'log', text: t }); };

function main() {
  const exe = Process.enumerateModules().find((m) => m.name.toLowerCase().includes('fl_2026'));
  if (!exe) { log('FL_2026.exe not loaded'); return; }
  const b = exe.base;

  // per-item resolver: rcx -> { u32 cid, u8 clubs, u8 has_group, u8 f6, u8 f7, u8 f8 }
  Interceptor.attach(b.add(0xb1cda0), {
    onEnter(args) {
      this.item = args[0];
      this.cid = this.item.readU32();
    },
    onLeave() {
      let s = '';
      try {
        const bytes = new Uint8Array(this.item.readByteArray(12));
        s = Array.from(bytes).map((x) => x.toString(16).padStart(2, '0')).join('');
      } catch (e) { s = '?'; }
      log('RESOLVE cid=' + this.cid + ' -> ' + s);
    },
  });

  // key-list resolver: rcx -> std::vector<u16> { begin, end }
  Interceptor.attach(b.add(0xeadca0), {
    onEnter(args) {
      const v = args[0];
      const p = v.readPointer();
      const q = v.add(8).readPointer();
      let keys = [];
      try {
        if (!p.isNull() && q.compare(p) >= 0 && q.sub(p).toInt32() <= 64) {
          const n = q.sub(p).toInt32() / 2;
          for (let i = 0; i < n; i++) keys.push(p.add(i * 2).readU16());
        }
      } catch (e) { }
      log('KEYLIST n=' + keys.length + ' [' + keys.join(',') + ']');
    },
  });

  // phkind(cid*, kind)
  Interceptor.attach(b.add(0x150af30), {
    onEnter(args) { this.cid = args[0].readU32(); this.k = args[1].toInt32(); },
    onLeave(retval) { log('phkind cid=' + this.cid + ' k=' + this.k + ' -> ' + retval.toNumber()); },
  });

  log('ready');
}

main();
