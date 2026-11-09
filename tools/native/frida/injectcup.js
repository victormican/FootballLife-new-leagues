// injectcup -- our cup, without the mod stack.
//
// Two things, both in memory:
//   1. regulation record +0x84 = 2   (the draw gate 0x14150d2b0 returns it; 2 = draw)
//   2. append {cid 50} to the cup list inside the menu's init (0x140b1c990), before the original
//      runs, exactly what fl26swiss does at +0xd8 -- but here so the rest of the stack stays off.
//
// Run it, then open Kick Off > Cup: "Copa Test" should be in the list, and selecting it should
// reach the draw.

'use strict';

const REG = 200;
const CID = 50;

const log = (s) => {
  const t = String(s);
  console.log(t);
  send({ kind: 'log', text: t });
};

function main() {
  const exe = Process.enumerateModules().find(
    (m) => m.name.toLowerCase().includes('fl_2026'));
  if (!exe) { log('FL_2026.exe not loaded'); return; }

  const owner = new NativeFunction(exe.base.add(0x14b6a60), 'pointer', []);
  const findrec = new NativeFunction(exe.base.add(0x14bc860), 'pointer', ['pointer', 'uint64']);
  const o = owner();
  const block = o.isNull() ? ptr(0) : o.add(0x48).readPointer();

  // 1. the gate's field
  if (!block.isNull()) {
    try {
      const rec = findrec(block, REG);
      if (!rec.isNull()) {
        log('reg ' + REG + ' +84 before = ' + rec.add(0x84).readU32());
        rec.add(0x84).writeU32(2);
        log('reg ' + REG + ' +84 after  = ' + rec.add(0x84).readU32());
      } else {
        log('reg ' + REG + ' record not found');
      }
    } catch (e) { log('state write error ' + e); }
  }

  // 2. append the competition to the list before the menu builds it
  try {
    Interceptor.attach(exe.base.add(0xb1c990), {
      onEnter(args) {
        const self = args[0];
        try {
          const b = self.add(0x90).readPointer();
          const e2 = self.add(0x98).readPointer();
          const cap = self.add(0xa0).readPointer();
          const n = b.isNull() || e2.compare(b) < 0 ? 0 : e2.sub(b).toInt32() / 12;
          const room = (cap.compare(b) > 0) ? cap.sub(b).toInt32() / 12 : n;
          let there = false;
          for (let i = 0; i < n; i++) if (b.add(i * 12).readU32() === CID) there = true;
          log('INIT n=' + n + ' room=' + room + ' cid ' + CID + ' present=' + there);
          if (!there && n < room) {
            const w = b.add(n * 12);
            w.writeU32(CID);
            w.add(4).writeU32(0xffff);
            w.add(8).writeU32(0);
            self.add(0x98).writePointer(w.add(12));
            log('appended cid ' + CID + ' at index ' + n);
          }
        } catch (e) { log('append error ' + e); }
      },
    });
    log('hook cup init installed');
  } catch (e) { log('hook failed ' + e); }
  // 3. watch the gate and the draw
  try {
    Interceptor.attach(exe.base.add(0x150d2b0), {
      onEnter(args) { this.reg = args[0].and(0xffff).toInt32(); },
      onLeave(retval) {
        if (this.reg === REG || this.reg === 46) {
          log('GATE reg=' + this.reg + ' -> ' + retval);
        }
      },
    });
    log('hook gate installed');
  } catch (e) { log('gate hook failed ' + e); }

  try {
    Interceptor.attach(exe.base.add(0x15485c0), {
      onEnter(args) {
        try {
          const reg = args[0].and(0xffff).toInt32();
          const v = args[1];
          const b = v.readPointer();
          const e2 = v.add(8).readPointer();
          const n = b.isNull() ? -1 : e2.sub(b).toInt32() / 4;
          log('DRAW reg=' + reg + ' clubs=' + n + ' ret=' + this.returnAddress);
        } catch (e) { log('DRAW log error ' + e); }
      },
    });
    log('hook draw installed');
  } catch (e) { log('draw hook failed ' + e); }

  // 4. is the scheduler root called at all for our regulation?
  try {
    Interceptor.attach(exe.base.add(0x13481f3), {
      onEnter(args) { this.reg = args[1].and(0xffff).toInt32(); },
      onLeave(retval) {
        if (this.reg === REG || this.reg === 46) {
          log('ROOT reg=' + this.reg + ' ret=' + this.returnAddress + ' -> ' + retval);
        }
      },
    });
    log('hook root installed');
  } catch (e) { log('root hook failed ' + e); }

  try {
    Interceptor.attach(exe.base.add(0x1546c70), {
      onEnter(args) { this.reg = args[0].and(0xffff).toInt32(); },
      onLeave(retval) {
        if (this.reg === REG || this.reg === 46) log('PHFIN reg=' + this.reg + ' -> ' + retval);
        if (this.reg === REG) {
          retval.replace(ptr(1));                 // EXPERIMENTO: fingir que la fase esta lista
          log('PHFIN reg=' + this.reg + ' forced -> 1');
        }
      },
    });
    log('hook phfin installed');
  } catch (e) { log('phfin hook failed ' + e); }

  log('ready');
}

main();
