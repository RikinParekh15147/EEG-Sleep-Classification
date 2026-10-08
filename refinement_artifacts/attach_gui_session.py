from pathlib import Path
from colab_cli.common import state
from colab_cli.state import SessionState
state.config_path='/tmp/eeg-colab-checks/sessions.json'
_,assignments=state.sync_sessions()
if len(assignments)!=1:raise RuntimeError('Expected one audit runtime')
a=assignments[0];info=a.runtime_proxy_info
config=Path.home()/'.local/share/eeg-sleep-studio/sessions.json'
config.parent.mkdir(parents=True,exist_ok=True)
state.config_path=str(config)
state._store=None
state.store.add(SessionState(name='eeg-refinement-audit',token=info.token,url=info.url,endpoint=a.endpoint,token_expires_at=info.expires_at(),accelerator=a.accelerator,variant='DEFAULT'))
config.chmod(0o600)
print('Attached the existing audit runtime to the GUI session store.')
