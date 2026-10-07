def _ppt_repository_probe():
 import os,json,zipfile
 from pathlib import Path
 import numpy as np
 base=Path('/content/drive/MyDrive/Sleep_Health_Profiling')
 pre=base/'processed/HMC_preprocessed'
 split=json.loads((pre/'subject_split.json').read_text())
 print('SPLIT',json.dumps(split))
 for group,subjects in split.items():
  for sid in subjects:
   p=pre/(sid+'.npz')
   with np.load(p,allow_pickle=False) as d:
    print('SUBJECT',group,sid,'X',d['X'].shape,'Y',d['Y'].shape,'counts',np.bincount(d['Y'].astype(int),minlength=5).tolist())
 for rel in ['models','processed/HMC_preprocessed/final_deliverables','Features']:
  folder=base/rel
  for root,dirs,files in os.walk(folder):
   for f in files:
    p=Path(root)/f
    print('FILE',p,p.stat().st_size)
    if f.endswith(('.json','.csv')) and p.stat().st_size<50000:
     print('CONTENTS',p,p.read_text())
 for p in (base/'models').rglob('*.keras'):
  with zipfile.ZipFile(p) as z:
   print('MODEL_CONFIG',str(p),z.read('config.json').decode())
   print('MODEL_METADATA',str(p),z.read('metadata.json').decode())
try:
 _ppt_repository_probe()
finally:
 del _ppt_repository_probe
