// Native Windows/Linux Electron smoke test. Uses an isolated app-data folder.
const path=require('node:path');const fs=require('node:fs');const {_electron}=require('playwright');
const root=path.resolve(__dirname,'..');
(async()=>{const app=await _electron.launch({args:[root],cwd:root,env:{...process.env,SLEEP_DATA_DIR:path.join(root,'.runtime/desktop-check')},timeout:60000});
 try{const page=await app.firstWindow();await page.getByRole('heading',{name:'Your sleep research workspace'}).waitFor({timeout:30000});
  const data=await page.evaluate(()=>window.sleep.bootstrap());if(!data.desktop||data.baseline.predictions.length!==3773)throw new Error('Native app did not load the real baseline');
  console.log('Native Electron loaded '+data.baseline.predictions.length+' epochs.');
  const folder=path.join(root,'.runtime/screenshots');fs.mkdirSync(folder,{recursive:true});await page.screenshot({path:path.join(folder,'overview.png'),fullPage:true});
  await page.getByRole('button',{name:'Results explorer',exact:true}).click();await page.getByRole('button',{name:'EEG & hypnogram',exact:true}).click();await page.getByRole('img',{name:'Normalized EEG waveform'}).waitFor();await page.screenshot({path:path.join(folder,'results.png'),fullPage:true});
  await page.getByRole('button',{name:'Connection & settings',exact:true}).click();const {Bridge}=require('../electron/bridge.cjs');const bridge=new Bridge(root);try{const distros=await bridge.distributions();await bridge.start({distro:distros[0]||'Ubuntu'});const hello=await bridge.request('hello');console.log('Windows WSL distributions: '+distros.join(', '));console.log('Windows → WSL bridge: Python '+hello.python);}finally{bridge.close();}
  const reportPath=path.join(root,'.runtime/desktop-check/report.pdf');await app.evaluate(({dialog},file)=>{dialog.showSaveDialog=async()=>({canceled:false,filePath:file});},reportPath);await page.evaluate(()=>window.sleep.exportPdf('baseline'));if(!fs.readFileSync(reportPath).subarray(0,4).equals(Buffer.from('%PDF')))throw new Error('PDF export failed');console.log('Native Electron navigation, charts, WSL bridge and PDF export passed.');
 }finally{await app.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
