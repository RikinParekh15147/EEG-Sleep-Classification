"""Attach a local CLI name to an already allocated runtime; never allocate."""
from colab_cli.common import state
from colab_cli.state import SessionState
state.config_path = '/tmp/eeg-colab-checks/sessions.json'
_, assignments = state.sync_sessions()
if len(assignments) != 1:
    raise RuntimeError('Expected exactly one existing runtime; found '+str(len(assignments)))
a = assignments[0]
info = a.runtime_proxy_info
state.store.add(SessionState(name='eeg-refinement-audit', token=info.token, url=info.url,
    endpoint=a.endpoint, token_expires_at=info.expires_at(), accelerator=a.accelerator,
    variant='DEFAULT'))
print('Attached eeg-refinement-audit to the existing runtime. No runtime allocated.')
