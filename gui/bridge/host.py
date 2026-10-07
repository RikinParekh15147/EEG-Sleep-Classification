"""JSON-lines bridge. Credentials stay in Linux; CLI prompts run in a PTY."""
import argparse
import codecs
import json
import os
import pty
import re
import select
import shutil
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

WRITE_LOCK = threading.Lock()
COMMAND_LOCK = threading.Lock()
PROMPTS = {}
CONFIG_DIR = Path.home() / '.local/share/eeg-sleep-studio'

def send(value):
    with WRITE_LOCK:
        print(json.dumps(value, allow_nan=False), flush=True)

def clean(text):
    text = re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]', '', text)
    text = re.sub(r'(?:Bearer\s+)[A-Za-z0-9._~-]+', 'Bearer [redacted]', text, flags=re.I)
    text = re.sub(r'((?:access_token|refresh_token|authorization_code|id_token)[\s"\x27:=]+)[^\s,"\x27}]+', r'\1[redacted]', text, flags=re.I)
    return text

def cli_path(settings):
    requested = settings.get('cliPath', '').strip()
    choices = [requested] if requested else [shutil.which('colab'), str(Path.home()/'.venvs/colab-cli/bin/colab'), str(Path.home()/'.local/bin/colab')]
    for candidate in choices:
        if candidate and Path(candidate).is_file() and os.access(candidate, os.X_OK):
            return candidate
    raise RuntimeError('Colab CLI was not found in this WSL distribution. Set its executable path in Connection settings.')

def initialize_config():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
    target = CONFIG_DIR/'sessions.json'
    if not target.exists():
        for old in [Path('/tmp/eeg-colab-checks/sessions.json'), Path.home()/'.config/colab-cli/sessions.json']:
            if old.is_file():
                try:
                    data=json.loads(old.read_text())
                    target.write_text(json.dumps(data));target.chmod(0o600);break
                except (OSError,ValueError):
                    pass
    return target

def cli(settings, args, request_id, timeout=600):
    executable=cli_path(settings);config=initialize_config()
    command=[executable,'--auth','oauth2','--config',str(config),'--logtostderr',*args]
    with COMMAND_LOCK:
        master,slave=pty.openpty()
        def terminal():
            os.setsid()
            import fcntl, termios
            fcntl.ioctl(0,termios.TIOCSCTTY,0)
        process=subprocess.Popen(command,stdin=slave,stdout=slave,stderr=slave,preexec_fn=terminal,close_fds=True)
        os.close(slave)
        PROMPTS[request_id]=(master,process)
        decoder=codecs.getincrementaldecoder('utf-8')('replace')
        output='';line_buffer='';seen_urls=set();asked_code=False;asked_enter=False
        start=time.monotonic()
        try:
            while True:
                if time.monotonic()-start>timeout:
                    os.killpg(process.pid,signal.SIGTERM)
                    raise TimeoutError('Colab command timed out. Reconnect to verify the remote operation before retrying.')
                ready,_,_=select.select([master],[],[],0.2)
                if ready:
                    try: chunk=os.read(master,65536)
                    except OSError: chunk=b''
                    if not chunk:
                        if process.poll() is not None: break
                        continue
                    text=clean(decoder.decode(chunk));output+=text;line_buffer+=text
                    # Never echo authorization codes written back through the PTY.
                    for url in re.findall(r'https://[^\s<>"\x27]+',text):
                        url=url.rstrip(').,')
                        if any(host in url for host in ['accounts.google.com/','colab.research.google.com/','sdk.cloud.google.com/']):
                            if url not in seen_urls:
                                seen_urls.add(url);send({'event':'auth-url','requestId':request_id,'url':url})
                    if 'Enter the authorization code:' in output and not asked_code:
                        asked_code=True;send({'event':'auth-prompt','requestId':request_id,'kind':'code','message':'Sign in in your browser, then paste the authorization code.'})
                    if 'Press Enter after you have granted access' in output and not asked_enter:
                        asked_enter=True;send({'event':'auth-prompt','requestId':request_id,'kind':'continue','message':'Grant Google Drive access in your browser, then click Continue.'})
                    while '\n' in line_buffer:
                        line,line_buffer=line_buffer.split('\n',1)
                        # Auth URLs contain state and codes: only the separate auth event sees them.
                        if not any(x in line.lower() for x in ['https://','authorization code','token','credentials','oauth','debug:','debug ']):
                            if line.strip():send({'event':'log','requestId':request_id,'message':line.strip()[:2000]})
                    if len(output)>4*1024*1024:output=output[-2*1024*1024:]
                elif process.poll() is not None:break
            code=process.wait(timeout=5)
            if code != 0:
                safe_lines=[line.strip() for line in clean(output).splitlines() if line.strip() and not any(x in line.lower() for x in ['token','https://','authorization code','oauth','credentials'])]
                raise RuntimeError('Colab command failed: '+'\n'.join(safe_lines[-5:])[:2000])
            return output
        finally:
            PROMPTS.pop(request_id,None);os.close(master)
            if process.poll() is None:
                os.killpg(process.pid,signal.SIGTERM)

