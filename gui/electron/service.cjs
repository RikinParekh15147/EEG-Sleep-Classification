const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const { EventEmitter } = require('node:events');
const { atomicJson } = require('./store.cjs');
const py = value => `json.loads(${JSON.stringify(JSON.stringify(value))})`;
const ACTIVE = ['queued','preparing','running','downloading'];
function remotePath(value) {
  if(typeof value !== 'string'||!value.startsWith('/content/')||value.length>2000||value.split('/').includes('..')||/[\0\r\n]/.test(value)) throw new Error('Choose an absolute /content/ path without parent traversal');
  return value;
}
function validateOptions(value={}) {
  const kind=value.kind||'inference';if(!['inference','training','preprocess'].includes(kind))throw new Error('Unknown job type');
  const batchSize=Number(value.batchSize ?? 128),emissionWeight=Number(value.emissionWeight ?? .9),epochs=Number(value.epochs ?? 10),learningRate=Number(value.learningRate ?? .0001);
  if(!Number.isInteger(batchSize)||batchSize<1||batchSize>512)throw new Error('Batch size must be an integer from 1 to 512');
  if(!Number.isFinite(emissionWeight)||emissionWeight<0||emissionWeight>2)throw new Error('Smoothing weight must be from 0 to 2');
  if(!Number.isInteger(epochs)||epochs<1||epochs>100)throw new Error('Epoch count must be an integer from 1 to 100');
  if(!Number.isFinite(learningRate)||learningRate<.000001||learningRate>.01)throw new Error('Learning rate must be from 0.000001 to 0.01');
  for(const key of ['smoothing','assumeContiguous','preprocessedAcknowledged'])if(value[key]!==undefined&&typeof value[key]!=='boolean')throw new Error(`Invalid ${key}`);
  return {kind,batchSize,emissionWeight,epochs,learningRate,smoothing:value.smoothing??true,assumeContiguous:value.assumeContiguous??false,preprocessedAcknowledged:value.preprocessedAcknowledged??false};
}
class Service extends EventEmitter {
  constructor(store,bridge) { super();this.store=store;this.bridge=bridge;this.connection={state:'offline',message:'Saved results are available offline.'};this.queue=[];this.processing=false;this.logs=[];this.imports=new Map();this.prompt=null;this.authUrls=[];this.connectionBusy=false;this.timers=new Set();
    bridge.on('event',e=>{if(e.event==='auth-url'){this.authUrls=[...this.authUrls.slice(-3),e.url];}if(e.event==='auth-prompt'){this.prompt={...e,urls:[...this.authUrls]};this.emit('event',this.prompt);}else if(e.event==='log'){this.log(e.message);}else{this.emit('event',e);}});
  }
  log(message) {this.logs=[...this.logs.slice(-199),{time:new Date().toISOString(),message}];this.emit('event',{event:'log',message});}
  state(value) {this.connection={...this.connection,...value};this.emit('event',{event:'connection',connection:this.connection});return this.connection;}
  async command(action,params={},timeout=180000,settings=this.store.settings()) {await this.bridge.start(settings);return this.bridge.request(action,{settings,...params},timeout);}
  async remote(code,timeout=180,settings=this.store.settings()) {return this.command('exec',{code,timeout},(timeout+90)*1000,settings);}
  bootstrap() {return {...this.store.bootstrap(),connection:this.connection,logs:this.logs,prompt:this.prompt,desktop:true,imports:[...this.imports.values()]};}
  async discover() {
    const settings=this.store.settings();this.state({state:'checking',message:'Discovering WSL and active Colab sessions…'});
    try {const distributions=await this.bridge.distributions();if(!distributions.includes(settings.distro)&&distributions.length===1)this.store.saveSettings({distro:distributions[0]});
      const found=await this.command('discover');this.state({state:'discovered',message:'Select a session or connect to create one.',...found,distributions});return {distributions,...found};
    }catch(e){this.state({state:'error',message:e.message});throw e;}
  }
  async connect() {
    if(this.connectionBusy)throw new Error('A connection operation is already running');
    if(this.processing)throw new Error('Wait for the current run before changing the connection');
    this.connectionBusy=true;
    try {let settings=this.store.settings();this.state({state:'connecting',message:'Checking authentication and Colab sessions…'});
      const found=await this.command('discover');
      if(settings.session==='eeg-sleep-studio'&&found.sessions.length){const reuse=found.sessions.find(s=>s.name==='eeg-diagnostics')||found.sessions[0];settings=this.store.saveSettings({session:reuse.name});this.log('Reusing active session '+reuse.name);}
      if(!found.sessions.some(s=>s.name===settings.session)){this.state({message:'Allocating '+settings.accelerator+' runtime…'});await this.command('create',{},660000);}
      this.state({message:'Mounting Google Drive…'});await this.command('mount',{},660000);return await this.probe(settings);
    }catch(e){this.state({state:'error',message:e.message});throw e;}finally{this.connectionBusy=false;}
  }
  async mountDrive() {if(this.processing)throw new Error('Wait for the active run before mounting Drive');await this.command('mount',{},660000);return this.probe();}
  async probe(settings=this.store.settings()) {
    const result=await this.remote(`import json, os, platform, shutil, subprocess\nfrom pathlib import Path\nimport importlib.metadata as md\ns=${py(settings)}\npackages={}\nfor package in ['numpy','tensorflow','keras','mne','matplotlib']:\n try: packages[package]=md.version(package)\n except md.PackageNotFoundError: packages[package]=None\ngpu=''\nif shutil.which('nvidia-smi'):\n r=subprocess.run(['nvidia-smi','--query-gpu=name,memory.total','--format=csv,noheader'],capture_output=True,text=True,timeout=20);gpu=r.stdout.strip()\nchecks={'drive':Path('/content/drive/MyDrive').is_dir(),'checkpoint':Path(s['checkpointPath']).is_file(),'processed':Path(s['processedPath']).is_dir(),'raw':Path(s['rawPath']).is_dir()}\nprint('SLEEP_JSON:'+json.dumps({'checks':checks,'packages':packages,'gpu':gpu or 'CPU runtime','python':platform.python_version(),'session':s['session']}))`,180,settings);
    const missing=Object.entries(result.packages).filter(([,version])=>!version).map(([name])=>name);
    const ready=result.checks.drive&&result.checks.checkpoint&&result.checks.processed&&missing.length===0;
    return this.state({...result,state:ready?'ready':'needs-setup',message:ready?'Connected. Runtime, Drive, checkpoint and packages are ready.':missing.length?'Install missing runtime packages: '+missing.join(', '):'Check the Drive, model and dataset paths below.'});
  }
  async prepareRuntime() {
    if(this.processing||this.connectionBusy)throw new Error('Wait for the current operation before installing runtime packages');
    this.state({state:'checking',message:'Installing missing runtime packages…'});
    try {await this.remote(`import json, sys, subprocess\nimport importlib.metadata as md\nrequired={'numpy':'2.1.3','tensorflow':'2.21.0','keras':'3.13.2','mne':'1.13.2','matplotlib':'3.10.8'}\nmissing=[]\nfor p,v in required.items():\n try:md.version(p)\n except md.PackageNotFoundError:missing.append(p+'=='+v)\nif missing:subprocess.run([sys.executable,'-m','pip','install',*missing],check=True)\nprint('SLEEP_JSON:'+json.dumps({'installed':missing}))`,900);return this.probe();}catch(e){this.state({state:'error',message:e.message});throw e;}
  }
  async browseDrive(folder) {
    folder=remotePath(folder||this.store.settings().processedPath);
    if(!folder.startsWith('/content/drive/MyDrive/')&&folder!=='/content/drive/MyDrive')throw new Error('Browse within MyDrive');
    return this.remote(`import json\nfrom pathlib import Path\np=Path(${JSON.stringify(folder)})\nif not p.is_dir():raise FileNotFoundError('Folder not found: '+str(p))\nitems=[]\nfor f in sorted(p.iterdir(),key=lambda x:(not x.is_dir(),x.name.lower())):\n if f.is_dir() or f.suffix.lower() in ['.edf','.npz','.keras']:\n  items.append({'name':f.name,'path':str(f),'directory':f.is_dir(),'bytes':f.stat().st_size if f.is_file() else 0})\n if len(items)>=500:break\nprint('SLEEP_JSON:'+json.dumps({'folder':str(p),'items':items}))`);
  }
  registerImports(files) {
    const result=[];
    for(const file of files) {
      const id='import-'+crypto.randomUUID();const ext=path.extname(file).toLowerCase();if(!['.npz','.edf'].includes(ext))continue;
      const item={id,name:path.basename(file),path:file,bytes:fs.statSync(file).size,source:'local'};this.imports.set(id,item);result.push(item);
    }
    return result;
  }
  async startRun(options) {
    if(this.connection.state!=='ready')throw new Error('Connect Colab and complete runtime setup before starting a run');
    const valid=validateOptions(options),settings={...this.store.settings(),...valid};
    if(options.checkpointPath)settings.checkpointPath=remotePath(options.checkpointPath);
    const source=options.source||'project';let inputs=[];
    const dataset=this.store.bootstrap().dataset;
    if(valid.kind!=='training') {
      if(source==='project') {
        const ids=options.recordings;
        const all=Object.values(dataset.split_subject_ids||{}).flat();
        if(!Array.isArray(ids)||!ids.length||ids.length>100||ids.some(id=>!all.includes(id)))throw new Error('Choose recordings from the project list');
        inputs=[...new Set(ids)].map(id=>({id,source:'project',path:settings.processedPath+'/'+id+'.npz'}));
        if(valid.kind==='preprocess')inputs=inputs.map(x=>({...x,path:settings.rawPath+'/'+x.id+'.edf',scoringPath:settings.rawPath+'/'+x.id+'_sleepscoring.edf'}));
      } else if(source==='local') {
        const ids=options.importIds;
        if(!Array.isArray(ids)||!ids.length||ids.length>100||ids.some(id=>!this.imports.has(id)))throw new Error('Import files first');
        const chosen=ids.map(id=>this.imports.get(id));
        const scores=chosen.filter(x=>x.name.toLowerCase().includes('_sleepscoring'));
        inputs=chosen.filter(x=>!scores.includes(x)).map((x,i)=>({id:path.parse(x.name).name.replace(/[^A-Za-z0-9_-]/g,'_')+'_'+(i+1),source:'local',localPath:x.path,scoringLocal:scores.find(s=>s.name.toLowerCase()===path.parse(x.name).name.toLowerCase()+'_sleepscoring.edf')?.path}));
        if(!inputs.length)throw new Error('Select a signal recording with its optional matching scoring file');
      } else if(source==='drive') {
        if(!Array.isArray(options.driveFiles)||!options.driveFiles.length||options.driveFiles.length>100)throw new Error('Select files from Drive');
        const chosen=options.driveFiles.map(remotePath);
        const scores=chosen.filter(x=>path.posix.basename(x).includes('_sleepscoring'));
        inputs=chosen.filter(x=>!scores.includes(x)).map((x,i)=>({id:path.posix.parse(x).name.replace(/[^A-Za-z0-9_-]/g,'_')+'_'+(i+1),source:'drive',path:x,scoringPath:scores.find(s=>s===x.replace(/\.edf$/i,'_sleepscoring.edf'))}));
        if(inputs.some(x=>!['.edf','.npz'].includes(path.posix.extname(x.path).toLowerCase())))throw new Error('Choose EDF or NPZ recordings, rather than checkpoints');
      } else throw new Error('Invalid data source');
    }
    const split=valid.kind==='training'?(options.split||dataset.split_subject_ids):null;
    if(split) {
      const values=['train','val','test'].map(key=>split[key]);const all=Object.values(dataset.split_subject_ids).flat();
      if(values.some(v=>!Array.isArray(v))||!split.train.length||!split.val.length||values.flat().some(id=>!all.includes(id))||new Set(values.flat()).size!==values.flat().length)throw new Error('Choose valid nonoverlapping training, validation and test recordings');
    }
    settings.testIds=dataset.split_subject_ids?.test||[];
    const transition=this.store.bootstrap().transition;const matrix=this.store.read(this.store.baseline,'transition_matrix.csv',[]).map(row=>['Wake','N1','N2','N3','REM'].map(n=>row[n]));
    const id='run-'+new Date().toISOString().replace(/[-:.TZ]/g,'')+'-'+crypto.randomBytes(3).toString('hex');
    const trained=this.store.runs().find(run=>run.kind==='training'&&run.status==='completed'&&run.result?.checkpoint===settings.checkpointPath);
    const selectedTransition=trained?this.store.read(this.store.directory(trained.id),'transition_config.json',null):{...transition,matrix};
    if(!selectedTransition||!selectedTransition.matrix)throw new Error('The selected checkpoint has no verified training transition priors');
    const config={id,kind:valid.kind,settings,inputs,transition:selectedTransition,split};
    const manifest={id,name:options.name?.slice(0,100)|| (valid.kind==='training'?'Fast SCFormer-U training':valid.kind==='preprocess'?'EDF preprocessing':'Sleep analysis · '+inputs.map(i=>i.id).join(', ')),kind:valid.kind,status:'queued',createdAt:new Date().toISOString(),settings,recordings:inputs.map(i=>i.id),step:'Queued',progress:0};
    this.store.saveRun(manifest);atomicJson(path.join(this.store.runsRoot,id,'config.json'),config);this.queue.push(id);this.emit('event',{event:'run',run:manifest});this.processQueue();return manifest;
  }
  async processQueue() {
    if(this.processing||!this.queue.length||this.connection.state!=='ready')return;
    this.processing=true;const id=this.queue.shift();
    try {await this.execute(id);} catch(e) {const run=this.store.manifest(id);this.update(id,{status:run.remotePid?'interrupted':'failed',error:e.message,step:run.remotePid?'Connection interrupted · Recover available':'Failed'});if(run.remotePid)this.state({state:'error',message:'A run lost its connection. Recover it before starting another computation.'});}
    finally {this.processing=false;this.processQueue();}
  }
  update(id,value) {const run={...this.store.manifest(id),...value,updatedAt:new Date().toISOString()};this.store.saveRun(run);this.emit('event',{event:'run',run});return run;}
  async execute(id) {
    const folder=path.join(this.store.runsRoot,id),config=this.store.json(path.join(folder,'config.json')),settings=config.settings;
    this.update(id,{status:'preparing',step:'Preparing isolated worker',progress:1});
    const remoteRoot='/content/eeg_sleep_studio/'+id;
    await this.remote(`import json\nfrom pathlib import Path\np=Path(${JSON.stringify(remoteRoot)});p.mkdir(parents=True,exist_ok=True)\nprint('SLEEP_JSON:'+json.dumps({'ok':True}))`,180,settings);
    for(const filename of ['core.py','worker.py']) {
      const local=await this.bridge.linuxPath(path.join(this.bridge.guiRoot,'pipeline',filename),settings.distro);
      await this.command('upload',{local,remote:remoteRoot+'/'+filename},960000,settings);
    }
    for(const item of config.inputs) {
      if(item.source==='local') {
        this.update(id,{step:'Uploading '+path.basename(item.localPath)});
        const local=await this.bridge.linuxPath(item.localPath,settings.distro);item.path=remoteRoot+'/'+item.id+path.extname(item.localPath).toLowerCase();await this.command('upload',{local,remote:item.path},960000,settings);
        if(item.scoringLocal){const scoringLocal=await this.bridge.linuxPath(item.scoringLocal,settings.distro);item.scoringPath=remoteRoot+'/'+item.id+'_sleepscoring.edf';await this.command('upload',{local:scoringLocal,remote:item.scoringPath},960000,settings);}
      }
      delete item.localPath;delete item.scoringLocal;
    }
    const remoteConfig=remoteRoot+'/config.json';const localConfig=path.join(folder,'remote-config.json');atomicJson(localConfig,config);
    await this.command('upload',{local:await this.bridge.linuxPath(localConfig,settings.distro),remote:remoteConfig},960000,settings);
    const launched=await this.remote(`import json, subprocess, sys\nfrom pathlib import Path\np=Path(${JSON.stringify(remoteRoot)})\nwith (p/'worker.log').open('w') as log:\n process=subprocess.Popen([sys.executable,str(p/'worker.py'),str(p/'config.json')],stdout=log,stderr=log,start_new_session=True)\n(p/'pid').write_text(str(process.pid))\nprint('SLEEP_JSON:'+json.dumps({'pid':process.pid}))`,180,settings);
    this.update(id,{status:'running',remotePid:launched.pid,remoteRoot,step:'Worker started',progress:3});
    await this.monitor(id,settings);
  }
  async monitor(id,settings) {
    let failures=0,missing=0;
    while(true) {
      const run=this.store.manifest(id);
      try {
        const value=await this.remote(`import json, os\nfrom pathlib import Path\np=Path(${JSON.stringify(run.remoteRoot)})\nf=p/'status.json'\nvalue=json.loads(f.read_text()) if f.exists() else {'status':'starting'}\nif not f.exists():\n bundle=Path(${JSON.stringify(settings.driveOutputs+'/'+id+'/results.zip')})\n if bundle.is_file():\n  import zipfile\n  with zipfile.ZipFile(bundle) as z:value=json.loads(z.read('worker_status.json'))\n  value['bundle']=str(bundle)\npid=${Number(run.remotePid)}\ncmd=Path('/proc')/str(pid)/'cmdline'\nvalue['alive']=cmd.is_file() and str(p/'worker.py') in cmd.read_bytes().decode(errors='replace')\nprint('SLEEP_JSON:'+json.dumps(value))`,60,settings);
        failures=0;
        if(!value.alive&&!['completed','failed','cancelled'].includes(value.status)) {
          if(++missing>=3){this.update(id,{status:'interrupted',step:'Worker stopped without a final status',error:'Worker exited without a complete status. Runtime files may have been lost.'});this.state({state:'error',message:'A worker stopped unexpectedly. Inspect or recover it in Run history.'});return;}
        }else missing=0;
        this.update(id,{step:value.step||'Starting worker',progress:value.progress||3,epochMetrics:value.epochMetrics});
        if(['completed','failed','cancelled'].includes(value.status)) {
          this.update(id,{status:'downloading',step:'Downloading results',progress:97,error:value.error,driveBundle:value.driveBundle,transferError:value.transferError});
          if(value.bundle) {
            const archive=path.join(this.store.runsRoot,id,'results.zip'),destination=this.store.directory(id);
            await this.command('download',{remote:value.bundle,local:await this.bridge.linuxPath(archive,settings.distro)},960000,settings);
            await this.command('unpack',{archive:await this.bridge.linuxPath(archive,settings.distro),destination:await this.bridge.linuxPath(destination,settings.distro)},180000,settings);
          }
          this.update(id,{status:value.status,step:value.status==='completed'?'Analysis complete':value.status==='cancelled'?'Cancelled':'Failed',progress:value.status==='completed'?100:value.progress||0,finishedAt:value.finishedAt,result:value.result,error:value.error});return;
        }
      }catch(e){if(++failures>=3)throw e;this.log('Retrying runtime status: '+e.message);}
      await new Promise(resolve=>{const timer=setTimeout(()=>{this.timers.delete(timer);resolve();},3500);this.timers.add(timer);});
    }
  }
  async cancelRun(id) {
    const run=this.store.manifest(id);if(!run)throw new Error('Run not found');
    if(run.status==='queued'){this.queue=this.queue.filter(x=>x!==id);return this.update(id,{status:'cancelled',step:'Cancelled before execution'});}
    if(!run.remotePid||!run.remoteRoot)throw new Error('The worker is still preparing. Wait for it to start before cancelling.');
    const result=await this.remote(`import json, os, signal\nfrom pathlib import Path\np=Path(${JSON.stringify(run.remoteRoot)})\npid=${Number(run.remotePid)}\ncommand=Path('/proc')/str(pid)/'cmdline'\nif command.exists():\n text=command.read_bytes().decode(errors='replace')\n if str(p/'worker.py') not in text or str(p/'config.json') not in text:raise RuntimeError('Worker identity differs; cancellation was refused')\n os.killpg(pid,signal.SIGTERM)\nprint('SLEEP_JSON:'+json.dumps({'requested':True}))`,60,run.settings);
    this.update(id,{step:'Cancellation requested · waiting for worker acknowledgement'});return result;
  }
  async recoverRun(id) {
    if(this.processing)throw new Error('Wait for the current run before recovering another');
    const run=this.store.manifest(id);if(!run||!run.remoteRoot)throw new Error('This run has no recoverable remote worker');
    this.processing=true;this.update(id,{status:'running',step:'Recovering runtime status'});
    this.monitor(id,run.settings).catch(e=>this.update(id,{status:'interrupted',step:'Recovery interrupted',error:e.message})).finally(()=>{this.processing=false;this.processQueue();});return this.store.manifest(id);
  }
  async authReply(value) {if(!this.prompt)throw new Error('No active authorization prompt');await this.bridge.request('auth-reply',{requestId:this.prompt.requestId,value},20000);this.prompt=null;this.emit('event',{event:'auth-dismiss'});return {ok:true};}
  async signal(id,recording,epoch) {
    const run=this.store.manifest(id);if(id==='baseline') {
      const value=this.store.bootstrap().exampleSignal;if(recording==='SN009'&&Number(epoch)===10)return value;
      if(this.connection.state!=='ready')return null;
      const index=Number(epoch);if(!Number.isInteger(index)||index<0||!['SN009','SN001','SN004','SN022'].includes(recording))throw new Error('Invalid baseline recording or epoch');
      const settings=this.store.settings();
      return this.remote(`import json, numpy as np\nfrom pathlib import Path\np=Path(${JSON.stringify(settings.processedPath+'/'+recording+'.npz')})\nif ${JSON.stringify(recording)}=='SN001':raise ValueError('SN001 uses the verified correction. Start a new project analysis to inspect its full EEG.')\nwith np.load(p,allow_pickle=False) as d:x=d['X'][${index}]\nprint('SLEEP_JSON:'+json.dumps({'channels':['EEG F4-M1','EEG C4-M1','EEG O2-M1','EEG C3-M2'],'recording_id':${JSON.stringify(recording)},'epoch_index':${index},'processed':x[:,::3].tolist(),'processed_sampling_hz':100/3,'processed_unit':'normalized amplitude'}))`,120,settings);
    }
    if(!run?.remoteRoot)return null;
    const input=this.store.read(this.store.directory(id),'run_config.json',{}).inputs?.find(x=>x.id===recording);
    if(!input)return null;
    const index=Number(epoch);if(!Number.isInteger(index)||index<0)throw new Error('Invalid epoch');
    return this.remote(`import json, numpy as np\nfrom pathlib import Path\nsid=${JSON.stringify(recording)}\np=Path(${JSON.stringify(run.remoteRoot)})\nfile=p/'artifacts'/(sid+'_corrected.npz')\nif not file.exists():file=Path(${JSON.stringify(input.path)})\nif file.suffix.lower()!='.npz':raise ValueError('Only the first EDF epoch preview is cached; use the exported EDF to inspect other epochs')\nwith np.load(file,allow_pickle=False) as d:\n x=d['X'][${index}]\nprint('SLEEP_JSON:'+json.dumps({'channels':['EEG F4-M1','EEG C4-M1','EEG O2-M1','EEG C3-M2'],'recording_id':sid,'epoch_index':${index},'processed':x[:,::3].tolist(),'processed_sampling_hz':100/3,'processed_unit':'normalized amplitude'}))`,120,run.settings);
  }
  close() {for(const t of this.timers)clearTimeout(t);this.bridge.close();}
}
module.exports={Service,validateOptions,remotePath,py,ACTIVE};
