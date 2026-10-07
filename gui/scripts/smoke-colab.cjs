// Explicit integration check against an existing session. Does not create or stop runtimes.
const fs=require('node:fs');const path=require('node:path');const {Store}=require('../electron/store.cjs');const {Bridge}=require('../electron/bridge.cjs');const {Service}=require('../electron/service.cjs');
const root=path.resolve(__dirname,'..'),store=new Store(path.dirname(root),path.join(root,'.runtime/live-check'));store.init();
store.saveSettings({session:process.env.SLEEP_TEST_SESSION||(process.argv.includes('--connect')?'eeg-sleep-studio-test':'eeg-diagnostics'),persistDrive:false,accelerator:'CPU'});
const bridge=new Bridge(root),service=new Service(store,bridge);let timer;
service.on('event',e=>{if(e.event==='auth-prompt'){console.error('Interactive Google login is required; complete it through the desktop app.');service.close();process.exitCode=2;}if(e.event==='connection')console.log(e.connection.state+': '+e.connection.message);if(e.event==='run')console.log(e.run.id+': '+e.run.step+' ('+e.run.progress+'%)');});
(async()=>{timer=setTimeout(()=>{console.error('Live check timed out.');service.close();process.exit(2);},10*60*1000);
 try{const discovered=await service.discover();console.log('Available sessions:',discovered.sessions.map(s=>s.name).join(', ')||'none');
  if(!discovered.sessions.some(s=>s.name===store.settings().session)&&!process.argv.includes('--connect'))throw new Error('The requested existing session is unavailable. No runtime was allocated.');
  const connection=process.argv.includes('--connect')?await service.connect():await service.probe();console.log('Runtime diagnostics:',JSON.stringify({checks:connection.checks,packages:connection.packages,gpu:connection.gpu}));
  if(process.argv.includes('--run-example')){
   const manifest=await service.startRun({recordings:['SN009'],source:'project',kind:'inference',name:'GUI integration check · SN009'});
   await new Promise((resolve,reject)=>{service.on('event',event=>{if(event.event==='run'&&event.run.id===manifest.id){if(event.run.status==='completed')resolve();else if(['failed','interrupted'].includes(event.run.status))reject(new Error(event.run.error||event.run.step));}});});
   const result=store.run(manifest.id);console.log('Example result:',JSON.stringify(result.metrics));if(result.predictions.length!==901)throw new Error('Expected 901 SN009 epochs');
   console.log('SN009 full GUI pipeline passed, with '+result.artifacts.length+' saved artifacts.');
  }
 }finally{clearTimeout(timer);service.close();}
})().catch(e=>{console.error(e.message);process.exitCode=1;});
