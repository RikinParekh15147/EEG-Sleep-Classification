const { app, BrowserWindow, ipcMain, protocol, net, dialog, shell, session } = require('electron');
const fs = require('node:fs');
const path = require('node:path');
const { pathToFileURL } = require('node:url');
const { Store, confined } = require('./store.cjs');
const { Bridge } = require('./bridge.cjs');
const { Service, ACTIVE } = require('./service.cjs');
const { report } = require('./report.cjs');
const guiRoot=path.resolve(__dirname,'..'),projectRoot=path.dirname(guiRoot);
let window,service,store;
app.setName('Sleep Studio');
protocol.registerSchemesAsPrivileged([{scheme:'sleep',privileges:{standard:true,secure:true,supportFetchAPI:true,stream:true}}]);
if(!app.requestSingleInstanceLock())app.quit();
app.on('second-instance',()=>{if(window){if(window.isMinimized())window.restore();window.focus();}});
function trusted(event) {const url=event.senderFrame?.url||'';return url.startsWith('sleep://app/')||(process.env.SLEEP_DEV_URL&&url.startsWith(process.env.SLEEP_DEV_URL+'/'));}
function external(url) {
  const parsed=new URL(url);const hosts=['accounts.google.com','colab.research.google.com','sdk.cloud.google.com','physionet.org','github.com'];
  if(parsed.protocol!=='https:'||!hosts.includes(parsed.hostname)||parsed.username||parsed.password)throw new Error('External URL is not an approved HTTPS destination');
  return shell.openExternal(parsed.href);
}
async function exportRun(id,format,artifact) {
  const run=store.run(id);const filters=format==='zip'?[{name:'ZIP bundle',extensions:['zip']}]:format==='json'?[{name:'JSON report',extensions:['json']}]:[{name:'Artifact',extensions:[path.extname(artifact||'results.csv').slice(1)||'csv']}];
  const selected=await dialog.showSaveDialog(window,{defaultPath:format==='zip'?id+'.zip':format==='json'?id+'.json':path.basename(artifact||'test_epoch_predictions.csv'),filters});if(selected.canceled)return null;
  if(format==='json')fs.writeFileSync(selected.filePath,JSON.stringify({manifest:run.manifest,result:run.result,metrics:run.metrics,biomarkers:run.biomarkers},null,2));
  else if(format==='zip') {
    const existing=path.join(store.runsRoot,id,'results.zip');
    if(id!=='baseline'&&fs.existsSync(existing))fs.copyFileSync(existing,selected.filePath);
    else {
      const {zipSync}=require('fflate');
      const entries=Object.fromEntries(run.artifacts.map(file=>[file.path,new Uint8Array(fs.readFileSync(store.artifactFile(id,file.path)))]));
      entries['desktop_run.json']=new Uint8Array(Buffer.from(JSON.stringify(run.manifest,null,2)));
      fs.writeFileSync(selected.filePath,zipSync(entries,{level:6}));
    }
  } else fs.copyFileSync(store.artifactFile(id,artifact||'test_epoch_predictions.csv'),selected.filePath);
  return selected.filePath;
}
async function exportPdf(id) {
  const selected=await dialog.showSaveDialog(window,{defaultPath:id+'-report.pdf',filters:[{name:'PDF report',extensions:['pdf']}]});if(selected.canceled)return null;
  const hidden=new BrowserWindow({show:false,webPreferences:{sandbox:true,nodeIntegration:false,contextIsolation:true}});
  try {const run=store.run(id);const images=run.artifacts.filter(f=>/^(hypnogram_(?:subject_)?SN\d+|smoothed_confusion_matrix_normalized|soft_viterbi_confusion_matrix|reliability_diagram|risk_coverage_curve)\.png$/.test(f.path)).map(f=>({title:f.path.replace(/_/g,' ').replace('.png',''),data:'data:image/png;base64,'+fs.readFileSync(store.artifactFile(id,f.path)).toString('base64')}));await hidden.loadURL('data:text/html;charset=utf-8,'+encodeURIComponent(report(run,images)));const pdf=await hidden.webContents.printToPDF({printBackground:true,pageSize:'A4'});fs.writeFileSync(selected.filePath,pdf);return selected.filePath;}finally{hidden.destroy();}
}
app.whenReady().then(()=>{
  store=new Store(projectRoot,process.env.SLEEP_DATA_DIR||app.getPath('userData'));store.init();
  for(const run of store.runs())if(ACTIVE.includes(run.status))store.saveRun({...run,status:'interrupted',step:'App restarted · recover this run to check its remote status'});
  service=new Service(store,new Bridge(guiRoot));
  service.on('event',value=>{if(window&&!window.isDestroyed())window.webContents.send('sleep:event',value);});
  protocol.handle('sleep',request=>{
    try {const url=new URL(request.url);let file;
      if(url.host==='artifact') {const [id,...parts]=url.pathname.slice(1).split('/').map(decodeURIComponent);file=store.artifactFile(id,parts.join('/'));}
      else if(url.host==='app')file=confined(path.join(guiRoot,'dist'),decodeURIComponent(url.pathname.slice(1)||'index.html'));
      else return new Response('Not found',{status:404});
      return net.fetch(pathToFileURL(file).href);
    }catch{return new Response('Not found',{status:404});}
  });
  const handlers={bootstrap:()=>service.bootstrap(),settings:()=>store.settings(),saveSettings:value=>{const previous=store.settings();const changed=Object.keys(previous).some(key=>key!=='theme'&&value[key]!==undefined&&value[key]!==previous[key]);if(changed&&(service.processing||service.connectionBusy))throw new Error('Wait for the active operation before changing connection settings');const settings=store.saveSettings(value);if(changed)service.state({state:'offline',message:'Settings saved. Reconnect to verify this configuration.'});return settings;},
    discover:()=>service.discover(),connect:()=>service.connect(),mountDrive:()=>service.mountDrive(),prepareRuntime:()=>service.prepareRuntime(),browseDrive:folder=>service.browseDrive(folder),startRun:value=>service.startRun(value),cancelRun:id=>service.cancelRun(id),recoverRun:id=>service.recoverRun(id),run:id=>store.run(id),runs:()=>store.runs(),
    importFiles:async()=>{const result=await dialog.showOpenDialog(window,{properties:['openFile','multiSelections'],filters:[{name:'EEG recordings and annotations',extensions:['edf','npz']}]});return result.canceled?[]:service.registerImports(result.filePaths);},
    artifacts:id=>store.artifacts(id),artifactText:(id,file)=>store.artifactText(id,file),exportRun,exportPdf,
    openArtifact:(id,file)=>shell.openPath(store.artifactFile(id,file)),openExternal:external,authReply:value=>service.authReply(value),signal:(id,recording,epoch)=>service.signal(id,recording,epoch)};
  for(const [method,handler] of Object.entries(handlers))ipcMain.handle('sleep:'+method,async(event,...args)=>{if(!trusted(event))throw new Error('Untrusted app request');return handler(...args);});
  session.defaultSession.setPermissionRequestHandler((_webContents,_permission,callback)=>callback(false));
  window=new BrowserWindow({width:1480,height:960,minWidth:1100,minHeight:740,backgroundColor:'#0b1214',title:'Sleep Studio',autoHideMenuBar:true,webPreferences:{preload:path.join(__dirname,'preload.cjs'),contextIsolation:true,nodeIntegration:false,sandbox:true}});
  window.webContents.setWindowOpenHandler(({url})=>{external(url).catch(()=>{});return {action:'deny'};});
  window.webContents.on('will-navigate',(event,url)=>{if(!url.startsWith('sleep://app/')&&!(process.env.SLEEP_DEV_URL&&url.startsWith(process.env.SLEEP_DEV_URL)))event.preventDefault();});
  window.loadURL(process.env.SLEEP_DEV_URL||'sleep://app/index.html');
  window.on('close',event=>{if(service.processing){const choice=dialog.showMessageBoxSync(window,{type:'question',buttons:['Keep app open','Close and recover later'],defaultId:0,cancelId:0,title:'Analysis is running',message:'Closing the app disconnects progress monitoring. The Colab worker may continue; use Run History to recover it later.'});if(choice===0)event.preventDefault();}});
}).catch(e=>{dialog.showErrorBox('Sleep Studio could not start',e.stack||e.message);app.quit();});
app.on('window-all-closed',()=>app.quit());app.on('before-quit',()=>service?.close());
