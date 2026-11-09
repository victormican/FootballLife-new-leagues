// mapwatch -- who writes the map that faults (0x1437ce9c8)?
//
// MemoryAccessMonitor puts a guard on the page and reports every access with the address and the
// thread that did it; we keep the writes and their backtrace.  The map is the one the crash dump
// points at (rcx = 0x1437ce9c8, walker at 0x141ae606f).

'use strict';

const MAP = 0x1437CE9C8;

const log = (s) => {
  const t = String(s);
  console.log(t);
  send({ kind: 'log', text: t });
};

function fmt(a) {
  const m = Process.findModuleByAddress(a);
  return m ? (m.name + '+' + a.sub(m.base)) : a.toString();
}

let writes = 0;

function main() {
  const page = ptr(MAP).and(ptr('0xfffffffffffff000'));
  log('watching page ' + page + ' (map ' + ptr(MAP) + ')');
  MemoryAccessMonitor.enable([{ base: page, size: 0x1000 }], {
    onAccess(details) {
      try {
        if (details.operation === 'write') {
          writes++;
          if (writes <= 25) {
            const bt = Thread.backtrace().slice(0, 10).map(fmt).join(' ');
            log('W ' + details.address + ' from ' + details.from + ' bt ' + bt);
          }
        }
      } catch (e) { /* keep going */ }
    },
  });
  log('armed');
}

main();
