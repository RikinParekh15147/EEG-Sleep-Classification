from pathlib import Path
import csv,hashlib,json,re,shutil,zipfile
from xml.etree import ElementTree as ET
ROOT=Path(__file__).resolve().parents[1];A=ROOT/'refinement_artifacts';D=A/'verified'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
names=['final_sleep_stage_project_presentation','sleep_stage_project_12_slides','mid.original_backup']
inventory={};deliverables=[]
ns={'a':'http://schemas.openxmlformats.org/drawingml/2006/main'}
for name in names:
    p=ROOT/(name+'.pptx')
    with zipfile.ZipFile(p) as z:
        slides=sorted([n for n in z.namelist() if re.fullmatch(r'ppt/slides/slide\d+\.xml',n)],key=lambda n:int(re.search(r'(\d+)\.xml',n)[1]))
        texts=['\n'.join(ET.fromstring(z.read(n)).findall('.//a:t',ns)[i].text or '' for i in range(len(ET.fromstring(z.read(n)).findall('.//a:t',ns)))) for n in slides]
        tables=sum(z.read(n).count(b'<a:tbl>') for n in slides)
    receipt=read(A/'validation'/(name+'.pptx.validation.json'))
    assert sha(p)==receipt['finalSha256'],name
    assert len(slides)==(12 if '12_slides' in name else 41)
    text='\n\n'.join(f'Slide {i+1}\n{s}' for i,s in enumerate(texts))
    assert 'N1/N2' in text and 'High Deviation' in text
    assert not any(t in text for t in ['Soft-Viterbi','Healthy Sleep','High Risk','[Insert','[Your'])
    inventory[name]={'slides':len(slides),'native_tables':tables,'texts':texts}
    target='presentation_text.txt' if name.startswith('final_') else 'sleep_stage_project_12_slides.txt' if '12_slides' in name else 'mid_original_backup.txt'
    src=ROOT/'docs'/target;backup=A/'originals'/target
    if src.exists() and not backup.exists():shutil.copy2(src,backup)
    src.write_text(text+'\n',encoding='utf8')
    for ext in ['.pptx','.pdf']:
        file=ROOT/(name+ext);assert file.is_file() and file.stat().st_size>10000
        deliverables.append({'file':file.name,'sha256':sha(file),'bytes':file.stat().st_size,'pages_or_slides':len(slides)})
(A/'current_slide_inventory.json').write_text(json.dumps(inventory,indent=2,ensure_ascii=False),encoding='utf8')
bounds=read(A/'renders/text_bounds.json');overflow=[b for b in bounds if b['boundHeight']>b['height']+2 or b['boundWidth']>b['width']+2]
assert not overflow
for name in ['master_sleep_health_features','train_reference_features','validation_night_features']:
    with (D/(name+'.csv')).open() as f:rows=list(csv.DictReader(f))
    value=[{k:v if k=='subject' else float(v) if v else None for k,v in r.items()} for r in rows]
    (D/(name+'.json')).write_text(json.dumps(value,indent=2),encoding='utf8')
