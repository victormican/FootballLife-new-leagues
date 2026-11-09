// keysource -- where does the base list builder get its ten competition ids?
'use strict';
const log = (s) => { const t = String(s); console.log(t); send({ kind: 'log', text: t }); };
function main() {
  const exe = Process.enumerateModules().find((m) => m.name.toLowerCase().includes('fl_2026'));
  const b = exe.base;

  Interceptor.attach(b.add(0xb1c990), {
    onEnter(args) { log('CTOR self=' + args[0]); },
  });

  Interceptor.attach(b.add(0xc6b076), {
    onEnter() {
      try {
        const c = this.context;
        const r12 = c.r12, r13 = c.r13, r14 = c.r14, rdi = c.rdi;
        let src = '';
        try {
          for (let i = 0; i < 10; i++) src += ' ' + r12.add(i * 2).readU16();
        } catch (e) { src = ' (unreadable)'; }
        log('COPY r12=' + r12 + ' r13=' + r13 + ' r14=' + r14 + ' rdi=' + rdi + ' u16:' + src);
      } catch (e) { log('COPY hook err ' + e); }
    },
  });
  log('ready');
}
main();
