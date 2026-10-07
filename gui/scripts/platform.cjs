const fs=require('node:fs');const path=require('node:path');const {spawnSync}=require('node:child_process');
function prepare(root){
 const marker=path.join(root,'node_modules/.sleep-platform'),current=process.platform+'-'+process.arch;
 if(!fs.existsSync(path.join(root,'node_modules/typescript'))){console.error('Dependencies are missing. Run npm install in gui/ first.');process.exit(1);}
 let installed='';try{installed=fs.readFileSync(marker,'utf8').trim();}catch{}
 let repair=installed!==current;
 try{require('esbuild').transformSync('const ok = true;',{});require('rollup');}catch{repair=true;}
 if(repair){
  console.log('Preparing dependencies for '+current+'…');
  const npm=process.platform==='win32'?'npm.cmd':'npm';
  const result=spawnSync(npm,['install','--include=optional'],{cwd:root,stdio:'inherit',shell:process.platform==='win32'});if(result.status!==0)process.exit(result.status||1);
 }
 // The installer verifies executable name, architecture/version and reuses its cache.
 const electron=spawnSync(process.execPath,[path.join(root,'node_modules/electron/install.js')],{cwd:root,stdio:'inherit'});if(electron.status!==0)process.exit(electron.status||1);
 fs.writeFileSync(marker,current);return require('electron');
}
module.exports={prepare};
