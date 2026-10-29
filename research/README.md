# V5 ranker reproducibility

`ranker_training.py` exposes the exact weighted ridge fit and numeric-animal
grouped validation primitives. Build features with
`ls900_biometry.v5.extract_features`; supply ILM/RPE annotations separately and
never load reference annotations during inference. This directory includes no
raw data, manual labels or identifiers from human patients.

The development search compared three aggregation modes (`processed75`,
`raw50`, `raw75`), 108 vs 202 feature columns, RPE target weights 0 vs 1,
and ridge strengths 0.1, 1, 10, plus a hard-target legacy comparator.
Soft targets use a 40-sample Gaussian. Each eye's positive and negative
candidate weights are balanced. The selected configuration was `raw50`,
202 features, RPE weight 0, ridge 0.1, without a selector bias correction.

Hyperparameters were selected by training-only grouped leave-one-animal-out
RMSE, then MAE/P90. A five-outer/four-inner grouped nested development estimate
was also produced using random seed 20261016. The selected-model training
estimate (MAE 0.01751 mm) is optimistic relative to the nested estimate
(MAE 0.02252 mm); neither is the independent-test result. Fit the coordinate
calibrations inside each training fold when replicating the complete estimate.

The model JSON holds the final calibration/coefficients. The local research
project retains the extraction and run manifests and frozen historical inputs.
Using the public code requires your own approved inputs; there is no automatic
download of research data.
