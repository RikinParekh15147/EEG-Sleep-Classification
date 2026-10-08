const fs=require('node:fs');const path=require('node:path');const {spawnSync}=require('node:child_process');
function prepare(root){
 const marker=path.join(root,'node_modules/.sleep-platform'),current=process.platform+'-'+process.arch;
 if(!fs.existsSync(path.join(root,'node_modules/typescript'))){console.error('Dependencies are missing. Run npm install in gui/ first.');process.exit(1);}
 let installed='';try{installed=fs.readFileSync(marker,'utf8').trim();}catch{}
 let repair=installed!==current;
 try{require('esbuild').transformSync('const ok = true;',{});require('rollup');}catch{repair=true;}
 if(repair){
  console.log('Preparing dependencies for '+current+'…');
  const npmCli=process.env.npm_execpath;
  const result=npmCli&&fs.existsSync(npmCli)
   ?spawnSync(process.execPath,[npmCli,'install','--include=optional'],{cwd:root,stdio:'inherit',shell:false})
   :process.platform==='win32'
    ?spawnSync(process.env.ComSpec||'cmd.exe',['/d','/s','/c','npm install --include=optional'],{cwd:root,stdio:'inherit',shell:false})
    :spawnSync('npm',['install','--include=optional'],{cwd:root,stdio:'inherit',shell:false});
  if(result.error){console.error(result.error.message);process.exit(1);}
  if(result.status!==0)process.exit(result.status||1);
 }
 // The installer verifies executable name, architecture/version and reuses its cache.
 const electron=spawnSync(process.execPath,[path.join(root,'node_modules/electron/install.js')],{cwd:root,stdio:'inherit'});if(electron.status!==0)process.exit(electron.status||1);
 fs.writeFileSync(marker,current);return require('electron');
}
module.exports={prepare};
