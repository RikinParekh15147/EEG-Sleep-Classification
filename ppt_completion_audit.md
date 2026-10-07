# Presentation completion audit

Run: **HMC-PPT-20261007-01**, 7 October 2026 (UTC).

## Deliverables and paths

The supplied presentation was edited as an existing 41-slide deck. No slides were removed. Its navy/teal/blue palette, 16:9 dimensions, Arial text, cover design and closing design were retained. Tables and numerical summaries remain editable; plots are exported from real data.

- Original: `/mnt/c/Users/Rikin Parekh/Documents/minorProject/mid.pptx`
- Exact backup: `mid.original_backup.pptx`
- Completed presentation: `final_sleep_stage_project_presentation.pptx`
- Artifacts: `ppt_artifacts/`
- Full precision machine-readable results: `ppt_artifacts/final_results.json`
- Plain text results: `sleep_stage_verified_results.txt`
- All slide text: `presentation_text.txt`
- Native PowerPoint slide renders and PDF: `ppt_artifacts/rendered_slides/`
- Original slide renders: `ppt_artifacts/original_render/`

Resolved path configuration is in `ppt_artifacts/paths.json`. Source and notebook directory are the project root. Processed inputs are in `/content/drive/MyDrive/Sleep_Health_Profiling/processed/HMC_preprocessed`; raw signals are in `/content/drive/MyDrive/Sleep_Health_Profiling/Data/HMC`; scoring annotations are in that directory's `recordings` subdirectory. Checkpoints are in `/content/drive/MyDrive/Sleep_Health_Profiling/models/HMC_CHECKPOINTS`. References are recorded in `ppt_artifacts/references.txt` and `literature_comparison.csv`.

## Preservation and repository audit

All original notebook cells and saved outputs were preserved byte for byte. No existing notebook cell was executed, rewritten, cleared or saved. Diagnostics ran through new standalone scripts in the already connected Colab kernel, inside temporary uniquely named functions that were deleted afterwards. No kernel restart was used. The original Drive arrays and model were read only; the repaired test input was written under a separate directory.

The repository was recursively inventoried using `rg --files` and source searches. Virtual environments and caches were treated as dependencies rather than experimental evidence. Project-owned files comprise the original notebook, its before-connection backup, connection-check notebooks and their helper scripts. No separate final model source tree or independent final dataset exists locally. Every source cell and saved output in the original notebook was inspected; machine-readable inventory is `notebook_cell_inventory.json`. Relevant source cells were exported to `authoritative_training_source.txt`, with split/training source and saved log separately exported. The 266 pre-connection cells match the backup; the additional cells are connection diagnostics.

Original notebook hashes are in `notebook_sha256_before.json` and are verified after completion. The original PPT and its backup are also hash-compared by `validate_results.py`.

### Authoritative pipeline

Zero-based notebook cells 201 (preprocessing), 203 (split), 205 (training arrays/weights), 206 (model and loss), 207 (fit and checkpoint selection), 211 (load final checkpoint), 212 (transitions), 213 (decoder) and 215 (biomarkers/risk rules) define the final pipeline. The final checkpoint is the only saved final project model found in the model directory:

`/content/drive/MyDrive/Sleep_Health_Profiling/models/HMC_CHECKPOINTS/best_objective1_model.keras`

SHA256: `3bf1423246d5672ce7473562079cb4e8d9aa1a578e18c1cb65e6b43e4156b226`.

A verified local copy is `ppt_artifacts/authoritative_checkpoint.keras`. Its Keras metadata gives version 3.13.2 and save time 2026-09-15 11:55:04. The checkpoint configuration, actual model summary/layers, saved training log, split counts and final source are mutually consistent. No alternative model was selected to improve reported metrics.

### Conflicts and excluded evidence

All original execution counts were cleared, so historical notebook outputs alone do not establish a fresh evaluation. Earlier notebook models/configurations and their results were not combined with the final checkpoint. Cell 2 contains dashboard fallback numbers (54.74%→62.30% accuracy, 57.01%→62.88% macro F1 and 0.4851→0.5367 kappa), demo profiles and dataset counts. These were excluded. A saved older approximately 75.94% accuracy belongs to another pipeline. Cell 214 explicitly reports model-loading failure and uses mock data; later hard-coded subject profiles and manually generated sequences are excluded. Every final confusion matrix, metric, uncertainty plot, hypnogram and profile comes from the executed run identified above.

