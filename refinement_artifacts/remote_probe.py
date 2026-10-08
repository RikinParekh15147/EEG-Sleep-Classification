from pathlib import Path
import json, importlib.util
roots=[Path('/content/drive/MyDrive/Sleep_Health_Profiling'),Path('/content/gdrive/MyDrive/Sleep_Health_Profiling')]
print('AUDIT:'+json.dumps({'roots':{str(p):p.exists() for p in roots},'packages':{m:bool(importlib.util.find_spec(m)) for m in ['numpy','scipy','sklearn','tensorflow','pandas']}}))
for p in roots:
    if p.exists():
        for branch in ['Features/biomarker_n1_n2_refinement','processed/HMC_preprocessed','models/HMC_CHECKPOINTS']:
            d=p/branch
            print(str(d),[f.name for f in d.iterdir()] if d.exists() else 'MISSING')
