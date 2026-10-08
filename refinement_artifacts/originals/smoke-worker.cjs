// Test the real archived checkpoint on the real corrected SN001 input in an
// existing isolated CPU session. Drive is not needed and original files stay intact.
const fs=require('node:fs');const path=require('node:path');const {Bridge}=require('../electron/bridge.cjs');const {Store}=require('../electron/store.cjs');const {py}=require('../electron/service.cjs');
const root=path.resolve(__dirname,'..'),bridge=new Bridge(root),store=new Store(path.dirname(root),path.join(root,'.runtime/worker-check'));
const settings={...store.settings(),session:'eeg-sleep-studio-test',persistDrive:false,accelerator:'CPU',batchSize:128,smoothing:true,emissionWeight:.9,preprocessedAcknowledged:true,assumeContiguous:true};
const remote=async code=>bridge.request('exec',{settings,code,timeout:180},240000);
(async()=>{let timer=setTimeout(()=>{bridge.close();console.error('Remote worker check timed out');process.exit(2);},12*60*1000);
 try{await bridge.start(settings);const found=await bridge.request('discover',{settings},90000);if(!found.sessions.some(s=>s.name===settings.session))throw new Error('The isolated CPU test session is unavailable');
 console.log('Checking runtime packages');await remote(`import json,sys,subprocess
import importlib.metadata as md
missing=[]
for p,v in [('mne','1.13.2'),('matplotlib','3.10.8')]:
 try:md.version(p)
 except md.PackageNotFoundError:missing.append(p+'=='+v)
if missing:subprocess.run([sys.executable,'-m','pip','install',*missing],check=True)
print('SLEEP_JSON:'+json.dumps({'installed':missing}))`);
 const id='worker-check-'+Date.now(),remoteRoot='/content/eeg_sleep_studio/'+id;
 await remote(`import json\nfrom pathlib import Path\nPath(${JSON.stringify(remoteRoot)}).mkdir(parents=True,exist_ok=True)\nprint('SLEEP_JSON:'+json.dumps({'ok':True}))`);
 const input=path.join(path.dirname(root),'ppt_artifacts/corrected_test_inputs/SN001.npz');if(!fs.existsSync(input))throw new Error('The actual corrected SN001 input is not available locally');
 for(const [local,name] of [[path.join(root,'pipeline/core.py'),'core.py'],[path.join(root,'pipeline/worker.py'),'worker.py'],[path.join(path.dirname(root),'ppt_artifacts/authoritative_checkpoint.keras'),'checkpoint.keras'],[input,'SN001.npz']]){
  console.log('Uploading '+name);await bridge.request('upload',{settings,local:await bridge.linuxPath(local,settings.distro),remote:remoteRoot+'/'+name},960000);
 }
 const transition=store.bootstrap().transition;transition.matrix=store.read(store.baseline,'transition_matrix.csv').map(r=>['Wake','N1','N2','N3','REM'].map(n=>r[n]));settings.checkpointPath=remoteRoot+'/checkpoint.keras';settings.testIds=['SN001'];
 const config={id,kind:'inference',settings,inputs:[{id:'SN001',source:'local',path:remoteRoot+'/SN001.npz'}],transition};
 await remote(`import json,sys,subprocess\nfrom pathlib import Path\np=Path(${JSON.stringify(remoteRoot)})\n(p/'config.json').write_text(json.dumps(${py(config)}))\nwith (p/'worker.log').open('w') as log:process=subprocess.Popen([sys.executable,str(p/'worker.py'),str(p/'config.json')],stdout=log,stderr=log,start_new_session=True)\nprint('SLEEP_JSON:'+json.dumps({'pid':process.pid}))`);
 for(let i=0;i<120;i++){
  const value=await remote(`import json\nfrom pathlib import Path\np=Path(${JSON.stringify(remoteRoot)})\nf=p/'status.json'\nprint('SLEEP_JSON:'+json.dumps(json.loads(f.read_text()) if f.exists() else {'status':'starting','step':'Importing runtime packages'}))`);console.log(value.step+' · '+(value.progress||0)+'%');
  if(['failed','cancelled'].includes(value.status))throw new Error(value.error);
  if(value.status==='completed'){
   const destination=path.join(root,'.runtime/worker-check');fs.mkdirSync(destination,{recursive:true});const archive=path.join(destination,'results.zip');await bridge.request('download',{settings,remote:value.bundle,local:await bridge.linuxPath(archive,settings.distro)},960000);await bridge.request('unpack',{archive:await bridge.linuxPath(archive,settings.distro),destination:await bridge.linuxPath(path.join(destination,'artifacts'),settings.distro)},180000);
   const metrics=JSON.parse(fs.readFileSync(path.join(destination,'artifacts/overall_metrics.json'),'utf8'));console.log('Real Colab inference metrics:',JSON.stringify(metrics));
   if(metrics.raw.test_epochs!==854||Math.abs(metrics.raw.accuracy-.4812646370023419)>1e-9||Math.abs(metrics.soft_viterbi.accuracy-.5807962529274004)>1e-9)throw new Error('SN001 metrics differ from the verified run');
   console.log('Real archived model, complete SN001 input, smoothing and artifact transfer passed.');return;
  }
  await new Promise(r=>setTimeout(r,6000));
 }
 throw new Error('Worker did not complete before the polling limit');
 }finally{clearTimeout(timer);bridge.close();}
})().catch(e=>{console.error(e.message);process.exitCode=1;});
