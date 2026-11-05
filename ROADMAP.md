# Roadmap

This roadmap lists what exists today and what we plan next. Items under "Planned" are **not implemented or evaluated yet**.

## Current status

- Fast SCFormer-U five-class sleep stage classifier (retained checkpoint)
- N1/N2 spectral refinement (training-only scaler + logistic regression)
- Recording-level architecture metrics and training-reference profiles
- Sleep Studio desktop app with hypnograms and PDF/JSON/CSV/ZIP exports
- Reproducible experiment HMC-N1N2-20261007 (24 HMC recordings, 3,109 test epochs)

## Near term: make the project easy to use and trust

- [ ] Add a short quickstart and Colab badge so the experiment can be run in a few clicks
- [ ] Record a short demo of Sleep Studio for the README
- [ ] Label `good first issue` tasks for new contributors
- [ ] Add more unit tests for feature extraction and edge cases (missing data, gaps)
- [ ] Make the GUI runnable without a Colab connection for offline exploration

## Mid term: stronger evidence

- [ ] Cross-validation across recordings to check how stable the N1/N2 gain is
- [ ] Evaluation on an external dataset (for example Sleep-EDF) with the same locked protocol
- [ ] Calibration analysis of model probabilities and uncertainty
- [ ] EDF alignment and quality audit
- [ ] Report macro/class F1, calibration, latency, and errors in sleep measurements alongside accuracy

## Longer term: planned model extensions

- [ ] Multistage design: coarse Wake/REM/NREM classifier plus an NREM expert for N1/N2/N3, with composed, normalized probabilities
- [ ] Optional fusion with the retained baseline
- [ ] Temporal CNN for context across consecutive epochs
- [ ] Controlled ablations and a newly locked test cohort
- [ ] Possible aligned EOG/EMG specialists

## Out of scope for now

- Diagnosis, disease-risk prediction, or any clinical claims
- Replacing clinician review

## How to help

See [CONTRIBUTING.md](CONTRIBUTING.md). Pick an item above, open an issue to discuss it, and we will coordinate.
