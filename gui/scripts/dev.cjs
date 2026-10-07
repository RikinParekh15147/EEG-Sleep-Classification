const { spawn } = require('node:child_process');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const vite = spawn(process.execPath, [path.join(root, 'node_modules/vite/bin/vite.js')], { cwd: root, stdio: 'inherit' });
let electron;
async function launch() {
  for (let i = 0; i < 80; i++) {
    try { const r = await fetch('http://127.0.0.1:5173'); if (r.ok) break; } catch {}
    await new Promise(r => setTimeout(r, 150));
  }
  const env = { ...process.env, SLEEP_DEV_URL: 'http://127.0.0.1:5173' }; delete env.ELECTRON_RUN_AS_NODE;
  electron = spawn(require('electron'), ['.'], { cwd: root, stdio: 'inherit', env });
  electron.on('exit', () => { vite.kill(); process.exit(); });
}
process.on('SIGINT', () => { vite.kill(); electron?.kill(); process.exit(); });
launch().catch(e => { console.error(e); vite.kill(); process.exit(1); });
