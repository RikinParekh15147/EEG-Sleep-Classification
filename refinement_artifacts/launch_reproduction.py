"""Start the audit as a detached process so CLI stream loss cannot cancel it."""
import json, subprocess, sys
from pathlib import Path
p=Path('/content/eeg_refinement_recovery');p.mkdir(exist_ok=True)
script=p/'reproduce.py'
if not script.is_file():raise FileNotFoundError('Upload the reproduction script first')
with (p/'audit.log').open('w') as log:
    process=subprocess.Popen([sys.executable,'-u',str(script)],stdout=log,stderr=log,start_new_session=True)
(p/'pid').write_text(str(process.pid))
print(json.dumps({'pid':process.pid,'log':str(p/'audit.log')}))
