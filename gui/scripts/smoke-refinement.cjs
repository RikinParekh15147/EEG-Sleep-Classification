// Exercise the current GUI bridge and worker on SN009 in an existing mounted runtime.
const fs=require('node:fs'),path=require('node:path');
const {Bridge}=require('../electron/bridge.cjs'),{Store}=require('../electron/store.cjs'),{py}=require('../electron/service.cjs');
const root=path.resolve(__dirname,'..'),bridge=new Bridge(root),store=new Store(path.dirname(root),path.join(root,'.runtime/worker-check'));
const settings={...store.settings(),session:process.env.SLEEP_COLAB_SESSION||'eeg-refinement-audit',persistDrive:false,accelerator:'CPU',batchSize:128,refinement:true,preprocessedAcknowledged:true,assumeContiguous:true};
const remote=code=>bridge.request('exec',{settings,code,timeout:60},150000);
(async()=>{
 const timer=setTimeout(()=>{bridge.close();console.error('Worker check timed out');process.exit(2);},12*60*1000);
 try{
  await bridge.start(settings);await bridge.request('discover',{settings},90000);
  const data=store.bootstrap(),id='n1n2-worker-check-'+Date.now(),remoteRoot='/content/eeg_sleep_studio/'+id;
  await remote(`import json\nfrom pathlib import Path\nPath(${JSON.stringify(remoteRoot)}).mkdir(parents=True,exist_ok=True)\nprint('SLEEP_JSON:'+json.dumps({'ok':True}))`);
  for(const name of ['core.py','refinement.py','worker.py'])await bridge.request('upload',{settings,local:await bridge.linuxPath(path.join(root,'pipeline',name),settings.distro),remote:remoteRoot+'/'+name},960000);
  const refinement=store.read(store.baseline,'refinement_model.json'),reference=store.read(store.baseline,'reference_stats.json');
  settings.projectHashes=Object.fromEntries(store.read(store.baseline,'data_manifest.json').map(r=>[r.subject_id,r.sha256]));
  const transition={...data.transition,matrix:store.read(store.legacy,'transition_matrix.csv').map(r=>['Wake','N1','N2','N3','REM'].map(n=>r[n]))};
  const config={id,kind:'inference',settings,inputs:[{id:'SN009',source:'project',path:settings.processedPath+'/SN009.npz'}],transition,refinement,reference};
  await remote(`import json,sys,subprocess\nfrom pathlib import Path\np=Path(${JSON.stringify(remoteRoot)})\n(p/'config.json').write_text(json.dumps(${py(config)}))\nwith (p/'worker.log').open('w') as log:process=subprocess.Popen([sys.executable,str(p/'worker.py'),str(p/'config.json')],stdout=log,stderr=log,start_new_session=True)\nprint('SLEEP_JSON:'+json.dumps({'pid':process.pid}))`);
  for(let i=0;i<100;i++){
   const state=await remote(`import json\nfrom pathlib import Path\np=Path(${JSON.stringify(remoteRoot)})\nf=p/'status.json'\nprint('SLEEP_JSON:'+json.dumps(json.loads(f.read_text()) if f.exists() else {'status':'starting','step':'Importing packages'}))`);
   console.log(state.step+' '+(state.progress||0)+'%');
   if(['failed','cancelled'].includes(state.status))throw new Error(state.error);
   if(state.status==='completed'){
    const dest=path.join(root,'.runtime/worker-check');fs.mkdirSync(dest,{recursive:true});
    const archive=path.join(dest,'results.zip');await bridge.request('download',{settings,remote:state.bundle,local:await bridge.linuxPath(archive,settings.distro)},960000);
    await bridge.request('unpack',{archive:await bridge.linuxPath(archive,settings.distro),destination:await bridge.linuxPath(path.join(dest,'artifacts'),settings.distro)},180000);
    const actual=store.read(path.join(dest,'artifacts'),'test_epoch_predictions.csv');
    const expected=data.baseline.predictions.filter(r=>r.subject_id==='SN009');
    if(actual.length!==901||actual.some((r,i)=>r.raw_prediction!==expected[i].raw_prediction||r.refined_prediction!==expected[i].refined_prediction))throw new Error('Live predictions differ from verified SN009');
    const profiles=store.read(path.join(dest,'artifacts'),'subject_profiles.json');
    if(profiles.find(p=>p.source==='refined').sleep_health_deviation_profile!=='Mild Deviation')throw new Error('SN009 profile mismatch');
    console.log('Live GUI bridge, all 901 raw/refined predictions, profile and artifact transfer passed.');return;
   }
   await new Promise(resolve=>setTimeout(resolve,6000));
  }
  throw new Error('Worker polling limit exceeded');
 }finally{clearTimeout(timer);bridge.close();}
})().catch(error=>{console.error(error.message);process.exitCode=1;});
