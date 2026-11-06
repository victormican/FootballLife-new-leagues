// vanilla -- put the cup menu back to the game's own initializer and watch it.
//
// fl26swiss.dll replaces the vtable slot 0x142692d18 with cupsel_handler, which filters cups whose
// group phase holds more than 32 clubs and appends the world cups.  This script writes the game's
// original 0x140b1c990 back into the slot (the DLL checked that value at install time), so the Cup
// menu of Kick Off runs exactly as shipped.  If the list still closes with it, the list is not what
// breaks; if it works, the handler is.

'use strict';

const MODULE = 'FL_2026.exe';
const SLOT = 0x2692d18;
const ORIG = 0xb1c990;

const log = (text) => {
  const s = String(text);
  console.log(s);
  send({ kind: 'log', text: s });
};

function main() {
  const exe = Process.enumerateModules().find((m) => m.name.toLowerCase() === MODULE.toLowerCase());
  if (!exe) { log('FL_2026.exe not loaded'); return; }

  const slot = exe.base.add(SLOT);
  const before = slot.readPointer();
  log('slot before = ' + before + ' (base+' + before.sub(exe.base) + ')');
  try {
    Memory.protect(slot, 8, 'rw-');
    slot.writePointer(exe.base.add(ORIG));
    log('slot after  = ' + slot.readPointer() + ' (base+' + slot.readPointer().sub(exe.base) + ')');
  } catch (e) {
    log('patch failed: ' + e);
  }

  try {
    Interceptor.attach(exe.base.add(ORIG), {
      onEnter(args) {
        try {
          const self = args[0];
          const b = self.add(0x90).readPointer();
          const e2 = self.add(0x98).readPointer();
          const cap = self.add(0xa0).readPointer();
          const n = b.isNull() || e2.compare(b) < 0 ? -1 : e2.sub(b).toInt32() / 12;
          log('INIT(vanilla) self=' + self + ' begin=' + b + ' end=' + e2 + ' cap=' + cap + ' n=' + n);
          if (n > 0 && n < 64) {
            const cids = [];
            for (let i = 0; i < n; i++) cids.push(b.add(i * 12).readU32());
            log('  cids ' + cids.join(','));
          }
        } catch (e) { log('INIT hook error ' + e); }
      },
      onLeave(retval) { log('INIT(vanilla) leave -> ' + retval); },
    });
    log('hook vanilla init installed');
  } catch (e) {
    log('hook init failed: ' + e);
  }

  for (const [modName, fnName] of [['kernel32.dll', 'ExitProcess'],
                                   ['kernel32.dll', 'TerminateProcess'],
                                   ['ntdll.dll', 'RtlExitUserProcess'],
                                   ['ucrtbase.dll', 'abort']]) {
    try {
      const m = Process.findModuleByName(modName);
      if (!m) continue;
      const addr = m.findExportByName(fnName);
      if (!addr) { log('exit hook: ' + modName + '!' + fnName + ' missing'); continue; }
      Interceptor.attach(addr, {
        onEnter(args) {
          log('EXIT ' + modName + '!' + fnName + ' code=' + args[0] + ' from ' + this.returnAddress);
          log('  backtrace ' + Thread.backtrace(this.context, Backtracer.ACCURATE)
                                            .map((a) => {
                                              const mm = Process.findModuleByAddress(a);
                                              return mm ? mm.name + '+' + a.sub(mm.base) : a;
                                            }).join(' '));
        },
      });
      log('hook ' + modName + '!' + fnName + ' installed');
    } catch (e) {
      log('exit hook ' + modName + '!' + fnName + ' failed: ' + e);
    }
  }

  Process.setExceptionHandler((details) => {
    if (details.type !== 'access-violation') return false;
    const c = details.context;
    log('EXC address=' + details.address + ' rip=' + c.pc);
    log('  backtrace ' + Thread.backtrace(c, Backtracer.ACCURATE).map((a) => {
      const mm = Process.findModuleByAddress(a);
      return mm ? mm.name + '+' + a.sub(mm.base) : a;
    }).join(' '));
    return false;
  });

  log('ready');
}

main();