## Data integrity, split and correction

The split reconstructed from cell 203 and matched to actual files is 16/4/4 across 24 unique SN recording IDs. No SN ID occurs in multiple splits. The repository calls these subject IDs, but no independent mapping from SN recording ID to person is supplied. Thus recording-ID separation is verified; cross-person identity cannot be independently established beyond the repository's one-ID-per-subject assumption. This qualification is stored in split/results files and slide notes.

| Split | IDs | Epochs |
|---|---|---:|
| Training | SN017, SN006, SN020, SN025, SN015, SN011, SN019, SN012, SN016, SN018, SN002, SN013, SN023, SN007, SN010, SN003 | 15,216 |
| Validation | SN024, SN005, SN021, SN008 | 3,619 |
| Test | SN009, SN001, SN004, SN022 | 3,773 |

All 24 raw/scoring EDF files were inspected. Twenty-three stored label sequences match the corresponding continuous 30-second EDF stage annotations. The stored SN001 input contains only 190 epochs and its label sequence cannot be matched to the complete annotated recording. It was not silently accepted or given guessed timestamps. SN001 was reconstructed from its untouched EDF with the exact final source preprocessing, yielding 854 valid epochs. Corrected input: `/content/ppt_corrected_test_inputs/SN001.npz`, with a hash-verified local copy at `ppt_artifacts/corrected_test_inputs/SN001.npz`. Details and original hash are in `input_repairs.json`; full input hashes are in `data_manifest.json`. Original SN001 was preserved. Since only a held-out input changed and training/validation inputs stayed unchanged, no retraining was required.

Final test sizes are SN009 901, SN001 854, SN004 1,016 and SN022 1,002 epochs. All final sequences have zero missing-epoch gaps. Total usable epochs: 22,608. Stage counts and percentages for every split are in `stage_distribution.csv`; all-split totals in Wake/N1/N2/N3/REM order are 4,288/2,446/8,258/4,103/3,513. Training counts are 3,202/1,553/5,254/2,926/2,281. There is no source amplitude-rejection step. Original epoch exclusion statistics were not saved, so no fabricated rejection counts were reported. Raw recording duration, annotation counts and gaps are recorded in `raw_recording_audit.json`.

Preprocessing: channels EEG F4-M1, EEG C4-M1, EEG O2-M1 and EEG C3-M2; original sampling verified 256 Hz; 50 Hz notch, 0.3–35 Hz bandpass, resampling to 100 Hz; 30-second epochs; each channel/epoch standardized as `(X−mean)/(std+1e−6)` in float32; `reject_by_annotation=False`. Filter order matches the source. The MNE EDF-header warnings about differing channel high/low-pass metadata are preserved in execution logs; these do not change the explicitly applied final filters.

Real EEG example: SN009, EEG F4-M1, recording seconds 300–330 (epoch 10). Raw plot uses µV derived from MNE volts; processed plot uses normalized amplitude. Same interval/channel was used for both. Reprocessed and stored example matched exactly (maximum absolute difference zero). Data and metadata are saved separately.

## Model and training provenance

Actual architecture is a hybrid CNN–self-attention/Transformer–BiLSTM, not a pure Transformer:

- Input (4,3000), permute to (3000,4).
- Conv1D 64, kernel 7, stride 4, same padding; batch normalization and ReLU; output (750,64).
- Conv1D 128, kernel 5, stride 4, same padding; batch normalization and ReLU; output (188,128).
- Multi-head attention: 4 heads, key dimension 16; residual/layer normalization; feed-forward 128→128 with GELU; residual/layer normalization.
- Bidirectional LSTM: 64 units each direction, return sequences (188,128).
- Global average pool; dropout 0.2; dense 128 ReLU; dropout 0.1; dense 5 softplus evidence.

