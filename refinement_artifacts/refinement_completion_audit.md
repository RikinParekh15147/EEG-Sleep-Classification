# N1/N2 refinement completion audit

Updated 8 October 2026. Current experiment: **HMC-N1N2-20261007**.

All three root presentations and their PDF exports use the verified N1/N2 refinement pipeline. The detailed and third decks each retain 41 slides, and the summary retains 12. Original source decks, PDFs, notebook, documentation and the prior GUI validation are preserved in `originals/`.

## Evidence and results

The source is the new pipeline in the first 47 cells of the supplied `Biomarker_N1_N2_Refinement.ipynb` (original code cells 1–46). Its original SHA256 is `0f39cff2b2b32d07de93d2c67bb8d541e9ec378fb4eb21a929250ec93dac3d77`. The active notebook now contains the current pipeline, interpretation notes and complete artifact exports. Historical development cells remain in the preserved full original.

The independent CPU Colab reproduction read the 24 original stored NPZ inputs and the existing checkpoint, normalized each input again for Transformer inference, extracted Welch features from stored EEG, fitted the refiner using training data only, and rebuilt the training reference. The checkpoint SHA256 is `3bf1423246d5672ce7473562079cb4e8d9aa1a578e18c1cb65e6b43e4156b226`. No Transformer retraining or source NPZ changes occurred. `reproduce.py` writes isolated outputs and a recovery bundle under the experiment's `independent_audit` Drive folder.

| Measure | Transformer | Refined |
| --- | ---: | ---: |
| Accuracy | 55.45% | 59.34% |
| Macro F1 | 57.42% | 59.51% |
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

All 94 slides were rendered through PowerPoint and visually reviewed. Structural package, slide geometry, font-policy and first-party import checks passed for each deck. Native measurements found no overflow in 507 text boxes. Tables were inspected visually. PDF page counts are 41 / 12 / 41; representative dense PDF pages and the GUI report were independently rendered with Poppler and reviewed. Native tables/text remain editable; scientific plots and the dashboard are raster images. `completion_manifest.json` records hashes and counts.

The earlier evaluation under `../ppt_artifacts` and old short-deck build under `../ppt_short_artifacts` are explicitly marked historical. Old evidence is preserved rather than silently rewritten. Root presentation text summaries and verified-results text now describe the current experiment.

Dataset source: [PhysioNet HMC Sleep Staging Database v1.1](https://physionet.org/content/hmc-sleep-staging/1.1/). Full input hashes, classifier parameters, epoch outputs, profiles and reference tables are under `verified/`.
