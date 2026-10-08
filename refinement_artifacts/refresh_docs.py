from pathlib import Path
import json,shutil,hashlib
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'refinement_artifacts/verified';O=ROOT/'refinement_artifacts/originals'
r=json.loads((D/'final_results.json').read_text());m=json.loads((D/'overall_metrics.json').read_text())
summary='''The retained Fast SCFormer-U evidential Transformer classifies four-channel, 100 Hz EEG in 30-second epochs. A StandardScaler and balanced logistic regression refine only predicted N1/N2 epochs using nine spectral features. Architecture and EEG features form recording-level profiles compared with a 16-recording HMC training reference using z-scores and empirical P10/P90 boundaries. Four architecture domains produce descriptive overall deviation levels.'''
caveat='''HMC is a heterogeneous clinical population, not a healthy normative cohort. LOW/NORMAL/HIGH indicate dataset-relative intervals. Mild/Moderate/High Deviation count deviated domains; they are not validated clinical severity, disease-risk predictions, or diagnoses. The stored SN001 input covers 190 epochs (95 minutes), so its profile describes a segment. NPZ timing assumes contiguous epochs; whole-night and lights-out timing are not independently established.'''
readme=f'''# EEG Sleep Classification and Reference-Based Sleep-Health Profiling

{summary}

Current implementation: [Biomarker_N1_N2_Refinement.ipynb](Biomarker_N1_N2_Refinement.ipynb). Current verified artifacts: [refinement_artifacts/verified](refinement_artifacts/verified). Desktop instructions: [gui/README.md](gui/README.md).

The 24-recording subset is split by recording ID into 16 training, four validation, and four test recordings (SN001, SN004, SN009, SN022). Stored inputs contain 15,216 / 3,619 / 3,109 epochs. Disjoint recording IDs prevent within-recording epoch leakage. SN IDs identify recordings; no repeated-night person mapping is supplied.

The independent Colab reproduction HMC-N1N2-20261007 gives:

| Measure | Transformer | N1/N2 refined |
| --- | ---: | ---: |
| Accuracy | {m['raw']['accuracy']*100:.2f}% | {m['refined']['accuracy']*100:.2f}% |
| Macro F1 | {m['raw']['macro_f1']*100:.2f}% | {m['refined']['macro_f1']*100:.2f}% |
| N1 F1 | 36.60% | 40.63% |
| N2 F1 | 57.12% | 63.57% |

2,871 predictions remain unchanged; 154 are corrected, 51 change while staying wrong, and 33 degrade. W/N3/REM predictions remain unchanged. This is separate from the earlier 3,773-epoch EDF reconstruction/Viterbi experiment archived in `ppt_artifacts`.

The master matrices have 23 columns: recording ID plus 22 numeric fields. There are 13 recording/architecture fields and nine EEG features. Deviation analysis excludes recording duration and compares 21 fields; ten architecture metrics determine the four domains. EEG deviations are shown alongside them and do not contribute to domain counts.

{caveat}

The [HMC v1.1 dataset source](https://physionet.org/content/hmc-sleep-staging/1.1/) documents 151 PSG recordings, four EEG derivations, 256 Hz source sampling and the heterogeneous clinical population.

## Deliverables

- `final_sleep_stage_project_presentation.pptx` and `.pdf`: detailed 41-slide report.
- `sleep_stage_project_12_slides.pptx` and `.pdf`: 12-slide summary.
- `mid.original_backup.pptx` and `.pdf`: updated 41-slide third deck. Its pre-update original is preserved under `refinement_artifacts/originals/`.
- `gui/`: Windows Electron application with Colab worker, current offline results and PDF/JSON/CSV/ZIP exports.
- `refinement_artifacts/refinement_completion_audit.md`: verification, source lineage and limitations.

## Reproduction

The audit script `refinement_artifacts/reproduce.py` loads the existing checkpoint, reads stored EEG, extracts features, fits only the training N1/N2 subset, and derives training reference statistics. It writes only an isolated `/content/eeg_refinement_audit` directory. It never trains the Transformer or changes the original NPZs.

Preprocessing applies the 50 Hz notch at the original rate before resampling, then 0.3-35 Hz filtering, 100 Hz resampling and 30-second epoch/channel normalization. Notebook inference normalizes each epoch again; spectral features use the stored input. Welch uses 4-second windows and 2-second overlap, total power 0.5-30 Hz and upper-exclusive band masks. All channel powers are averaged before forming relative powers and ratios. Night EEG features average all evaluated epochs, including Wake.

Original notebooks, source decks, and the previous evaluation artifacts are historical evidence; they are not the current reported experiment.
'''
(ROOT/'README.md').write_text(readme + "\n## Repository layout\n\n- `Biomarker_N1_N2_Refinement.ipynb`: current implementation.\n- `gui/`: desktop application, worker, and tests.\n- `refinement_artifacts/`: current verified results, reproduction tools, and preserved originals.\n- `ppt_artifacts/` and `ppt_short_artifacts/`: historical experiment evidence and presentation tools.\n- `notebooks/archive/`: earlier training notebook and its connection-check backup.\n- `tools/colab/`: Colab connection diagnostics and notebook preparation utilities.\n- `docs/`: proposal, audits, verified result summary, and extracted presentation text.\n- Root `.pptx` and `.pdf` files: current detailed, summary, and third presentation decks and exports. All source and backup PowerPoint files are retained.\n\nRun Colab utilities from their new paths, for example `python tools/colab/prepare_colab_checks.py`. The preparation script preserves its existing behavior: it refuses to overwrite an existing diagnostics notebook.\n",encoding='utf8')
gui=f'''# Sleep Studio

Windows Electron workspace for the current N1/N2 spectral refinement and descriptive sleep-health reference pipeline.

```powershell
cd "{ROOT/'gui'}"
npm install
npm start
```

`start.bat` also launches the app. Windows runs Electron; Ubuntu WSL runs the existing Colab CLI, normally `~/.venvs/colab-cli/bin/colab`. Use Connection & settings to discover or connect a runtime, mount Drive and verify the checkpoint/dataset paths. Package checks now include SciPy and scikit-learn.

Offline Overview and Results display the independently reproduced `HMC-N1N2-20261007` run: 3,109 stored test epochs, 55.45% raw accuracy, 59.34% refined accuracy. Choose SN001, SN004, SN009 or SN022 in Results. The Sleep profile tab shows four domains, the overall deviation level, architecture, all nine spectral features, z-scores and reference P10/P90 values.

## Running an analysis

1. Connect your existing Colab runtime and mounted project Drive.
2. Data & Run accepts project NPZ examples, Drive files or Windows EDF/NPZ imports.
3. N1/N2 spectral refinement defaults on. Its fitted scaler/coefficients and training reference are checkpoint-specific and are uploaded with each isolated run. A different checkpoint needs its own refiner; disable refinement for raw inference with that checkpoint.
4. Project examples use the notebook’s stored NPZ sequences, with an explicit continuity assumption displayed in the interface. Project SHA256 hashes are checked against the audit. They do not silently reconstruct SN001 into a different experiment.
5. Imported NPZs need confirmation of channel order/preprocessing and a continuity assumption if timestamps are absent. Unknown timing or gaps makes SOL/WASO/fragmentation unavailable; incomplete domains produce an unavailable overall profile.
6. Results include hypnograms, original evidential probabilities/uncertainty, raw/refined evaluations, descriptive profiles, artifacts and PDF/JSON/CSV/ZIP exports.

The Transformer is retained. Ground truth is used only for evaluation and training subset construction; test routing depends only on the predicted N1/N2 label. Nine EEG features use Delta 0.5-4, Theta 4-8, Alpha 8-12, Sigma 12-16, Beta 16-30 Hz, plus four band/Delta ratios. Welch uses 400 samples and 200 overlap at 100 Hz. Relative powers use 0.5-30 Hz total power, average channel powers first, and include all epochs in recording-level spectral means.

## Architecture and profiling

TST excludes Wake. Efficiency is TST / evaluated recording duration. N1/N2/N3/REM percentages use TST. SOL starts at the evaluated sequence origin. WASO includes terminal Wake after sleep onset; REM latency starts at sleep onset. Awakenings count non-Wake → Wake. Fragmentation counts all stage transitions per TST hour and is project-defined.

Reference mean, sample SD (ddof=1), median, P10 and P90 come from 16 training recordings only. Bounds are inclusive. 0/1/2/3–4 deviated domains give Within Reference/Mild/Moderate/High Deviation. EEG features, REM latency and total transition count are available for comparison but are not independently counted as extra domain flags.

{caveat}

There is no explicit spindle detection, dedicated formal SWA metric, spectral edge frequency, disease predictor, healthy normative cohort, or true repeated-night personalization. Model uncertainty is a different concept from reference deviation and is not recalibrated by N1/N2 label refinement.

## Validation and provenance

```powershell
npm run build
npm test
npm run test:ui
npm run test:desktop
```

Run Python unittest discovery under a Python environment. `tests/test_pipeline.py` verifies archived Viterbi evidence; `tests/test_refinement.py` verifies the current architecture, exact fitted-refiner predictions, boundaries and missing-data behavior. The active baseline is `refinement_artifacts/verified`; `ppt_artifacts` contains the previous evaluation.

Each run stores its settings, input hashes and results under app data. OAuth credentials stay in the WSL CLI configuration. Every worker runs in its own `/content/eeg_sleep_studio/<run-id>` folder. History supports cancellation and recovery. Training writes a separate checkpoint and retains the existing architecture; it does not automatically create a compatible spectral refiner for the new checkpoint.
'''
for name in ['gui/README.md','docs/ppt_completion_audit.md','docs/sleep_stage_verified_results.txt','docs/multistage_pipeline_proposal.md']:
    src=ROOT/name;dest=O/src.name
    if src.exists() and not dest.exists():shutil.copy2(src,dest)
