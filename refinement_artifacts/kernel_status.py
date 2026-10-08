"""Read kernel state, optionally interrupt only this audit's own execution."""
import json,sys,requests
from colab_cli.common import state
state.config_path='/tmp/eeg-colab-checks/sessions.json'
s=state.get_session('eeg-refinement-audit')
headers={'X-Colab-Runtime-Proxy-Token':s.token,'X-Colab-Client-Agent':'colab-cli'}
response=requests.get(s.url+'/api/kernels/'+s.kernel_id,headers=headers,params={'colab-runtime-proxy-token':s.token},timeout=30)
response.raise_for_status();v=response.json()
print(json.dumps({k:v.get(k) for k in ['id','execution_state','last_activity','connections']}))
if '--interrupt' in sys.argv:
    if not s.running or 'reproduce.py' not in s.running:raise RuntimeError('This audit is not the active execution; refused interrupt')
    r=requests.post(s.url+'/api/kernels/'+s.kernel_id+'/interrupt',headers=headers,params={'colab-runtime-proxy-token':s.token},timeout=30)
    r.raise_for_status();print('Interrupted only the audit execution; kernel was not restarted.')
