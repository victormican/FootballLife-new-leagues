// phwatch -- who asks the game about our competition when the cup is opened?
//
// Hooks phkind(cid, kind) and findrec(block, regulation) and logs every call that mentions our
// ids (131 / 200) or the clone's (36 / 46), with the caller.  This names the function that
// decides which regulation goes into the session table, and whether it asks at all.

'use strict';

const log = (s) => { const t = String(s); console.log(t); send({ kind: 'log', text: t }); };

function main() {
  const exe = Process.enumerateModules().find((m) => m.name.toLowerCase().includes('fl_2026'));
  if (!exe) { log('FL_2026.exe not loaded'); return; }
  const b = exe.base;
  const base = 0x140000000;

  function where(p) {
    try {
      const a = p;
      const m = Process.findModuleByAddress(a);
      if (m && m.name.toLowerCase().includes('fl_2026')) return '+' + a.sub(m.base).toString(16);
      return m ? m.name + '+' + a.sub(m.base) : a.toString();
    } catch (e) { return '?'; }
  }

  try {
    Interceptor.attach(b.add(0x150af30), {
      onEnter(args) {
        this.cid = args[0].readU32();
        this.kind = args[1].toInt32();
        this.want = [131, 36, 130, 11].includes(this.cid);
        this.ret = this.returnAddress;
      },
      onLeave(retval) {
        if (this.want)
          log('phkind cid=' + this.cid + ' kind=' + this.kind + ' -> ' + retval.toNumber() +
              ' from=' + where(this.ret));
      },
    });
    log('hook phkind');
  } catch (e) { log('phkind failed ' + e); }

  try {
    Interceptor.attach(b.add(0x14bc860), {
      onEnter(args) {
        this.id = args[1].toUInt16 ? args[1].toUInt16() : (args[1].toInt32() & 0xffff);
        this.want = [200, 46, 36, 11].includes(this.id);
        this.ret = this.returnAddress;
      },
      onLeave(retval) {
        if (this.want)
          log('findrec reg=' + this.id + ' -> ' + (retval.isNull() ? 'null' : 'ok') +
              ' from=' + where(this.ret));
      },
    });
    log('hook findrec');
  } catch (e) { log('findrec failed ' + e); }

  log('ready');
}

main();
