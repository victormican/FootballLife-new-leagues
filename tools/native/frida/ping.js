// ping -- verify Frida instrumentation is live on this process.
'use strict';
const log = (s) => { const t = String(s); console.log(t); send({ kind: 'log', text: t }); };
function main() {
  const exe = Process.enumerateModules().find((m) => m.name.toLowerCase().includes('fl_2026'));
  const b = exe.base;
  let n = 0;
  Interceptor.attach(b.add(0x14b6a60), { onEnter() { n++; } });
  Interceptor.attach(b.add(0xb1c990), { onEnter() { log('CTOR fired'); } });
  Interceptor.attach(b.add(0xc6b076), { onEnter() { log('COPY fired'); } });
  setTimeout(() => log('owner calls in 3s: ' + n), 3000);
}
main();