226,309 total parameters; 225,925 trainable; 384 non-trainable. Saved training uses Adam at approximately 1e−4, batch 128, maximum/completed 10 epochs. Checkpoint selected at epoch 9 by maximum validation evidential accuracy (0.6797457933425903). Early stopping patience 5 with restore-best enabled did not trigger. No scheduler or layer/weight-decay regularizer is in the final training cell. Balanced class weights are Ntraining/(5Nk). Loss uses label smoothing 0.05, CE of normalized Dirichlet means, plus evidence penalty coefficient 0.003 for evidence assigned outside the smoothed target. Full configuration is in `hyperparameters.json`.

Final training hardware and global training random-state provenance are unavailable. Split seed 42 is explicit. An earlier cell sets a training seed, but execution order cannot be recovered, so a final training seed/GPU was not invented. Saved history was recovered, not synthesized or retrained. Training and validation loss differ in class weighting, which is explicitly noted on plots. Evaluation environment/library versions are saved independently; they are not claimed as complete historical training versions.

## Executed evaluation and independent verification

The actual evaluation command was:

```bash
/home/rikin_parekh/.venvs/colab-cli/bin/colab --auth oauth2 --config /tmp/eeg-colab-checks/sessions.json exec -s eeg-diagnostics -f ppt_artifacts/evaluate_authoritative_run.py --timeout 1800
```

The script audits every original input, corrects SN001 in a new location, loads the exact checkpoint, runs fresh inference, constructs Dirichlet outputs, learns transitions only from training labels, decodes each recording separately and saves all results. Full source and output are `evaluate_authoritative_run.py` and `authoritative_evaluation.log`; executed source hash is `executed_evaluation_source.sha256`. The temporary CLI session configuration is environment-specific, contains connection state, and was not copied into the artifact package. For reproduction on a new runtime, mount the same Drive directory and create a connected CLI session first.

| Metric | Raw model | Soft-Viterbi |
|---|---:|---:|
| Accuracy | 53.75% | 61.99% |
| Balanced accuracy | 57.83% | 64.26% |
| Macro F1 | 55.12% | 61.76% |
| Weighted F1 | 54.92% | 61.93% |
| Cohen's kappa | 0.4060 | 0.4999 |

Full-precision metrics, macro precision/recall and all per-class reports are retained in JSON/CSV. Both conditions use the identical 3,773 epoch identities. Every confusion-matrix support, row count, diagonal accuracy and report total reconciles. Raw N1 has lowest F1 (0.3657); N2 has lowest recall (0.4400). Smoothing improves all listed aggregate metrics but reduces some stage recalls (e.g., N1/N3); it does not establish clinical validity.

Probability construction is alpha=evidence+1, p=alpha/sum(alpha), uncertainty=5/sum(alpha). This is not `1−max softmax`. There is no separately fitted calibrator or self-calibrated checkpoint. Raw calibration: 10-bin ECE 0.0704548380; multiclass summed Brier 0.5879372997; NLL 1.1011897762; uncertainty error AUROC 0.5798189247; discrete-mean AURC 0.3628265846. Correct/incorrect mean uncertainty is 0.2280234826/0.2354807075, indicating weak discrimination rather than assumed reliable rejection. Reliability bin counts, risk/coverage values, epoch evidence/alpha/probabilities and uncertainty are saved.

Soft-Viterbi is the source's weighted MAP Viterbi dynamic program, not differentiable soft-DP. Laplace pseudocount 1 per training transition cell; training stage-prevalence initialization with one pseudocount per class; epsilon 1e−12; log emission weight 0.9. Class order is Wake,N1,N2,N3,REM. Decoder restarts per recording and per missing-epoch gap, correcting the source's unsafe potential concatenation behavior. No transition uses validation/test labels and no hyperparameter was tuned to test performance. All transitions remain possible. Pseudocode and transition configuration are saved.

`export_validation_inputs.py` exported actual stored training/validation/test labels for independent checks. `validate_results.py` independently recomputes confusion metrics, Dirichlet identities, class weights, transitions, an alternative Viterbi implementation, biomarker/risk rules, ECE/Brier/NLL/error AUROC/AURC, history checkpoint selection, file preservation and slide placeholders/headings. Current validation results are in `numerical_validation.json`.