(ROOT/'gui/README.md').write_text(gui,encoding='utf8')
(ROOT/'docs/sleep_stage_verified_results.txt').write_text(summary+'\n\n'+json.dumps({'run_id':r['run_id'],'metrics':m,'changes':r['changes'],'n1n2_only':r['n1n2_only']},indent=2)+'\n\n'+caveat,encoding='utf8')
(ROOT/'docs/ppt_completion_audit.md').write_text('# Current presentation audit\n\nThe three decks and PDFs now use HMC-N1N2-20261007. See [the complete current audit](../refinement_artifacts/refinement_completion_audit.md). The prior audit is preserved under refinement_artifacts/originals.\n\n'+caveat+'\n',encoding='utf8')
p=ROOT/'docs/multistage_pipeline_proposal.md';old=p.read_text(encoding='utf8');p.write_text('# Historical future-work proposal\n\nCurrent implementation: '+summary+'\n\nThis proposal concerns future architecture research, not the current N1/N2 refinement. Its old baseline comparisons are historical; current results are in README.md.\n\n'+old,encoding='utf8')
(ROOT/'ppt_artifacts/README.md').write_text('# Archived prior evaluation\n\nThis directory records HMC-PPT-20261007-01, including SN001 EDF reconstruction (854 epochs), 3,773 test epochs and Soft-Viterbi. Its biomarker definitions and heuristic categories belong to the historical experiment. The current source is Biomarker_N1_N2_Refinement.ipynb; current artifacts are ../refinement_artifacts/verified. Do not mix the two denominators or present old risk categories as current outcomes.\n',encoding='utf8')
source=ROOT/'Biomarker_N1_N2_Refinement.ipynb';backup=O/source.name
if not backup.exists():shutil.copy2(source,backup)
n=json.loads(source.read_text(encoding='utf8'));n['cells']=n['cells'][:47]
n['cells'][0]['source']=('# EEG Sleep Classification and Reference-Based Sleep-Health Profiling\n\n'+summary+'\n\n'+caveat+'\n\nThis notebook contains the current refinement pipeline. Legacy development/Viterbi cells are preserved in refinement_artifacts/originals/Biomarker_N1_N2_Refinement.ipynb.\n').splitlines(keepends=True)
n['cells'][2]['source']="from google.colab import drive\ndrive.mount('/content/drive')\n".splitlines(keepends=True);n['cells'][2]['outputs']=[];n['cells'][2]['execution_count']=None
n['cells'][3]['source']=[line.replace('/content/gdrive/MyDrive','/content/drive/MyDrive') for line in n['cells'][3]['source']];n['cells'][3]['outputs']=[];n['cells'][3]['execution_count']=None
n['cells'].insert(2,{'cell_type':'markdown','metadata':{},'source':('## Reproduction and interpretation\n\nVerified on the existing Colab runtime with the saved checkpoint and stored NPZ inputs. Test epochs: 3,109. The stored SN001 input has 190 epochs (95 minutes). The 4 × 23 and 16 × 23 tables include an ID and 22 numeric columns; 21 fields are compared after excluding recording_minutes. EEG biomarkers do not enter the four-domain count. Reference architecture uses fitted training predictions; boundaries use sample SD and empirical linear quantiles.\n\nTransformer inference uses per-epoch/per-channel normalization again. Spectral features use the stored EEG, average powers across channels first and then form ratios. The 50 Hz notch belongs before resampling to 100 Hz.\n').splitlines(keepends=True)})
n['cells'].append({'cell_type':'markdown','metadata':{},'source':['## Export reproducible refinement and reference artifacts\n','Run the following cell after the current pipeline. It exports complete tables rather than truncated display tables.\n']})
export='''import json
from pathlib import Path
export_dir = Path(EXPERIMENT_PATH)
export_dir.mkdir(parents=True, exist_ok=True)
scaler = refinement_model.named_steps["scaler"]
classifier = refinement_model.named_steps["classifier"]
refinement_parameters = {
    "feature_order": BIOMARKER_FEATURES,
    "mean": scaler.mean_.tolist(), "scale": scaler.scale_.tolist(),
    "coefficients": classifier.coef_[0].tolist(),
    "intercept": float(classifier.intercept_[0]), "classes": [1, 2],
    "training_subjects": train_subjects,
    "training_filter": "predicted and true stages are N1/N2, training only"
}
import hashlib
refinement_parameters["checkpoint_sha256"] = hashlib.sha256(Path(MODEL_PATH).read_bytes()).hexdigest()
(export_dir / "refinement_model.json").write_text(json.dumps(refinement_parameters, indent=2))
for name, frame in {
    "master_sleep_health_features": master_sleep_health_features,
    "train_reference_features": train_reference_features,
    "reference_stats": reference_stats,
    "test_deviation_profiles": test_deviation_profiles,
    "domain_profiles": domain_profiles_df,
    "sleep_health_profiles": sleep_health_profiles_df,
    "baseline_refined_test": baseline_refined_test
}.items():
    frame.to_csv(export_dir / (name + ".csv"), index=False)
    (export_dir / (name + ".json")).write_text(frame.to_json(orient="records", indent=2))
print("Exported fitted refinement and complete reference tables to", export_dir)
'''
# Match the actual variable names from the original cells, checked below.
source_text='\n'.join(''.join(c['source']) for c in n['cells'])
if 'domain_profiles_df =' not in source_text:export=export.replace('domain_profiles_df','domain_profile_df')
if 'sleep_health_profiles_df =' not in source_text:export=export.replace('sleep_health_profiles_df','sleep_health_profile')
n['cells'].append({'cell_type':'code','metadata':{},'execution_count':None,'outputs':[],'source':export.splitlines(keepends=True)})
source.write_text(json.dumps(n,indent=1,ensure_ascii=False)+'\n',encoding='utf8')
print('Updated project docs and focused the active notebook on the current pipeline; originals preserved.')
