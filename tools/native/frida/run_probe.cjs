// run_probe -- attach the Frida probe to the running game and write its messages to a file.
//
//   node run_probe.cjs <pid> <out-file> <seconds>
//
// The frida package lives in the npx cache that rea-agents installed (the MCP server), so the
// require is anchored there instead of adding a node_modules to this repository.

'use strict';

const fs = require('fs');
const path = require('path');
const { createRequire } = require('module');

const FRIDA_ROOT = 'C:\\Users\\viarm\\AppData\\Local\\npm-cache\\_npx\\ad9a3fdbcad992c6\\package.json';
const frida = createRequire(FRIDA_ROOT)('frida');

const pid = Number(process.argv[2]);
const out = process.argv[3];
const seconds = Number(process.argv[4] || '120');
const cupsArg = process.argv[5] || '';           // "131" or "131,200" or "" (no world cups)
const scriptPath = process.argv[6] || path.join(__dirname, 'cupmenu_probe.js');
const source = fs.readFileSync(scriptPath, 'utf8');

const lines = [];
function dump() {
  try { fs.writeFileSync(out, lines.join('\r\n') + '\r\n'); } catch (e) { /* keep going */ }
}

(async () => {
  const device = await frida.getLocalDevice();
  const session = await device.attach(pid);
  const script = await session.createScript(source);
  script.message.connect((m) => {
    const p = m.payload || {};
    const text = p.text !== undefined ? p.text : JSON.stringify(p);
    lines.push((p.kind ? p.kind + ': ' : '') + text);
    dump();
  });
  await script.load();
  dump();
  const cids = cupsArg.split(',').map((s) => Number(s.trim())).filter((n) => n > 0);
  try {
    const res = await script.exports.setcups(cids);
    lines.push('setcups [' + cids.join(',') + '] -> ' + res);
  } catch (e) {
    lines.push('setcups failed: ' + (e && e.message ? e.message : e));
  }
  dump();
  await new Promise((r) => setTimeout(r, seconds * 1000));
  try { await session.detach(); } catch (e) { lines.push('detach: ' + e.message); }
  dump();
  process.exit(0);
})().catch((e) => {
  lines.push('ERROR ' + (e && e.stack ? e.stack : e));
  dump();
  process.exit(1);
});
