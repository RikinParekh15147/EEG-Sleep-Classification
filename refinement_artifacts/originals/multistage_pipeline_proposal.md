# Proposed multistage, multi-model sleep pipeline

This is a future research design, not an implemented or evaluated experiment. The existing model, data and results are unchanged.

## Why this design fits the evidence

The authoritative current run has raw N1 F1 0.366 and N2 recall 44.00%. Its uncertainty error-detection AUROC is only 0.580. These observations support testing task specialization and learned inter-epoch context. They do not prove that a cascade or uncertainty-based routing will improve accuracy. The current BiLSTM operates on downsampled samples inside one EEG epoch, whereas the proposed temporal model would operate across consecutive epochs.

A small cohort makes a large ensemble prone to overfitting. Start with two compact expert models and retain the existing five-stage model as a comparison. Add the temporal component only after a controlled ablation demonstrates benefit.

## Stages and separate models

1. **Input quality checks:** verify channel presence, sampling, epoch alignment, finite values and obvious flat/clipped segments. Flag suspect epochs. Any learned artifact detector would require suitable quality labels and is not assumed available. Preserve timestamps and recording boundaries.
2. **Model A — coarse CNN:** a separate compact 1D CNN outputs probabilities for Wake, REM and NREM. Supervised targets merge the original N1/N2/N3 labels into NREM. EEG remains the initial input modality.
3. **Model B — NREM expert:** a separately trained compact CNN or residual CNN distinguishes N1/N2/N3, trained only on training-set NREM epochs. Use training-only class weights. Evaluate its scores on every inference epoch and apply soft NREM weighting, rather than hard-routing only epochs guessed as NREM.
4. **Probability composition and baseline fusion:** let g be the normalized coarse probabilities and h the conditional NREM probabilities. Construct q=[gWake, gNREM*hN1, gNREM*hN2, gNREM*hN3, gREM]. The entries sum to one. Optionally combine q with p from the current five-stage SCFormer-U model: r=λq+(1−λ)p. Select λ on development/validation data only; no value or benefit is asserted now. This soft composition limits irreversible early-stage errors, but conditional expert errors and poor coarse probabilities can still hurt.
5. **Model C — temporal convolutional network:** after the two-model experiment, test a small TCN on consecutive epoch probabilities/logits and optionally validated confidence features. It emits a refined five-class distribution using inter-epoch context. An offline bidirectional context version is compatible with retrospective scoring; an online deployment would require causal context and separate latency evaluation. Do not confuse this with the existing within-epoch BiLSTM.
6. **Calibration, optional decoding and profile:** fit final-output calibration using validation predictions. If fusion inputs also require calibration, fit that in the development procedure separately. Compare TCN alone, original weighted Viterbi alone and their combination; do not automatically stack refiners. Use training-only transitions and reset at each recording/gap. Derive biomarkers and research profiles with explicit denominators. A review/referral flag can use uncertainty only after its error discrimination and coverage trade-off are validated. No referral threshold is invented.

The slide depicts fusion/calibration as a compact bridge before the temporal model. Technically, experts may be calibrated before fusion, and the final temporal output must be calibrated separately before confidence/referral is interpreted. This distinction is specified here and in speaker notes.

## Validation strategy

- Keep every existing run artifact unchanged. The four current test recordings have already been reused in development, so they cannot become a newly blinded test by renaming them.
- Reserve a genuinely new locked recording/person cohort before new tuning; verify person identities when a mapping becomes available.
- Use grouped development folds for architecture and fusion selection. With limited data, favor fewer parameters and fewer tuning decisions.
- Train base experts on training folds only. To train the temporal/stacking component, produce out-of-fold base predictions so the refiner does not learn from artificially accurate in-sample expert outputs. Refit base experts on the development training partition after selection.
- Keep preprocessing statistics, class weights and transition fitting confined to the training partition. Preserve recording boundaries in both training windows and inference.
- Evaluate current flat model; coarse+NREM composition; composition+flat fusion; fusion+TCN; and original decoder alternatives on the same locked epochs.
- Report accuracy, balanced accuracy, macro F1, per-stage precision/recall/F1 (especially N1/N2), kappa, ECE, error-detection AUROC, risk-coverage, inference time and model size. Examine recording-level variability and uncertainty intervals using recording/subject resampling rather than treating epochs as independent subjects.
- Evaluate biomarker error against separately calculated ground truth, and research category agreement. Increased epoch accuracy does not guarantee more faithful health profiles.

## Later extensions

Only after the EEG hierarchy works, investigate EOG/EMG specialist branches if suitable aligned channels are genuinely available. Missing-modality behavior requires explicit testing. External dataset validation and clinically reviewed biomarker denominators/thresholds remain separate requirements.

## Literature context and limits

The architecture above is our proposed engineering design, not attributed as the implementation of another paper. Relevant source material:

- Phan et al., SeqSleepNet (2019): https://arxiv.org/html/1809.10932; DOI 10.1109/TNSRE.2019.2896659. Sequence context is part of its approach; its published modality/dataset/protocol differ from this project.
- Supratak et al., DeepSleepNet (2017): https://arxiv.org/pdf/1703.04046; DOI 10.1109/TNSRE.2017.2721116. Current deck comparison uses the already verified Sleep-EDF figures.
- Guillot and Thorey, RobustSleepNet (2021): https://arxiv.org/abs/2101.02452. The authors evaluated heterogeneous datasets using a leave-one-dataset-out protocol. This supports including cross-dataset validation as a future requirement, not claiming comparable performance here.
- Perslev et al., U-Sleep (2021): https://www.nature.com/articles/s41746-021-00440-5. Provides broader sleep-staging context. No U-Sleep metric was transplanted into the project results.

A cascaded-LSTM publisher search result was found, but the full page returned HTTP 403. Its detailed architecture/metrics were not used as verified evidence.
