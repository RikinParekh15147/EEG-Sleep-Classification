import json,os
from pathlib import Path
p=Path('/content/eeg_refinement_recovery');log=p/'audit.log'
lines=log.read_text(errors='replace').splitlines() if log.exists() else []
print('\n'.join(lines[-8:]))
done=Path('/content/eeg_refinement_audit.zip')
print(json.dumps({'bundle_exists':done.exists(),'bundle_bytes':done.stat().st_size if done.exists() else None,'alive':Path('/proc/'+(p/'pid').read_text().strip()).exists() if (p/'pid').exists() else False}))
