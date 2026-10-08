// Read the desktop settings and verify its existing runtime without allocating one.
const path=require('node:path');
const {Store}=require('../electron/store.cjs');
const {Bridge}=require('../electron/bridge.cjs');
const {Service}=require('../electron/service.cjs');
const gui=path.resolve(__dirname,'..');
const profile=process.env.SLEEP_DATA_DIR||path.join(process.env.APPDATA,'Sleep Studio');
const store=new Store(path.dirname(gui),profile);
const sessionIndex=process.argv.indexOf('--session');
if(sessionIndex!==-1){const requested=process.argv[sessionIndex+1];if(!requested||!/^[A-Za-z0-9_-]{1,100}$/.test(requested))throw new Error('Provide a valid session name');const saved=store.settings();store.settings=()=>({...saved,session:requested});}
const bridge=new Bridge(gui);
const service=new Service(store,bridge);
(async()=>{
  try {
    const found=await service.command('discover');
    if(!found.sessions.some(session=>session.name===store.settings().session))throw new Error('The configured runtime '+store.settings().session+' is inactive. Available sessions: '+(found.sessions.map(session=>session.name).join(', ')||'none')+'. Connect through the desktop app to choose a runtime.');
    const result=await service.connect();
    console.log(JSON.stringify({state:result.state,message:result.message,session:result.session,gpu:result.gpu,checks:result.checks,packages:result.packages},null,2));
    if(result.state!=='ready')process.exitCode=1;
  }finally{service.close();}
})().catch(error=>{console.error(error.message);process.exitCode=1;});
