from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def replace(file,pairs):
    p=ROOT/file;s=p.read_text(encoding='utf8')
    for a,b in pairs:s=s.replace(a,b)
    p.write_text(s,encoding='utf8')
replace('gui/tests/store.test.cjs',[
 ("{smoothing:'false'}","{refinement:'false'}"),('3773','3109'),('soft_viterbi','refined'),
 ('0.6199310893188444','0.5934384046317144'),('authoritative_checkpoint.keras','refinement_model.json'),
 ('0.6199','0.5934'),('HMC-PPT-20261007-01','HMC-N1N2-20261007')])
replace('gui/tests/ui/workspace.spec.ts',[
 ('61.99%','59.34%'),('22,608','21,944'),('0.619931','0.593438'),
 ("});\r\n", "});\n")])
replace('gui/scripts/smoke-desktop.cjs',[('3773','3109')])
replace('gui/electron/main.cjs',[('smoothed_confusion_matrix_normalized|soft_viterbi_confusion_matrix','refined_confusion_matrix|raw_confusion_matrix|performance_comparison')])
replace('gui/bridge/host.py',[("'--config',str(config),'--logtostderr',*args","'--config',str(config),*args")])
replace('gui/src/App.tsx',[
 ('Sleep stages as a percentage of TST; Wake shown separately','Sleep-stage percentages use TST; Wake is excluded'),
 ('SN009 · refined predictions','SN009 · percentage of TST'),
 ('macro F1 score','macro F1 score'),
 ('data.connection.packages||{numpy:null,tensorflow:null,keras:null,mne:null,matplotlib:null}', 'data.connection.packages||{numpy:null,tensorflow:null,keras:null,mne:null,matplotlib:null,scipy:null,"scikit-learn":null}'),
 ('connection.packages||{numpy:null,tensorflow:null,keras:null,mne:null,matplotlib:null}', 'connection.packages||{numpy:null,tensorflow:null,keras:null,mne:null,matplotlib:null,scipy:null,"scikit-learn":null}')])
replace('gui/electron/store.cjs',[("rules:this.read(this.legacy,'risk_rules.json',{})","rules:this.read(this.baseline,'profile_rules.json',{})")])
print('Updated regression expectations, exports and runtime checks.')
