# Sleep Studio

Windows Electron workspace for the current N1/N2 spectral refinement and descriptive sleep-health reference pipeline.

```powershell
cd "C:\Users\Rikin Parekh\AntiGravity\EEG-Sleep-Classification\gui"
npm install
npm start
```

`start.bat` also launches the app. Windows runs Electron; Ubuntu WSL runs the existing Colab CLI, normally `~/.venvs/colab-cli/bin/colab`. Use Connection & settings to discover or connect a runtime, mount Drive and verify the checkpoint/dataset paths. Package checks now include SciPy and scikit-learn.

Offline Overview and Results display the independently reproduced `HMC-N1N2-20261007` run: 3,109 stored test epochs, 55.45% raw accuracy, 59.34% refined accuracy. Choose SN001, SN004, SN009 or SN022 in Results. The Sleep profile tab shows four domains, the overall deviation level, architecture, all nine spectral features, z-scores and reference P10/P90 values.

## Running an analysis

1. In Connection & settings, connect your existing Colab runtime and mounted project Drive. Connecting automatically installs missing runtime packages (including MNE), retains existing versions, and checks the checkpoint/dataset paths. Wait for “Your runtime is ready” before running. “Install missing packages” retries package setup if needed.
2. Data & Run accepts project NPZ examples, Drive files or Windows EDF/NPZ imports.
3. N1/N2 spectral refinement defaults on. Its fitted scaler/coefficients and training reference are checkpoint-specific and are uploaded with each isolated run. A different checkpoint needs its own refiner; disable refinement for raw inference with that checkpoint.
4. Project examples use the notebook’s stored NPZ sequences, with an explicit continuity assumption displayed in the interface. Project SHA256 hashes are checked against the audit. They do not silently reconstruct SN001 into a different experiment.
5. Imported NPZs need confirmation of channel order/preprocessing and a continuity assumption if timestamps are absent. Unknown timing or gaps makes SOL/WASO/fragmentation unavailable; incomplete domains produce an unavailable overall profile.
6. Results include hypnograms, original evidential probabilities/uncertainty, raw/refined evaluations, descriptive profiles, artifacts and PDF/JSON/CSV/ZIP exports.

The Transformer is retained. Ground truth is used only for evaluation and training subset construction; test routing depends only on the predicted N1/N2 label. Nine EEG features use Delta 0.5-4, Theta 4-8, Alpha 8-12, Sigma 12-16, Beta 16-30 Hz, plus four band/Delta ratios. Welch uses 400 samples and 200 overlap at 100 Hz. Relative powers use 0.5-30 Hz total power, average channel powers first, and include all epochs in recording-level spectral means.

## Architecture and profiling

TST excludes Wake. Efficiency is TST / evaluated recording duration. N1/N2/N3/REM percentages use TST. SOL starts at the evaluated sequence origin. WASO includes terminal Wake after sleep onset; REM latency starts at sleep onset. Awakenings count non-Wake → Wake. Fragmentation counts all stage transitions per TST hour and is project-defined.

Reference mean, sample SD (ddof=1), median, P10 and P90 come from 16 training recordings only. Bounds are inclusive. 0/1/2/3–4 deviated domains give Within Reference/Mild/Moderate/High Deviation. EEG features, REM latency and total transition count are available for comparison but are not independently counted as extra domain flags.

HMC is a heterogeneous clinical population, not a healthy normative cohort. LOW/NORMAL/HIGH indicate dataset-relative intervals. Mild/Moderate/High Deviation count deviated domains; they are not validated clinical severity, disease-risk predictions, or diagnoses. The stored SN001 input covers 190 epochs (95 minutes), so its profile describes a segment. NPZ timing assumes contiguous epochs; whole-night and lights-out timing are not independently established.

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
