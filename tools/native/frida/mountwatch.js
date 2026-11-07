// mountwatch -- catch the exact reason the cup screen does not mount.
//
// 0x141e3f4c0 is the mount: it needs (rows[0x0a] || rows[0x0b]) and rows[0x3d0] != rows[0x3d8],
// then 0x1424bea50() != 0, and finally calls the mode's +0x120.  This logs every call with the
// values the condition reads, so pressing ENTER on a cup tells us which leg fails.
//
// 0x140e43450 is the shared enter: it logs the +0xd8 result and the row loop.

'use strict';

const log = (s) => {
  const t = String(s);
  console.log(t);
  send({ kind: 'log', text: t });
};

function main() {
  const exe = Process.enumerateModules().find(
    (m) => m.name.toLowerCase().includes('fl_2026'));
  if (!exe) { log('FL_2026.exe not loaded'); return; }

  try {
    Interceptor.attach(exe.base.add(0x1e3f4c0), {
      onEnter(args) {
        const self = args[0];
        try {
          const rows = self.add(0x88).readPointer();
          const a = rows.add(0x0a).readU8();
          const b = rows.add(0x0b).readU8();
          const vb = rows.add(0x3d0).readPointer();
          const ve = rows.add(0x3d8).readPointer();
          const rb = rows.add(0x70).readPointer();
          const re = rows.add(0x78).readPointer();
          const nr = rb.isNull() || re.compare(rb) < 0 ? -1 : re.sub(rb).toInt32() / 0x50;
          log('MOUNT self=' + self + ' rowsObj=' + rows +
              ' flagA=' + a + ' flagB=' + b +
              ' rows=' + nr + ' mountVec=' + vb + '..' + ve +
              (vb.equals(ve) ? '  MOUNT-VEC-VACIO' : ''));
        } catch (e) { log('MOUNT error ' + e); }
      },
    });
    log('hook mount installed');
  } catch (e) { log('hook mount failed ' + e); }

  try {
    Interceptor.attach(exe.base.add(0xe43450), {
      onEnter(args) {
        try {
          const self = args[0];
          const b = self.add(0x90).readPointer();
          const e2 = self.add(0x98).readPointer();
          const n = b.isNull() || e2.compare(b) < 0 ? -1 : e2.sub(b).toInt32() / 12;
          log('ENTER self=' + self + ' items=' + n);
        } catch (e) { log('ENTER error ' + e); }
      },
      onLeave(retval) { log('ENTER -> ' + retval); },
    });
    log('hook enter installed');
  } catch (e) { log('hook enter failed ' + e); }

  log('ready');
}

main();