def sessions():
    target=initialize_config()
    if not target.exists():return []
    data=json.loads(target.read_text())
    # The CLI stores either a sessions mapping or a direct mapping, depending on version.
    values=data.get('sessions',data) if isinstance(data,dict) else {}
    if isinstance(values,list):return [{'name':x.get('name'),'accelerator':x.get('accelerator',''),'variant':x.get('variant','')} for x in values if isinstance(x,dict) and x.get('name')]
    if isinstance(values,dict):return [{'name':x.get('name',key),'accelerator':x.get('accelerator',''),'variant':x.get('variant','')} for key,x in values.items() if isinstance(x,dict) and ('endpoint' in x or 'name' in x)]
    return []

def marker(output):
    found=re.findall(r'SLEEP_JSON:(\{[^\r\n]+\}|\[[^\r\n]*\])',output)
    if not found:raise RuntimeError('Runtime returned no structured response. Check the connection log.')
    return json.loads(found[-1])

def exec_code(settings, code, rid, timeout=180):
    folder=CONFIG_DIR/'scripts';folder.mkdir(exist_ok=True)
    file=folder/f'{rid}_{time.time_ns()}.py';file.write_text(code,encoding='utf8')
    try:return cli(settings,['exec','-s',settings['session'],'-f',str(file),'--timeout',str(timeout)],rid,timeout+60)
    finally:file.unlink(missing_ok=True)

def handle(request):
    rid=request['id'];action=request['action'];p=request.get('params',{});settings=p.get('settings',{})
    try:
        if action=='hello':result={'platform':sys.platform,'python':sys.version.split()[0]}
        elif action=='auth-reply':
            target=str(p['requestId']);entry=PROMPTS.get(target)
            if not entry:raise RuntimeError('The authorization prompt has expired. Retry connecting.')
            value=p.get('value','')
            if not isinstance(value,str) or '\n' in value or '\r' in value or len(value)>4096:raise ValueError('Invalid authorization response')
            import termios
            attrs=termios.tcgetattr(entry[0]);attrs[3]&=~termios.ECHO;termios.tcsetattr(entry[0],termios.TCSANOW,attrs)
            os.write(entry[0],(value+'\n').encode());result={'ok':True}
        elif action=='discover':
            cli(settings,['sessions'],rid);result={'cliPath':cli_path(settings),'sessions':sessions()}
        elif action=='create':
            args=['new','-s',settings['session']]
            if settings.get('accelerator','CPU')!='CPU':args+=['--gpu',settings['accelerator']]
            cli(settings,args,rid);result={'sessions':sessions()}
        elif action=='mount':
            cli(settings,['drivemount','-s',settings['session']],rid);result={'ok':True}
        elif action=='exec':result=marker(exec_code(settings,p['code'],rid,p.get('timeout',180)))
        elif action=='upload':
            cli(settings,['upload','-s',settings['session'],p['local'],p['remote'].lstrip('/')],rid,900);result={'ok':True}
        elif action=='download':
            cli(settings,['download','-s',settings['session'],p['remote'].lstrip('/'),p['local']],rid,900);result={'ok':True}
        elif action=='unpack':
            import zipfile
            archive=Path(p['archive']);destination=Path(p['destination']).resolve();destination.mkdir(parents=True,exist_ok=True)
            with zipfile.ZipFile(archive) as z:
                if sum(info.file_size for info in z.infolist())>2*1024**3:raise ValueError('Result archive exceeds 2 GB extraction limit')
                for info in z.infolist():
                    file=(destination/info.filename).resolve()
                    if not file.is_relative_to(destination) or (info.external_attr>>16)&0o170000==0o120000:raise ValueError('Unsafe result archive')
                z.extractall(destination)
            result={'ok':True}
        elif action=='pack':
            import zipfile
            folder=Path(p['folder']).resolve();target=Path(p['target']).resolve()
            with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
                for file in folder.rglob('*'):
                    if file.is_file() and not file.is_symlink() and file.resolve()!=target:
                        z.write(file,str(file.relative_to(folder)))
            result={'ok':True}
        else:raise ValueError('Unknown bridge action')
        send({'id':rid,'result':result})
    except Exception as e:
        send({'id':rid,'error':clean(str(e))[:3000]})

if __name__=='__main__':
    for line in sys.stdin:
        try:
            request=json.loads(line)
            threading.Thread(target=handle,args=(request,),daemon=True).start()
        except (ValueError,KeyError):send({'event':'log','message':'Invalid bridge request'})
    for fd,proc in list(PROMPTS.values()):
        try:os.killpg(proc.pid,signal.SIGTERM)
        except ProcessLookupError:pass
