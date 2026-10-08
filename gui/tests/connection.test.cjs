const {test}=require('node:test');
const assert=require('node:assert/strict');
const {EventEmitter}=require('node:events');
const {Service}=require('../electron/service.cjs');
const {Bridge}=require('../electron/bridge.cjs');

function fixture({missing=false,installError=false}={}) {
  const bridge=new EventEmitter();
  const calls=[];
  const settings={distro:'Ubuntu',session:'existing-t4'};
  let installed=!missing;
  bridge.start=async()=>{};
  bridge.distributions=async()=>['Ubuntu'];
  bridge.close=reason=>{calls.push({action:'close',reason});};
  bridge.request=async(action,params)=>{
    calls.push({action,code:params?.code});
    if(action==='discover')return {sessions:[{name:settings.session}]};
    if(action==='mount')return {ok:true};
    if(action==='create')throw new Error('Must reuse the active runtime');
    if(action==='exec'&&params.code.includes('required=')){
      if(installError)throw new Error('pip install failed');
      installed=true;return {installed:['mne==1.13.2']};
    }
    if(action==='exec')return {checks:{drive:true,checkpoint:true,processed:true,raw:true},packages:{numpy:'2.1.3',mne:installed?'1.13.2':null},gpu:'Tesla T4',session:settings.session};
    throw new Error('Unexpected command '+action);
  };
  const service=new Service({settings:()=>settings},bridge);
  return {service,bridge,calls};
}

test('connect reuses the runtime and installs missing MNE before becoming ready',async()=>{
  const {service,calls}=fixture({missing:true});
  const states=[];service.on('event',event=>{if(event.event==='connection')states.push(event.connection.state);});
  try {
    const result=await service.connect();
    assert.equal(result.state,'ready');assert.equal(result.packages.mne,'1.13.2');
    assert.equal(calls.filter(c=>c.action==='exec').length,3);
    assert.equal(calls.filter(c=>c.code?.includes('required=')).length,1);
    assert.ok(states.includes('needs-setup'));assert.ok(states.includes('checking'));
    assert.equal(states.filter(s=>s==='ready').length,1);
    assert.equal(service.connectionBusy,false);
  }finally{service.close();}
});

test('connect retains installed packages without invoking pip',async()=>{
  const {service,calls}=fixture();
  try {assert.equal((await service.connect()).state,'ready');assert.equal(calls.filter(c=>c.action==='exec').length,1);assert.ok(!calls.some(c=>c.code?.includes('pip')));}
  finally{service.close();}
});

test('a failed package installation reports the error and releases connection controls',async()=>{
  const {service}=fixture({missing:true,installError:true});
  try {await assert.rejects(service.connect(),/pip install failed/);assert.equal(service.connection.state,'error');assert.equal(service.connectionBusy,false);}
  finally{service.close();}
});

test('closing during connection cancels pending work without emitting an error state',async()=>{
  const {service,bridge}=fixture();
  let rejectRequest,started;
  const waiting=new Promise(resolve=>{started=resolve;});
  bridge.request=()=>new Promise((resolve,reject)=>{rejectRequest=reject;started();});
  bridge.close=reason=>rejectRequest(new Error(reason));
  const states=[];service.on('event',event=>{if(event.event==='connection')states.push(event.connection.state);});
  const connecting=service.connect();await waiting;service.close();await connecting;
  assert.equal(service.closed,true);assert.equal(service.connectionBusy,false);assert.ok(!states.includes('error'));
  await assert.rejects(service.command('discover'),/Application closed/);
});

test('connection operations cannot compete with an active connect',async()=>{
  const {service,bridge}=fixture();
  let release,started;
  const waiting=new Promise(resolve=>{started=resolve;});
  const request=bridge.request;
  bridge.request=async(action,params)=>{
    if(action==='discover'){started();await new Promise(resolve=>{release=resolve;});}
    return request(action,params);
  };
  const connecting=service.connect();await waiting;
  await assert.rejects(service.discover(),/already running/);
  await assert.rejects(service.mountDrive(),/current operation/);
  await assert.rejects(service.prepareRuntime(),/current operation/);
  release();await connecting;service.close();
});

test('simultaneous bridge callers share startup instead of reconfiguring each other',async()=>{
  const bridge=new Bridge(__dirname);let opens=0,release;
  bridge.open=()=>{opens++;return new Promise(resolve=>{release=resolve;});};
  const first=bridge.start({distro:'Ubuntu'}),second=bridge.start({distro:'Ubuntu'});
  assert.equal(first,second);assert.equal(opens,1);release();await Promise.all([first,second]);bridge.close();
});

test('closing while resolving a WSL path prevents a late bridge process from starting',async()=>{
  const bridge=new Bridge(__dirname);let release;
  bridge.linuxPath=()=>new Promise(resolve=>{release=resolve;});
  const opening=bridge.start({distro:'Ubuntu'});bridge.close('Application closed.');release('/tmp/host.py');
  await assert.rejects(opening,/cancelled/);assert.equal(bridge.child,null);
});
