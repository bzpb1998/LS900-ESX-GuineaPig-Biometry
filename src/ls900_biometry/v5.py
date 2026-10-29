"""Experimental animal-grouped retinal ranker; raw inputs stay on the host.

The V4 implementation remains available as a comparator. No manual retinal
cursor or EyeSuite length field is used by this inference module.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import math

import numpy as np

from .esx_reader import EsxRecord, read_esx
from . import inference as legacy


@dataclass
class RetinalFeatures:
    signal: np.ndarray
    candidates: np.ndarray
    pairs: np.ndarray
    matrix: np.ndarray
    front: float
    back: float
    support: np.ndarray
    n_scans: int
    mode: str


def extract_features(record: EsxRecord, eye: str, mode: str = "processed75") -> RetinalFeatures:
    measurements = [m for m in record.measurements
                    if m.eye == eye and not m.is_placeholder and len(m.scan)]
    if not measurements:
        raise ValueError("No valid processed scans")
    length = min(len(m.scan) for m in measurements)
    raw = [s[:length] for m in measurements for s in m.raw_ascans if len(s) >= length]
    raw_array = np.stack(raw) if raw else np.stack([m.scan[:length] for m in measurements])
    if mode == "processed75":
        aggregate = np.percentile(np.stack([m.scan[:length] for m in measurements]), 75, axis=0)
    elif mode in ("raw50", "raw75"):
        # Equalise scan amplitudes, so one unusually bright scan cannot
        # manufacture the dominant retinal layer in an aggregate.
        normalizers = np.maximum(np.max(raw_array[:, 13000:17000], axis=1), 1e-8)
        normalized = raw_array / normalizers[:, None]
        aggregate = np.percentile(normalized, 50 if mode == "raw50" else 75, axis=0)
    else:
        raise ValueError(mode)
    signal = legacy._smooth(aggregate, 3.0)
    peak_scale = max(float(np.max(signal[13000:17000])), 1e-8)
    candidates = legacy._local_peaks(signal, max(0.0001, .008 * peak_scale), distance=18)
    candidates = candidates[(candidates >= 13000) & (candidates <= 17000)]
    if len(candidates) > 60:
        candidates = np.sort(candidates[np.argsort(signal[candidates])[-60:]])
    base = legacy._candidate_features(signal, candidates)
    pairs, old_matrix = legacy._pair_matrix(signal, candidates, base)
    if not len(pairs):
        raise ValueError("No plausible retinal peak pair")
    raw_region = raw_array[:, 13000:17000]
    normalizers = np.maximum(raw_region.max(axis=1), 1e-8)
    normalized_raw = raw_array / normalizers[:, None]
    offsets = np.arange(-600, 1001, 40)
    extras = []
    support = []
    for position in candidates:
        local = normalized_raw[:, position-35:position+36]
        local_max = local.max(axis=1)
        noise = np.median(normalized_raw[:, 13000:17000], axis=1)
        persistence = float(np.mean(local_max > np.maximum(.03, noise * 4)))
        support.append(persistence)
        shape = signal[np.clip(position + offsets, 0, length-1)] / peak_scale
        local_positions = np.argmax(local, axis=1) - 35
        extra = np.r_[shape, persistence, np.median(local_max),
                      np.quantile(local_max, .25), np.quantile(local_max, .75),
                      np.mean(np.abs(local_positions) <= 20),
                      np.std(local_positions)/35]
        extras.append(extra)
    lookup = {int(c): i for i, c in enumerate(candidates)}
    extended = np.stack([np.r_[extras[lookup[int(a)]], extras[lookup[int(b)]]]
                         for a, b in pairs])
    front = float(np.median([m.cursors.get(0, math.nan) for m in measurements]))
    back = float(np.median([m.cursors.get(1, math.nan) for m in measurements]))
    return RetinalFeatures(signal, candidates, pairs,
                           np.column_stack([old_matrix, extended]), front, back,
                           np.asarray(support), len(raw), mode)


def score_features(features: RetinalFeatures, ranker: dict) -> dict:
    dimension = int(ranker["feature_count"])
    x = features.matrix[:, :dimension]
    mean = np.asarray(ranker["feature_mean"])
    scale = np.asarray(ranker["feature_scale"])
    scores = np.column_stack([np.ones(len(x)), (x-mean)/scale]) @ np.asarray(ranker["coefficient"])
    best = int(np.argmax(scores))
    ilm, rpe = map(int, features.pairs[best])
    alternatives = scores[np.abs(features.pairs[:, 0]-ilm) > 80]
    margin = float(scores[best]-np.max(alternatives)) if len(alternatives) else math.inf
    support = float(features.support[np.flatnonzero(features.candidates == ilm)[0]])
    alternate_ilm, alternate_rpe = legacy._simple_retina_pair(features.candidates, features.signal)
    disagreement = abs(ilm-alternate_ilm) if alternate_ilm >= 0 else math.nan
    return {"ilm": ilm, "rpe": rpe, "margin": margin, "support": support,
            "score": float(scores[best]), "backup_ilm": alternate_ilm,
            "backup_rpe": alternate_rpe, "disagreement": disagreement}


def predict_retina(record: EsxRecord, eye: str, model: dict) -> dict:
    f = extract_features(record, eye, model["retina"]["aggregation"])
    p = score_features(f, model["retina"])
    calibration = model["calibration"]
    convert = lambda metric, delta: float(calibration[metric]["slope_mm_per_sample"])*delta + float(calibration[metric]["intercept_mm"])
    reasons = []
    gate = model["retina"]["quality_gate"]
    if not np.isfinite(p["disagreement"]):
        reasons.append("backup_selector_unavailable")
    elif p["disagreement"] > gate["maximum_disagreement_samples"]:
        reasons.append("retinal_selectors_disagree")
    if p["margin"] < gate["minimum_margin"]:
        reasons.append("ambiguous_retinal_layers")
    if p["support"] < gate["minimum_raw_support"]:
        reasons.append("weak_raw_scan_support")
    if not np.isfinite(f.front):
        reasons.append("cornea_front_missing")
    return {"predicted_AL_mm": convert("AL_mm", p["ilm"]-f.front),
            "predicted_CCT_mm": convert("CCT_mm", f.back-f.front),
            "predicted_RT_mm": convert("RT_mm", p["rpe"]-p["ilm"]),
            "AL_quality": "review" if reasons else "high",
            "AL_status": "predicted_review_required" if reasons else "predicted",
            "AL_gate_reasons": ";".join(reasons), "CCT_quality": "high",
            "RT_quality": "exploratory", "cornea_front_position": f.front,
            "cornea_back_position": f.back, "predicted_ILM_position": p["ilm"],
            "predicted_RPE_position": p["rpe"], "retina_margin": p["margin"],
            "retina_raw_support": p["support"], "n_retinal_raw_scans": f.n_scans,
            "baseline_ILM_position": p["backup_ilm"],
            "selector_disagreement_samples": p["disagreement"]}


def analyze_esx(path: str | Path, model_path: str | Path) -> list[dict]:
    model = json.loads(Path(model_path).read_text(encoding="utf-8"))
    record = read_esx(path)
    rows = []
    for eye in ("OD", "OS"):
        retinal = predict_retina(record, eye, model)
        # The lens module is deliberately carried forward unchanged; the
        # release notes and validation report identify this explicitly.
        lens = legacy._lens_prediction(record, eye, retinal["cornea_back_position"])
        rows.append({"animal_id": record.animal_id, "eye": eye, **retinal, **lens,
                     "algorithm_version": model["version"], "source_file": record.path.name})
    return rows
