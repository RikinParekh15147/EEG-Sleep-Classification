# EEG Sleep Classification and Reference-Based Sleep-Health Profiling

The retained Fast SCFormer-U evidential Transformer classifies four-channel, 100 Hz EEG in 30-second epochs. A StandardScaler and balanced logistic regression refine only predicted N1/N2 epochs using nine spectral features. Architecture and EEG features form recording-level profiles compared with a 16-recording HMC training reference using z-scores and empirical P10/P90 boundaries. Four architecture domains produce descriptive overall deviation levels.

Current implementation: [Biomarker_N1_N2_Refinement.ipynb](Biomarker_N1_N2_Refinement.ipynb). Current verified artifacts: [refinement_artifacts/verified](refinement_artifacts/verified). Desktop instructions: [gui/README.md](gui/README.md).

The 24-recording subset is split by recording ID into 16 training, four validation, and four test recordings (SN001, SN004, SN009, SN022). Stored inputs contain 15,216 / 3,619 / 3,109 epochs. Disjoint recording IDs prevent within-recording epoch leakage. SN IDs identify recordings; no repeated-night person mapping is supplied.

The independent Colab reproduction HMC-N1N2-20261007 gives:

| Measure | Transformer | N1/N2 refined |
| --- | ---: | ---: |
| Accuracy | 55.45% | 59.34% |
| Macro F1 | 57.42% | 59.51% |
| N1 F1 | 36.60% | 40.63% |
| N2 F1 | 57.12% | 63.57% |

2,871 predictions remain unchanged; 154 are corrected, 51 change while staying wrong, and 33 degrade. W/N3/REM predictions remain unchanged. This is separate from the earlier 3,773-epoch EDF reconstruction/Viterbi experiment archived in `ppt_artifacts`.

The master matrices have 23 columns: recording ID plus 22 numeric fields. There are 13 recording/architecture fields and nine EEG features. Deviation analysis excludes recording duration and compares 21 fields; ten architecture metrics determine the four domains. EEG deviations are shown alongside them and do not contribute to domain counts.

HMC is a heterogeneous clinical population, not a healthy normative cohort. LOW/NORMAL/HIGH indicate dataset-relative intervals. Mild/Moderate/High Deviation count deviated domains; they are not validated clinical severity, disease-risk predictions, or diagnoses. The stored SN001 input covers 190 epochs (95 minutes), so its profile describes a segment. NPZ timing assumes contiguous epochs; whole-night and lights-out timing are not independently established.

The [HMC v1.1 dataset source](https://physionet.org/content/hmc-sleep-staging/1.1/) documents 151 PSG recordings, four EEG derivations, 256 Hz source sampling and the heterogeneous clinical population.

## Deliverables

- `final_sleep_stage_project_presentation.pptx` and `.pdf`: detailed 41-slide report.
- `sleep_stage_project_12_slides.pptx` and `.pdf`: 12-slide summary.
- `mid.original_backup.pptx` and `.pdf`: updated 41-slide third deck. Its pre-update original is preserved under `refinement_artifacts/originals/`.
- `gui/`: Windows Electron application with Colab worker, current offline results and PDF/JSON/CSV/ZIP exports.
- `refinement_artifacts/refinement_completion_audit.md`: verification, source lineage and limitations.

## Reproduction

The audit script `refinement_artifacts/reproduce.py` loads the existing checkpoint, reads stored EEG, extracts features, fits only the training N1/N2 subset, and derives training reference statistics. It writes an isolated `/content/eeg_refinement_audit` directory and saves a recovery bundle under the experiment's `independent_audit` Drive folder. It never trains the Transformer or changes the original NPZs.

Preprocessing applies the 50 Hz notch at the original rate before resampling, then 0.3-35 Hz filtering, 100 Hz resampling and 30-second epoch/channel normalization. Notebook inference normalizes each epoch again; spectral features use the stored input. Welch uses 4-second windows and 2-second overlap, total power 0.5-30 Hz and upper-exclusive band masks. All channel powers are averaged before forming relative powers and ratios. Night EEG features average all evaluated epochs, including Wake.

Original notebooks, source decks, and the previous evaluation artifacts are historical evidence; they are not the current reported experiment.

## Repository layout

- `Biomarker_N1_N2_Refinement.ipynb`: current implementation.
- `gui/`: desktop application, worker, and tests.
- `refinement_artifacts/`: current verified results, reproduction tools, and preserved originals.
- `ppt_artifacts/` and `ppt_short_artifacts/`: historical experiment evidence and presentation tools.
- `notebooks/archive/`: earlier training notebook and its connection-check backup.
- `tools/colab/`: Colab connection diagnostics and notebook preparation utilities.
- `docs/`: proposal, audits, verified result summary, and extracted presentation text.
- Root `.pptx` and `.pdf` files: current detailed, summary, and third presentation decks and exports. All source and backup PowerPoint files are retained.

Run Colab utilities from their new paths, for example `python tools/colab/prepare_colab_checks.py`. The preparation script preserves its existing behavior: it refuses to overwrite an existing diagnostics notebook.
