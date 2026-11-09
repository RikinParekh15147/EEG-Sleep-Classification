# Manuscript evidence map

All paths below are relative to the repository root. Current experiment: **HMC-N1N2-20261007**. The primary evidence directory is `refinement_artifacts/verified/`; similarly named files in `ppt_artifacts/` describe a historical experiment and must not replace current evidence.

| Manuscript content | Existing source |
| --- | --- |
| Team names, affiliation, mentor | `README.md` |
| Split sizes and recording membership | `refinement_artifacts/verified/split_summary.json` |
| Checkpoint identity, headline metrics, change counts, limits | `refinement_artifacts/verified/final_results.json` |
| Raw/refined aggregate metrics | `refinement_artifacts/verified/overall_metrics.json` |
| Per-stage test metrics/support | `refinement_artifacts/verified/classification_report.csv`, `refined_classification_report.csv` |
| Confusion counts | `refinement_artifacts/verified/confusion_matrix_counts.csv`, `refined_confusion_matrix_counts.csv` |
| Epoch-level labels and prediction changes | `refinement_artifacts/verified/test_epoch_predictions.csv` |
| Preprocessing and timing assumptions | `refinement_artifacts/verified/preprocessing_config.json` |
| Architecture and saved training configuration | `refinement_artifacts/verified/hyperparameters.json`, `model_layers.csv` |
| Refiner scaling, coefficients, training counts, checkpoint hash | `refinement_artifacts/verified/refinement_model.json` |
| Exact fitting and inference conversion | `refinement_artifacts/reproduce.py` |
| Desktop spectral equations, architecture metrics, missing-data behavior | `gui/pipeline/refinement.py` |
| Reference values and domain rules | `refinement_artifacts/verified/reference_stats.json`, `profile_rules.json` |
| Recording architecture and profile values | `refinement_artifacts/verified/subject_profiles.json`, `subject_biomarkers.csv` |
| Environment versions | `refinement_artifacts/verified/evaluation_environment.json` |
| Existing reproduction status | `refinement_artifacts/refinement_completion_audit.md` |
| Software setup, interfaces, imports, exports | `gui/README.md`, `gui/pipeline/worker.py` |
| Proposed future architecture | `README.md`, `docs/multistage_pipeline_proposal.md` |

The three manuscript PNGs are byte-for-byte copies of files with the same names in `refinement_artifacts/verified/`. The figure captions describe their existing contents. `verify_sources.py` checks copy integrity.

External citations were checked against the HMC PhysioNet dataset page and the DeepSleepNet and SeqSleepNet arXiv records. The PhysioNet platform citation follows the citation supplied by the dataset page on the documentation date. These sources provide background; all project performance numbers come from repository artifacts.

## Interpretation rules

- Report the 3,109-epoch stored-NPZ experiment separately from the 3,773-epoch historical EDF/Soft-Viterbi experiment.
- Distinguish recording-disjoint partitions from unverified person-level independence.
- Report metric improvements in **percentage points**, calculating gains before rounding.
- Refiner training uses true and predicted N1/N2 labels; test routing uses predicted labels alone.
- Preserving baseline Wake/N3/REM predictions does not mean every epoch whose true label is one of those stages bypasses refinement.
- N1/N2 relabeling cannot change total sleep time or Wake assignments. It can change stage composition and transition counts.
- Treat original evidential uncertainty separately from refined-label confidence and reference deviation.
- Use evaluated-window efficiency, not an independently verified time-in-bed efficiency.
- Qualify SN001 as 190 epochs / 95 minutes and all NPZ timing as assuming continuity.
- Describe training-reference intervals and domain counts as descriptive comparisons to this clinical cohort.
- Keep planned experts, temporal CNNs, calibration, and external validation explicitly prospective.

The documentation build verifies internal artifact consistency and manuscript rendering. It does not rerun signal processing, retrain models, or independently establish clinical validity.

Welch's spectral estimator is attributed to the original 1967 paper (DOI: `10.1109/TAU.1967.1161901`); the scaler/logistic-regression implementation is attributed to the scikit-learn paper in JMLR (2011). See `ORIGINALITY.md` for the scope of the prose and attribution review; no institutional similarity score is available.
