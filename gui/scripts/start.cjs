const { spawnSync, spawn } = require('node:child_process');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
require('./platform.cjs').prepare(root);
const build = spawnSync(process.execPath, [path.join(root,'scripts/build.cjs')], { cwd: root, stdio: 'inherit', shell: false });
if(build.error){console.error(build.error.message);process.exit(1);}
if (build.status !== 0) process.exit(build.status || 1);
const binary = require('electron');
const env = { ...process.env }; delete env.ELECTRON_RUN_AS_NODE;
const app = spawn(binary, ['.'], { cwd: root, stdio: 'inherit', env });
app.on('error', e => { console.error(e.message); process.exit(1); });
app.on('exit', code => process.exit(code || 0));