## Biomarkers and rule-based profiles

Source cell 215 equations were retained and clearly qualified:

- SE proxy = 100×non-Wake/evaluated epochs, not independently measured time-in-bed sleep efficiency.
- WASO = 0.5×Wake epochs between first and last sleep; trailing Wake excluded; no sleep returns 0.
- N3 percentage = 100×N3/all evaluated epochs including Wake.
- SFI = transitions from N2/N3/REM to Wake/N1 divided by non-Wake hours; no sleep returns 0. This is a coarse stage-transition proxy, not EEG micro-arousal scoring.

EDF lights-off/on markers exist and their intervals are recorded in `lights_interval_audit.json`. They are not the denominator used by source biomarkers. No independent bed-entry/exit log exists. Recording/evaluated duration is therefore explicitly labelled a proxy instead of silently treated as time in bed.

Risk flags: SE<75%, WASO>60 min, N3<10%, SFI>10/sleep hour. Precedence: High if ≥3 flags OR SE<65% OR SFI>15; otherwise Mild if ≥1 flag; otherwise Healthy. Strict inequalities match the code. Original rules did not handle missing values explicitly; the new evaluator returns Unclassified for nonfinite/missing inputs rather than incorrectly labelling them Healthy. No final subject has missing values. Rule thresholds are research code, not clinically validated diagnostic cutoffs.

Ground-truth, raw and decoded biomarkers occupy separately labelled source rows. Slide 21 uses only decoded labels. SN009/SN001 are Healthy; SN004/SN022 Mild Risk. Decoded risk agreement with ground truth is only 2/4, explicitly shown. `biomarker_validation.csv` provides differences for every measure; risk agreement is not inferred from matching category distributions.

## Literature verification

Primary papers were consulted; no secondary blog metrics were used:

1. SeqSleepNet (2019), DOI 10.1109/TNSRE.2019.2896659, original manuscript https://arxiv.org/html/1809.10932, Sections II/V-A and Table II: MASS 200 subjects, EEG C4-A1+EOG+EMG, 20-fold subject CV (180/10/10 train/val/test), accuracy 87.1%, macro F1 83.3%, kappa 0.815.
2. DeepSleepNet (2017), DOI 10.1109/TNSRE.2017.2721116, https://arxiv.org/pdf/1703.04046, Tables III/IV: Sleep-EDF 20 subjects, Fpz-Cz EEG, 20-fold subject CV, accuracy 82.0%, macro F1 76.9%, kappa 0.76.
3. Official HMC dataset v1.1, https://physionet.org/content/hmc-sleep-staging/1.1/, DOI 10.13026/t79q-fr32; dataset paper DOI 10.1371/journal.pone.0256111.

Slide 41 includes two external studies plus this project's raw condition. Different datasets, modalities and protocols are conspicuously labelled; this is contextual literature, not a like-for-like leaderboard or state-of-the-art claim. Full protocols, reference locations and DOI links are in literature artifacts.

## Presentation changes and visual quality control

All 41 slides were modified, including provenance notes on retained cover/closing slides. `slide_source_manifest.json` lists each slide's artifact sources. Main changes:

- 1–4: verified owner-supplied metadata, implemented scope/objectives, actual split/counts/channels and explicit SN001 repair; simplified split geometry.
- 5–10: genuine EEG pair, proportional verified training counts, actual hybrid architecture/component roles, real uncertainty analysis, recovered training curves and exact settings. No GPU guessed.
- 11–18: one-run final metrics, raw confusion/class reports, genuine calibration, source-derived decoder/transition matrix and real SN009 hypnogram; replaced all provisional smoothing numbers.
- 19–22: qualified source equations, strict rules/precedence/units, four genuine profiles, visible risk disagreement and correct end-to-end arrows.
- 23–27: actual completion status, evidence-based limitations/future work, real system output and restrained numerical conclusion.
- 28–31: retained closing/divider design, repaired narrow closing text, full actual model/configuration and classification report.
- 32: supported raw-model confusion counts. 33: unsupported self-calibrated slide renamed Soft-Viterbi confusion matrix rather than fabricating an evaluation condition.
- 34–41: actual risk-coverage/reliability, exact weights/hyperparameters/formulas/Viterbi details, three additional real hypnograms and sourced literature.

