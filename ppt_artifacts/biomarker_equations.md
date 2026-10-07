# Exact implemented research biomarkers

Source: original notebook cell 215 (zero-based); reproduced in evaluate_authoritative_run.py.
Let N be evaluated 30-second epochs, z_t the stage (0=Wake,1=N1,2=N2,3=N3,4=REM).
Let n_sleep = sum(1[z_t != 0]), T_sleep_min = n_sleep / 2, and T_eval_min = N / 2.

- SE (%) = 100 * n_sleep / N. This is evaluated-recording efficiency, not verified time-in-bed efficiency.
- WASO (min) = 0.5 * sum(1[z_t = 0], t from first to last non-Wake epoch inclusive).
  Trailing Wake after the final sleep epoch is excluded by this source definition.
  If no sleep occurs, the source returns 0 minutes; this should not be interpreted as good sleep.
- N3 (%) = 100 * sum(1[z_t = 3]) / N. The denominator is all evaluated epochs, not total sleep time.
- SFI (transitions/sleep hour) = count(z_t in {N2,N3,REM} AND z_(t+1) in {Wake,N1}) / (n_sleep / 120).
  This is a coarse stage-transition proxy, not EEG micro-arousal scoring. The source returns 0 if no sleep.
  New evaluation guards missing/nonfinite risk inputs; no zero-sleep subject occurs in this run.

Raw, smoothed and ground-truth values are in separate source rows. No mixing of label sources.
All authoritative test sequences were reconstructed/verified as contiguous before biomarkers were used.
Lights-off/on annotations provide a lights interval (lights_interval_audit.json), but source biomarkers
use evaluated-epoch duration. NPZ arrays have no time-in-bed field or independently verified bed-entry log.
