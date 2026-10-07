def _ppt_export_validation_inputs():
    import json, tarfile
    from pathlib import Path
    import numpy as np
    base=Path('/content/drive/MyDrive/Sleep_Health_Profiling/processed/HMC_preprocessed')
    split=json.loads((base/'subject_split.json').read_text())
    out=Path('/content/ppt_authoritative_artifacts')
    labels={}
    for group,ids in split.items():
        for sid in ids:
            p=Path('/content/ppt_corrected_test_inputs')/(sid+'.npz')
            if not p.exists():p=base/(sid+'.npz')
            with np.load(p,allow_pickle=False) as d:labels[group.replace('_subjects','')+'_'+sid]=d['Y'].astype(np.int32)
    np.savez_compressed(out/'validation_source_labels.npz',**labels)
    with tarfile.open('/content/ppt_validation_inputs.tar.gz','w:gz') as t:
        t.add(out/'validation_source_labels.npz',arcname='validation_source_labels.npz')
    print('Validation label sequences exported for independent metric/transition checks.')
try:
    _ppt_export_validation_inputs()
finally:
    del _ppt_export_validation_inputs
