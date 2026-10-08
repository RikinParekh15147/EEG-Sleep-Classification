const { spawn, execFile } = require('node:child_process');
const path = require('node:path');
const { EventEmitter } = require('node:events');
const { promisify } = require('node:util');
const exec = promisify(execFile);
class Bridge extends EventEmitter {
  constructor(guiRoot) { super(); this.guiRoot=guiRoot; this.pending=new Map(); this.sequence=0; this.child=null; this.distro=null; this.starting=null; this.generation=0; }
  async distributions() {
    if (process.platform !== 'win32') return [process.env.WSL_DISTRO_NAME || 'Linux'];
    const {stdout}=await exec('wsl.exe',['--list','--quiet'],{encoding:'utf16le',windowsHide:true,timeout:20000});
    return stdout.replace(/\0/g,'').split(/[\r\n]+/).map(x=>x.trim()).filter(Boolean);
  }
  async linuxPath(file,distro) {
    if (process.platform !== 'win32') return path.resolve(file);
    const {stdout}=await exec('wsl.exe',['--distribution',distro,'--exec','wslpath','-u',path.resolve(file)],{windowsHide:true,timeout:20000});
    return stdout.trim();
  }
  start(settings) {
    if(this.starting){
      if(this.startingDistro===settings.distro)return this.starting;
      return this.starting.catch(()=>{}).then(()=>this.start(settings));
    }
    if(this.child && this.distro===settings.distro)return Promise.resolve();
    this.startingDistro=settings.distro;
    const opening=this.open(settings);
    const pending=opening.finally(()=>{if(this.starting===pending)this.starting=null;});
    this.starting=pending;return pending;
  }
  async open(settings) {
    this.close();
    const generation=this.generation;
    const file=await this.linuxPath(path.join(this.guiRoot,'bridge/host.py'),settings.distro);
    if(generation!==this.generation)throw new Error('Bridge connection cancelled.');
    const command=process.platform==='win32' ? 'wsl.exe' : 'python3';
    const args=process.platform==='win32' ? ['--distribution',settings.distro,'--exec','python3','-u',file] : ['-u',file];
    this.child=spawn(command,args,{stdio:['pipe','pipe','pipe'],windowsHide:true}); this.distro=settings.distro;
    let buffer='';
    this.child.stdout.setEncoding('utf8'); this.child.stdout.on('data',chunk=>{
      buffer+=chunk;
      let end; while((end=buffer.indexOf('\n'))>=0) {
        const line=buffer.slice(0,end);buffer=buffer.slice(end+1);
        try { const message=JSON.parse(line); if(message.event) this.emit('event',message);
          else { const pending=this.pending.get(message.id); if(pending) { this.pending.delete(message.id); clearTimeout(pending.timer); message.error ? pending.reject(new Error(message.error)) : pending.resolve(message.result); } }
        } catch(e) { this.emit('event',{event:'log',message:'Bridge output could not be decoded.'}); }
      }
      if(buffer.length>8*1024*1024) { this.emit('event',{event:'log',message:'Bridge output exceeded limit.'}); this.close(); }
    });
    this.child.stderr.setEncoding('utf8');this.child.stderr.on('data',()=>this.emit('event',{event:'log',message:'WSL bridge reported an error. Check connection diagnostics.'}));
    const current=this.child;current.on('error',e=>{if(this.child===current)this.fail(e);});current.on('exit',()=>{if(this.child===current){this.child=null;this.fail(new Error('WSL bridge closed. Reconnect to continue.'));}});
    await this.request('hello',{},20000);
  }
  fail(error) { for(const item of this.pending.values()) {clearTimeout(item.timer);item.reject(error);}this.pending.clear(); }
  request(action,params={},timeout=180000) {
    if(!this.child?.stdin.writable) return Promise.reject(new Error('Connect to WSL first.'));
    const id=String(++this.sequence);
    return new Promise((resolve,reject)=>{const timer=setTimeout(()=>{this.pending.delete(id);reject(new Error(`${action} timed out. The runtime may still be active; reconnect before retrying.`));},timeout);this.pending.set(id,{resolve,reject,timer});this.child.stdin.write(JSON.stringify({id,action,params})+'\n');});
  }
  close(reason='Bridge reconfigured.') { this.generation++; const old=this.child;this.child=null;old?.stdin.end();this.fail(new Error(reason)); }
}
module.exports={Bridge};