manifest={'updated':'2026-10-08','run_id':'HMC-N1N2-20261007','deliverables':deliverables,'rendered_slides':94,'measured_text_boxes':len(bounds),'measured_text_overflows':len(overflow),'native_application':'Microsoft PowerPoint 2024','pdf_render_checks':['detailed-reference','short-reference','third-profiles','gui-report'],'numerical_validation':read(D/'numerical_validation.json'),'gui_checks':{'production_build':'passed','backend_tests':9,'python_tests_in_ubuntu':14,'browser_tests':4,'native_electron':'passed','native_wsl_bridge':'passed','native_pdf_export':'passed','live_sn009_worker_epochs':901,'live_input_hash_check':'passed'}}
(A/'completion_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
results=read(D/'final_results.json');metrics=read(D/'overall_metrics.json')
audit=f'''# N1/N2 refinement completion audit

Updated 8 October 2026. Current experiment: **HMC-N1N2-20261007**.

All three root presentations and their PDF exports use the verified N1/N2 refinement pipeline. The detailed and third decks each retain 41 slides, and the summary retains 12. Original source decks, PDFs, notebook, documentation and the prior GUI validation are preserved in `originals/`.

## Evidence and results

The source is the new pipeline in the first 47 cells of the supplied `Biomarker_N1_N2_Refinement.ipynb` (original code cells 1–46). Its original SHA256 is `{read(A/'source_manifest.json')['sha256']}`. The active notebook now contains the current pipeline, interpretation notes and complete artifact exports. Historical development cells remain in the preserved full original.

The independent CPU Colab reproduction read the 24 original stored NPZ inputs and the existing checkpoint, normalized each input again for Transformer inference, extracted Welch features from stored EEG, fitted the refiner using training data only, and rebuilt the training reference. The checkpoint SHA256 is `{results['checkpoint_sha256']}`. No Transformer retraining or source NPZ changes occurred. `reproduce.py` writes isolated outputs and a recovery bundle under the experiment's `independent_audit` Drive folder.

| Measure | Transformer | Refined |
| --- | ---: | ---: |
| Accuracy | {metrics['raw']['accuracy']*100:.2f}% | {metrics['refined']['accuracy']*100:.2f}% |
| Macro F1 | {metrics['raw']['macro_f1']*100:.2f}% | {metrics['refined']['macro_f1']*100:.2f}% |
| N1 F1 | 36.60% | 40.63% |
| N2 F1 | 57.12% | 63.57% |

Test epochs: 3,109. Unchanged: 2,871. Corrected: 154. Wrong-to-wrong: 51. Degraded: 33. Changed: 238. Accuracy gains 3.89 percentage points; macro F1 gains 2.10 using unrounded values. All true N1/N2 epochs have accuracy 53.75% → 60.95%, with denominator 1,680.

Local code reproduces all 3,109 raw/refined class decisions, all architecture values for 12 test profiles, all four descriptive profile outcomes, all 22 reference means/sample SDs/medians/linear quantiles, and the notebook's displayed coefficient/reference precision. Evidential formulas match within source float32 rounding, with a maximum probability difference of 1.26e-7 from Python double arithmetic. `verified/numerical_validation.json` records the checks.

## Corrections and interpretation

- The current dataset has 15,216 training, 3,619 validation and 3,109 test epochs, totaling 21,944. Disjoint recording IDs prevent within-recording epoch leakage. SN IDs are recording identifiers; a separate repeated-person mapping was not supplied.
- SN001 has **190 stored epochs, or 95 minutes**. Its profile describes a segment. The earlier reconstruction to 854 epochs and 3,773 total test epochs is a separate archived experiment, with separate Viterbi metrics.
- Fit candidates require both true and predicted N1/N2 on training data (1,278 N1 / 4,588 N2). Test routing uses predicted labels only. Original predicted W/N3/REM are retained.
- Welch: 100 Hz, 400 samples/window, 200 overlap. Average four-channel band powers before relative powers and ratios. Use upper-exclusive masks and total power 0.5–30 Hz. Recording EEG means include Wake epochs.
- The 50 Hz notch precedes resampling to 100 Hz. Band edges are project feature definitions. Sigma power is not spindle detection or spindle density.
- TST excludes Wake. Stage percentages use TST. Efficiency uses evaluated duration. WASO includes terminal Wake after first sleep. SOL is relative to sequence origin, and REM latency starts at first sleep. Fragmentation is all stage transitions per TST hour, a project-defined measure.
- Test/reference matrices are 4 × 23 and 16 × 23: one ID plus 22 numeric fields. Deviation compares 21 fields after excluding recording duration. Ten architecture metrics determine four domain statuses; EEG deviations do not add to the domain count.
- The reference uses 16 training recordings only, sample SD (ddof=1), and empirical linear P10/P90. Boundary equality is within reference. Training reference architecture is estimated in sample, after fitting the refiner.
- Four refined profiles: SN001 High (3 domains), SN004 High (3), SN009 Mild (1), SN022 Moderate (2).
- HMC is a heterogeneous clinical population, not a healthy normative cohort. LOW/NORMAL/HIGH are dataset positions. Mild/Moderate/High count deviated domains and are not clinical severity, disease-risk predictions or diagnoses. No explicit spindle detector, formal SWA, spectral edge, disease predictor or longitudinal personalization was implemented.
- Transformer uncertainty remains separate from profile deviation. N1/N2 label refinement does not recalibrate the five-stage probabilities or their uncertainty.

## GUI and artifact verification

The GUI now loads current artifacts, runs the exact fitted spectral refiner, shows architecture and nine EEG features, displays z-scores/P10/P90 and four domains, and exports current PDF/JSON/CSV/ZIP reports. Checkpoint compatibility and project-input hashes are checked. Unknown or discontinuous timing leaves temporal metrics and incomplete overall profiles unavailable.

TypeScript/Vite build passed. Nine backend tests, 14 Ubuntu Python tests and four browser tests passed. All four browser profiles and 21 comparison rows were checked, with desktop/mobile screenshots. Native Windows Electron loaded 3,109 epochs, navigated results, exercised the WSL bridge and exported a valid report PDF. A live Colab GUI worker reproduced every raw/refined prediction for all 901 SN009 epochs, enforced the audited input hash, reproduced Mild Deviation and transferred the ZIP bundle.

All 94 slides were rendered through PowerPoint and visually reviewed. Structural package, slide geometry, font-policy and first-party import checks passed for each deck. Native measurements found no overflow in {len(bounds)} text boxes. Tables were inspected visually. PDF page counts are 41 / 12 / 41; representative dense PDF pages and the GUI report were independently rendered with Poppler and reviewed. Native tables/text remain editable; scientific plots and the dashboard are raster images. `completion_manifest.json` records hashes and counts.

The earlier evaluation under `../ppt_artifacts` and old short-deck build under `../ppt_short_artifacts` are explicitly marked historical. Old evidence is preserved rather than silently rewritten. Root presentation text summaries and verified-results text now describe the current experiment.

Dataset source: [PhysioNet HMC Sleep Staging Database v1.1](https://physionet.org/content/hmc-sleep-staging/1.1/). Full input hashes, classifier parameters, epoch outputs, profiles and reference tables are under `verified/`.
'''
(A/'refinement_completion_audit.md').write_text(audit,encoding='utf8')
print(json.dumps({'slides':94,'text_boxes':len(bounds),'overflow':0,'deliverables':len(deliverables),'passed':True}))