Deck changes were applied by `complete_presentation.py` to the existing presentation's slide objects. Matplotlib plots come from `generate_presentation_artifacts.py`. No screenshots, mock sequences, synthetic EEG or generated illustrative data were used. Exported PNGs meet the requested high-resolution standard. All graph classes use Wake,N1,N2,N3,REM; hypnogram vertical order is Wake,REM,N1,N2,N3.

Native Windows PowerPoint COM was used to open and render all slides at 1920×1080 and export a PDF. This also exercises PowerPoint's actual layout engine. Original and final decks were rendered. All 41 final slides were inspected through seven contact sheets, with the specifically requested slides checked at full resolution. Layout repairs addressed title retention, body-box height, appendix dark-background contrast, cover/closing narrow text, training labels, risk-table wrapping and architecture arrow direction. Slides 10,15,21,30,35,40 have a clear title band; slide 4 geometry is simplified, slide 20 words stay intact, slide 25 uses wider readable cards. A final rerender was checked after repairs. PowerPoint text and table cell bounding boxes were exported for clipping checks. Final visual-validation details are in `visual_validation.json`.

Commands used for artifact generation and validation:

```bash
/tmp/ppt-venv/bin/python ppt_artifacts/generate_presentation_artifacts.py
/tmp/ppt-venv/bin/python ppt_artifacts/complete_presentation.py
/tmp/ppt-venv/bin/python ppt_artifacts/validate_results.py
```

Renderer:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File 'C:\Users\Rikin Parekh\AntiGravity\EEG-Sleep-Classification\ppt_artifacts\render_presentation.ps1' -PresentationPath 'C:\Users\Rikin Parekh\AntiGravity\EEG-Sleep-Classification\final_sleep_stage_project_presentation.pptx' -OutputDirectory 'C:\Users\Rikin Parekh\AntiGravity\EEG-Sleep-Classification\ppt_artifacts\rendered_slides'
```

CLI sessions were tested using `/home/rikin_parekh/.venvs/colab-cli/bin/colab --auth oauth2 sessions`; Drive/dataset/model access was verified via `remote_repository_probe.py` and `remote_signal_audit.py`. Their command outputs are saved in matching logs. An initial preflight timed out while another diagnostic was busy; the local hung CLI process was stopped without restarting the shared kernel. A transient Drive disconnection was remounted with the user's existing authorization; a transient download DNS issue was retried. None changed original notebook files or model inputs. Data/export archives were transferred from the runtime and extracted; copied checkpoint and repaired input hashes were verified. Credentials and temporary connection state were not published.

## Acceptance and remaining limits

Final machine-readable status and all acceptance checks are in `final_results.json`, `numerical_validation.json` and `visual_validation.json`. Original backup is exact; notebook preservation is hash-verified; all 41 slides are present; no specified placeholders remain; final results reconcile; raw/decoded epoch identity is exact; source rules/equations are reproduced; literature citations are included; slides were rendered by PowerPoint and visually repaired.

Remaining scientific limitations are preserved rather than filled with plausible values: four test recordings, no independent person-ID mapping, no external/cross-dataset validation, previously reused notebook test records, unknown final training hardware/global RNG provenance, weak uncertainty error discrimination, uncalibrated evidential probabilities, non-clinically-validated profile thresholds, and recording-duration biomarker proxies. This deliverable verifies a reproducible research pipeline; it does not claim a newly blinded or clinically validated experiment.

Final verification: 218 independent checks passed; 486 text/table cells measured with no overflow above 2 pt tolerance; all 41 native PowerPoint renders inspected. Generated artifact count: 200 (includes renders/scripts/logs/evidence). Final PPTX SHA256: `07d00b7584beb74d4373afa53a9ff9d27c91a3ea02766416cf13628e2694c91c`.
