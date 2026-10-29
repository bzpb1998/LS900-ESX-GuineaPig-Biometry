# V5 experimental model (2026-10-16)

The V5 model developed on 2026-10-16 is now the default in the v0.2.0 native
desktop release (2026-10-29). The historical V4/v0.1.0 release is retained.
Shipping V5 in a usable application does not change its evidence status:
it remains an incremental research candidate pending new-animal prospective
validation, not a uniformly superior replacement established externally.

## What changed

- The retinal input is a median of amplitude-normalized, instrument-accepted,
  non-saturated raw A-scans, rather than the 75th percentile of processed scans.
- Candidate-pair features add wider local waveform context and raw-scan support.
  Training targets emphasize the ILM endpoint; no retinal manual cursor or
  reference AL is used during inference.
- All eyes and timepoints of the same numeric animal ID are grouped in training
  cross-validation. Fold-specific scaling and distance calibration use only
  that fold's training animals. A nested grouped development estimate is also
  saved in the model metadata, distinct from tuning estimates.
- An unavailable backup peak selector now requests review, rather than
  silently receiving the default high heuristic quality label.
- CCT calibration, AD/LT inference and lens gating are carried forward from the
  same 60-eye V4 development set. No new improvement is claimed for these parts.

## Evaluation and limitations

Training used 60 eyes from 30 animal-timepoints / 23 unique animals. Of the
historical 48 evaluation eyes, 28 eyes from 10 animals have no animal IDs in
training; the other 20 eyes are overlapping-animal historical review records.
All evaluation references had already been revealed during V4 research; the
failure modes were known before V5 development. V5 predictions were saved and
hashed before this run's reference comparison, but this is **retrospective
evaluation, not a new blinded or prospective test**.

| AL metric | V4, same 28 eyes | V5, same 28 eyes | V4, all 48 | V5, all 48 |
| --- | ---: | ---: | ---: | ---: |
| MAE (mm) | 0.03355 | 0.02893 | 0.02951 | 0.02471 |
| Within 0.05 mm | 24/28 | 23/28 | 42/48 | 43/48 |
| Within 0.10 mm | 25/28 | 26/28 | 45/48 | 46/48 |
| Maximum absolute error (mm) | 0.17598 | 0.11556 | 0.17598 | 0.11556 |

Lower average error did not improve every tolerance metric. Heuristic quality
labels still miss some large errors; they are not calibrated probabilities.
Weak ILM boundaries and retinal pathology require review. Manual EyeSuite
values are an operational reference, not independently proven anatomical truth.

## Use from source

Use the pinned environment and installable package described in
[REPRODUCIBILITY.md](REPRODUCIBILITY.md). The default command is now:

```powershell
ls900-biometry --input "D:\your_esx_folder" --output "D:\your_output\LS900_results.xlsx"
```

No data are uploaded. Results use the existing compact two-sheet Excel layout.
No before/after option is required. The V5 model is in
`src/ls900_biometry/models/v5_model.json`; the V4 model is retained separately.

## Reproducibility and data boundaries

The public tree contains inference, ranker-fitting primitives, parameters,
documentation, synthetic tests and the empty report template. It contains no
raw ESX, reference tables, research screenshots, patient records or vendor
software. Dataset extraction, training manifests, feature caches, per-eye
comparisons and paper figures stay in the local research project. The code
primitives document the numerical fit; access to the original approved
research data is a separate matter.
