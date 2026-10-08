# N1/N2 refinement validation, 8 October 2026

The active baseline is `HMC-N1N2-20261007`, with 3,109 stored test epochs. The previous validation is preserved in `../../refinement_artifacts/originals/gui-validation.md`.

| Check | Result |
| --- | --- |
| Windows production build | TypeScript and Vite passed |
| Node backend tests | 16 passed, including missing-package installation, connection serialization, and cancellation during shutdown |
| Ubuntu numerical and terminal authorization tests | 14 passed |
| Windows Chrome UI tests | 4 passed, including all four profiles and 21 comparison rows |
| Native Windows Electron | Loaded all 3,109 epochs; offline Run opens connection setup; selection, navigation, EEG chart and PDF export passed |
| Windows to Ubuntu WSL | Distribution discovery and Python bridge passed |
| Live GUI worker in Colab | All 901 SN009 raw and refined predictions match the independently reproduced baseline; Mild Deviation profile and ZIP transfer passed |
| Independent notebook reproduction | All 24 stored inputs evaluated; training-only refiner and reference rebuilt; notebook metrics and reference statistics match |

The local implementation reproduces all 3,109 refiner decisions and every architecture value for the 12 ground-truth/raw/refined test profiles. Tests cover terminal Wake in WASO, TST denominators, gaps, unknown continuity, zero sleep, missing REM, boundary equality, zero reference SD, path confinement and report escaping.

The verified accuracy is 55.45% before refinement and 59.34% afterward. Macro F1 is 57.42% and 59.51%. The refiner retains Transformer predictions of Wake, N3 and REM. The original evidential probabilities and uncertainty are not recalibrated by label refinement.

SN001 contains 190 stored epochs, or 95 minutes. This experiment is distinct from the archived reconstruction of SN001 to 854 epochs and 3,773 total test epochs. HMC reference comparisons are descriptive and do not establish healthy norms, medical severity, disease risk or diagnoses.

Run `npm run build`, `npm test`, `npm run test:ui` and `npm run test:desktop` in `gui/`. Run `python3 -m unittest discover -s tests -p 'test_*.py'` from `gui/` in Ubuntu. `node scripts/smoke-worker.cjs` needs the current audit runtime and mounted Drive, or a session specified by `SLEEP_COLAB_SESSION`.

No full Transformer retraining or full EDF preprocessing job was needed for this refinement update. Live EDF ingestion retains its previous checks; the current live worker verification used the actual stored SN009 NPZ.

## Connection regression fix, 8 October 2026

Connection now installs missing runtime packages automatically, preserves existing installed versions, and probes the runtime again before marking it ready. Package-install failures remain visible and release the connection controls. Concurrent connection operations are rejected, concurrent bridge startup is shared, and closing the app cancels pending startup and IPC requests without a misleading connection error. The Windows startup/build scripts invoke Node tools directly without `shell: true`.

The production build, 16 Node tests, four browser checks and native Electron checks passed. Live connection through the same Service/WSL bridge reached `ready` on `eeg-refinement-audit`: Drive, checkpoint, processed data and raw data were present; MNE 1.13.2 and the other required packages were installed. The selected `eeg-sleep-studio-test` T4 expired during verification; the audit runtime remained active. Session availability can change after these checks. `node scripts/check-runtime.cjs --session eeg-refinement-audit` verifies an existing named runtime without changing desktop settings or allocating another runtime.
