from pathlib import Path
import json
d=Path('/content/eeg_refinement_audit')
p=d/'final_results.json'
if p.exists():
    v=json.loads(p.read_text())
    print(json.dumps({'modified':p.stat().st_mtime,'raw':v['raw_metrics'],'refined':v['refined_metrics'],'changes':v['changes']}))
print('ZIP',Path('/content/eeg_refinement_audit.zip').stat().st_mtime)
print('AUDIT_GLOBALS',{k:type(globals().get(k)).__name__ for k in ['model','tables','sid','x','x_normalized','train','ref']})
