const {spawnSync}=require('node:child_process');
const path=require('node:path');
const root=path.resolve(__dirname,'..');
for(const args of [[require.resolve('typescript/bin/tsc'),'--noEmit'],[path.join(root,'node_modules/vite/bin/vite.js'),'build']]){
 const result=spawnSync(process.execPath,args,{cwd:root,stdio:'inherit',shell:false});
 if(result.error){console.error(result.error.message);process.exit(1);}
 if(result.status!==0)process.exit(result.status||1);
}
