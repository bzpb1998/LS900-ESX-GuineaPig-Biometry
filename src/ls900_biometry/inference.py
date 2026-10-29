"""Locked V4 inference for guinea-pig ocular biometry.

The implementation is deliberately self-contained so the local application
does not depend on the research/training notebooks or their absolute paths.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from typing import Any, Iterable

import numpy as np

from .esx_reader import EsxRecord, read_esx


MODEL_PATH = files("ls900_biometry").joinpath("models/v4_model.json")
with MODEL_PATH.open("r", encoding="utf-8") as handle:
    _MODEL: dict[str, Any] = json.load(handle)
MODEL_VERSION = str(_MODEL["version"])


@dataclass(slots=True)
class SurfaceScan:
    positions: np.ndarray
    features: np.ndarray


def _smooth(signal: np.ndarray, sigma: float) -> np.ndarray:
    radius = int(math.ceil(4 * sigma))
    x = np.arange(-radius, radius + 1, dtype=float)
    kernel = np.exp(-(x**2) / (2 * sigma**2))
    kernel /= kernel.sum()
    return np.convolve(signal, kernel, mode="same")


def _aggregate_eye(record: EsxRecord, eye: str) -> tuple[np.ndarray, dict[int, float]]:
    measurements = [
        item
        for item in record.measurements
        if item.eye == eye and not item.is_placeholder and len(item.scan)
    ]
    if not measurements:
        raise ValueError(f"{eye} 未找到有效的聚合扫描")
    length = min(len(item.scan) for item in measurements)
    scans = np.stack([item.scan[:length] for item in measurements])
    aggregate = np.percentile(scans, 75, axis=0)
    cursor_sets = [set(item.cursors) for item in measurements]
    cursor_ids = sorted(set.intersection(*cursor_sets)) if cursor_sets else []
    cursors = {
        element: float(np.median([item.cursors[element] for item in measurements]))
        for element in cursor_ids
    }
    return _smooth(aggregate, sigma=3.0), cursors


def _local_peaks(signal: np.ndarray, minimum_height: float, distance: int = 18) -> np.ndarray:
    candidates = np.flatnonzero(
        (signal[1:-1] > signal[:-2])
        & (signal[1:-1] >= signal[2:])
        & (signal[1:-1] >= minimum_height)
    ) + 1
    if not len(candidates):
        return candidates
    chosen: list[int] = []
    for position in candidates[np.argsort(signal[candidates])[::-1]]:
        if all(abs(int(position) - previous) >= distance for previous in chosen):
            chosen.append(int(position))
    return np.asarray(sorted(chosen), dtype=int)


def _candidate_features(signal: np.ndarray, candidates: np.ndarray) -> np.ndarray:
    region_start, region_stop = 13000, min(17000, len(signal))
    region = signal[region_start:region_stop]
    scale = max(float(np.max(region)), 1e-8)
    normalized = signal / scale
    active = np.flatnonzero(region >= 0.015 * scale)
    if len(active):
        active_start = region_start + int(active[0])
        active_stop = region_start + int(active[-1])
    else:
        active_start, active_stop = region_start, region_stop - 1
    global_peak = region_start + int(np.argmax(region))
    energy = np.maximum(region, 0)
    cumulative = np.cumsum(energy)
    energy_total = max(float(cumulative[-1]), 1e-8)

    offsets = np.arange(-200, 201, 10)
    rows: list[np.ndarray] = []
    for rank, position in enumerate(candidates):
        sample_positions = np.clip(position + offsets, 0, len(normalized) - 1)
        window = normalized[sample_positions]
        region_index = int(np.clip(position - region_start, 0, len(region) - 1))
        cdf = float(cumulative[region_index] / energy_total)
        base = np.asarray(
            [
                normalized[position],
                normalized[max(0, position - 20)],
                normalized[min(len(normalized) - 1, position + 20)],
                (position - active_start) / 1000.0,
                (active_stop - position) / 1000.0,
                (position - global_peak) / 1000.0,
                cdf,
                rank / max(1, len(candidates) - 1),
                (len(candidates) - rank - 1) / max(1, len(candidates) - 1),
            ],
            dtype=float,
        )
        rows.append(np.concatenate([base, window]))
    return np.stack(rows) if rows else np.empty((0, 50), dtype=float)


def _pair_matrix(
    signal: np.ndarray, candidates: np.ndarray, features: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    pairs: list[tuple[int, int]] = []
    rows: list[np.ndarray] = []
    region_scale = max(float(np.max(signal[13000:17000])), 1e-8)
    for i, ilm in enumerate(candidates):
        for j, rpe in enumerate(candidates):
            separation = int(rpe - ilm)
            if separation < 150 or separation > 460:
                continue
            between = signal[int(ilm) : int(rpe) + 1] / region_scale
            extra = np.asarray(
                [
                    separation / 300.0,
                    (separation / 300.0) ** 2,
                    float(between.mean()),
                    float(between.max()),
                    float(between.min()),
                    float(signal[int(ilm)] / region_scale),
                    float(signal[int(rpe)] / region_scale),
                    float((signal[int(rpe)] - signal[int(ilm)]) / region_scale),
                ]
            )
            rows.append(np.concatenate([features[i], features[j], extra]))
            pairs.append((int(ilm), int(rpe)))
    if not rows:
        return np.empty((0, 2), dtype=int), np.empty((0, 108), dtype=float)
    return np.asarray(pairs, dtype=int), np.stack(rows)


def _simple_retina_pair(candidates: np.ndarray, signal: np.ndarray) -> tuple[int, int]:
    allowed = candidates[(candidates >= 13500) & (candidates <= 16500)]
    if not len(allowed):
        return -1, -1
    rpe = int(allowed[np.argmax(signal[allowed])])
    ilm_candidates = allowed[(allowed >= rpe - 430) & (allowed <= rpe - 160)]
    if not len(ilm_candidates):
        return -1, rpe
    ilm = int(ilm_candidates[np.argmax(signal[ilm_candidates])])
    return ilm, rpe


def _calibrated(metric: str, sample_difference: float) -> float:
    payload = _MODEL["calibration"][metric]
    return float(payload["slope_mm_per_sample"]) * sample_difference + float(
        payload["intercept_mm"]
    )


def _retinal_prediction(record: EsxRecord, eye: str) -> dict[str, Any]:
    signal, cursors = _aggregate_eye(record, eye)
    region = signal[13000 : min(17000, len(signal))]
    if not len(region):
        raise ValueError(f"{eye} 扫描长度不足")
    minimum_height = max(0.03, 0.008 * float(np.max(region)))
    candidates = _local_peaks(signal, minimum_height, distance=18)
    candidates = candidates[(candidates >= 13000) & (candidates <= 17000)]
    cornea_front = float(cursors.get(0, math.nan))
    cornea_back = float(cursors.get(1, math.nan))
    cct = (
        _calibrated("CCT_mm", cornea_back - cornea_front)
        if np.isfinite(cornea_front) and np.isfinite(cornea_back)
        else math.nan
    )
    if len(candidates) < 2:
        return {
            "predicted_AL_mm": math.nan,
            "AL_quality": "review",
            "AL_status": "unmeasurable_no_retinal_candidates",
            "predicted_CCT_mm": cct,
            "CCT_quality": "high" if np.isfinite(cct) and 0.12 <= cct <= 0.30 else "review",
            "predicted_RT_mm": math.nan,
            "RT_quality": "exploratory",
            "cornea_front_position": cornea_front,
            "cornea_back_position": cornea_back,
        }

    features = _candidate_features(signal, candidates)
    pairs, matrix = _pair_matrix(signal, candidates, features)
    if not len(pairs):
        return {
            "predicted_AL_mm": math.nan,
            "AL_quality": "review",
            "AL_status": "unmeasurable_no_retinal_pair",
            "predicted_CCT_mm": cct,
            "CCT_quality": "high" if np.isfinite(cct) and 0.12 <= cct <= 0.30 else "review",
            "predicted_RT_mm": math.nan,
            "RT_quality": "exploratory",
            "cornea_front_position": cornea_front,
            "cornea_back_position": cornea_back,
        }

    retina = _MODEL["retina"]
    coefficient = np.asarray(retina["coefficient"], dtype=float)
    mean = np.asarray(retina["feature_mean"], dtype=float)
    scale = np.asarray(retina["feature_scale"], dtype=float)
    design = np.column_stack([np.ones(len(matrix)), (matrix - mean) / scale])
    scores = design @ coefficient
    ilm, rpe = map(int, pairs[int(np.argmax(scores))])
    baseline_ilm, baseline_rpe = _simple_retina_pair(candidates, signal)
    disagreement = abs(ilm - baseline_ilm) if baseline_ilm >= 0 else math.nan
    if np.isfinite(disagreement) and disagreement > 120:
        quality, status = "review", "predicted_review_required"
    elif np.isfinite(disagreement) and disagreement > 50:
        quality, status = "medium", "predicted"
    else:
        quality, status = "high", "predicted"
    al = (
        _calibrated("AL_mm", ilm - cornea_front)
        + float(retina["selector_bias_correction_mm"])
        if np.isfinite(cornea_front)
        else math.nan
    )
    return {
        "predicted_AL_mm": al,
        "AL_quality": quality,
        "AL_status": status,
        "predicted_CCT_mm": cct,
        "CCT_quality": "high" if np.isfinite(cct) and 0.12 <= cct <= 0.30 else "review",
        "predicted_RT_mm": _calibrated("RT_mm", rpe - ilm),
        "RT_quality": "exploratory",
        "cornea_front_position": cornea_front,
        "cornea_back_position": cornea_back,
        "predicted_ILM_position": ilm,
        "predicted_RPE_position": rpe,
        "baseline_ILM_position": baseline_ilm,
        "baseline_RPE_position": baseline_rpe,
        "selector_disagreement_samples": disagreement,
        "retina_selection_score": float(np.max(scores)),
    }


def _weighted_median(values: np.ndarray, weights: np.ndarray) -> float:
    order = np.argsort(values)
    values = values[order]
    weights = weights[order]
    cumulative = np.cumsum(weights)
    return float(values[int(np.searchsorted(cumulative, cumulative[-1] / 2.0))])


def _surface_scan(signal: np.ndarray, window: tuple[int, int]) -> SurfaceScan:
    start, stop = window
    region = signal[start:stop]
    scale = max(float(np.max(region)), 1e-8)
    threshold = max(1.0, 0.02 * scale)
    local = np.flatnonzero(
        (region[1:-1] > region[:-2])
        & (region[1:-1] >= region[2:])
        & (region[1:-1] >= threshold)
    ) + 1
    chosen: list[int] = []
    for position in local[np.argsort(region[local])[::-1]]:
        if all(abs(int(position) - previous) >= 14 for previous in chosen):
            chosen.append(int(position))
    candidates = np.asarray(sorted(start + position for position in chosen), dtype=int)
    if not len(candidates):
        candidates = np.asarray([start + int(np.argmax(region))], dtype=int)
    elif len(candidates) > 20:
        candidates = np.sort(candidates[np.argsort(signal[candidates])[-20:]])

    normalized = signal / scale
    amplitude_order = np.argsort(signal[candidates])[::-1]
    amplitude_rank = np.empty(len(candidates), dtype=float)
    amplitude_rank[amplitude_order] = np.arange(len(candidates), dtype=float)
    offsets = np.arange(-120, 121, 10)
    rows: list[np.ndarray] = []
    for index, position in enumerate(candidates):
        left = signal[max(start, position - 100) : position + 1]
        right = signal[position : min(stop, position + 101)]
        left_min = float(np.min(left)) if len(left) else float(signal[position])
        right_min = float(np.min(right)) if len(right) else float(signal[position])
        prominence = float(signal[position] - max(left_min, right_min))
        sample_positions = np.clip(position + offsets, 0, len(signal) - 1)
        neighbourhood = normalized[sample_positions]
        base = np.asarray(
            [
                (position - start) / max(1, stop - start),
                float(signal[position] / scale),
                float(signal[position] / 50.0),
                prominence / scale,
                amplitude_rank[index] / max(1, len(candidates) - 1),
                len(candidates) / 20.0,
                float(np.mean(left) / scale),
                float(np.mean(right) / scale),
                float((np.mean(right) - np.mean(left)) / scale),
            ],
            dtype=float,
        )
        rows.append(np.concatenate([base, neighbourhood]))
    return SurfaceScan(candidates, np.stack(rows))


def _predict_surface(
    scans: list[SurfaceScan], payload: dict[str, Any]
) -> dict[str, float | int]:
    coefficient = np.asarray(payload["coefficient"], dtype=float)
    mean = np.asarray(payload["feature_mean"], dtype=float)
    scale = np.asarray(payload["feature_scale"], dtype=float)
    positions: list[int] = []
    scores: list[float] = []
    margins: list[float] = []
    for scan in scans:
        design = np.column_stack([np.ones(len(scan.features)), (scan.features - mean) / scale])
        candidate_scores = design @ coefficient
        order = np.argsort(candidate_scores)[::-1]
        best = int(order[0])
        positions.append(int(scan.positions[best]))
        scores.append(float(candidate_scores[best]))
        margins.append(
            float(candidate_scores[best] - candidate_scores[int(order[1])])
            if len(order) > 1
            else float(candidate_scores[best])
        )
    if not positions:
        return {
            "position": math.nan,
            "support": 0,
            "support_fraction": 0.0,
            "position_sd": math.nan,
            "score": math.nan,
            "margin": math.nan,
        }
    position_array = np.asarray(positions, dtype=float)
    score_array = np.asarray(scores, dtype=float)
    cluster_weights = np.exp(np.clip(score_array, -2.0, 2.0))
    density = np.asarray(
        [
            cluster_weights[np.abs(position_array - centre) <= 70].sum()
            for centre in position_array
        ]
    )
    centre = position_array[int(np.argmax(density))]
    keep = np.abs(position_array - centre) <= 90
    selected_positions = position_array[keep]
    selected_weights = cluster_weights[keep]
    return {
        "position": _weighted_median(selected_positions, selected_weights),
        "support": int(keep.sum()),
        "support_fraction": float(keep.mean()),
        "position_sd": float(selected_positions.std(ddof=1)) if len(selected_positions) > 1 else 0.0,
        "score": float(np.median(score_array[keep])),
        "margin": float(np.median(np.asarray(margins)[keep])),
    }


def _window_consensus(
    scans: list[np.ndarray],
    front_window: tuple[int, int],
    back_window: tuple[int, int],
    minimum_amplitude: float,
) -> dict[str, float | int]:
    records: list[tuple[int, int, float, float]] = []
    for signal in scans:
        front = front_window[0] + int(np.argmax(signal[slice(*front_window)]))
        back = back_window[0] + int(np.argmax(signal[slice(*back_window)]))
        amp_front = float(signal[front])
        amp_back = float(signal[back])
        if amp_front >= minimum_amplitude and amp_back >= minimum_amplitude:
            records.append((front, back, amp_front, amp_back))
    if not records:
        return {"n_selected": 0, "front": math.nan, "back": math.nan, "lt_sd_mm": math.nan}
    matrix = np.asarray(records, dtype=float)
    front = _weighted_median(matrix[:, 0], np.sqrt(matrix[:, 2]))
    back = _weighted_median(matrix[:, 1], np.sqrt(matrix[:, 3]))
    slope = float(_MODEL["lens"]["LT_slope_mm_per_sample"])
    intercept = float(_MODEL["lens"]["LT_intercept_mm"])
    lt_values = slope * (matrix[:, 1] - matrix[:, 0]) + intercept
    return {
        "n_selected": int(len(matrix)),
        "front": front,
        "back": back,
        "lt_sd_mm": float(lt_values.std(ddof=1)) if len(matrix) > 1 else 0.0,
    }


def _usable_lens_scans(record: EsxRecord, eye: str) -> list[np.ndarray]:
    return [
        _smooth(scan, sigma=2.0)
        for measurement in record.measurements
        if measurement.eye == eye and not measurement.is_placeholder
        for scan in measurement.raw_ascans
    ]


def _lens_prediction(record: EsxRecord, eye: str, cornea_back: float,
                     lens_model: dict[str, Any] | None = None) -> dict[str, Any]:
    lens = _MODEL["lens"] if lens_model is None else lens_model
    scans = _usable_lens_scans(record, eye)
    if not scans:
        return {
            "predicted_AD_mm": math.nan,
            "predicted_LT_mm": math.nan,
            "lens_quality": "unmeasurable_or_review",
            "lens_gate_reasons": "no_usable_ascan",
        }

    window_payload = lens["window_consensus"]
    window = _window_consensus(
        scans,
        tuple(window_payload["front_window_samples"]),
        tuple(window_payload["back_window_samples"]),
        float(window_payload["minimum_amplitude"]),
    )
    front_payload = lens["front_selector"]
    back_payload = lens["back_selector"]
    front_selector = _predict_surface(
        [_surface_scan(scan, tuple(front_payload["window_samples"])) for scan in scans],
        front_payload,
    )
    back_selector = _predict_surface(
        [_surface_scan(scan, tuple(back_payload["window_samples"])) for scan in scans],
        back_payload,
    )

    window_front = float(window.get("front", math.nan))
    window_back = float(window.get("back", math.nan))
    lt_slope = float(lens["LT_slope_mm_per_sample"])
    lt_intercept = float(lens["LT_intercept_mm"])
    candidate_lt = (
        lt_slope * (window_back - window_front) + lt_intercept
        if np.isfinite(window_front) and np.isfinite(window_back)
        else math.nan
    )
    selector_lt = (
        lt_slope
        * (float(back_selector["position"]) - float(front_selector["position"]))
        + lt_intercept
    )
    disagreement = abs(candidate_lt - selector_lt) if np.isfinite(candidate_lt) else math.inf
    selected_fraction = float(window.get("n_selected", 0)) / len(scans)
    gate = lens["quality_gate"]
    reasons: list[str] = []
    if selected_fraction < float(gate["minimum_selected_fraction"]):
        reasons.append("low_paired_peak_fraction")
    if float(front_selector["support_fraction"]) < float(gate["minimum_front_support_fraction"]):
        reasons.append("unstable_lens_front")
    if float(back_selector["support_fraction"]) < float(gate["minimum_back_support_fraction"]):
        reasons.append("unstable_lens_back")
    if disagreement > float(gate["maximum_algorithm_disagreement_mm"]):
        reasons.append("dual_algorithm_disagreement")
    lower, upper = map(float, gate["plausible_LT_mm"])
    if not np.isfinite(candidate_lt) or not lower <= candidate_lt <= upper:
        reasons.append("LT_out_of_range_or_missing")
    candidate_ad = (
        float(lens["AD_slope_mm_per_sample"]) * (window_front - cornea_back)
        + float(lens["AD_intercept_mm"])
        if np.isfinite(window_front) and np.isfinite(cornea_back)
        else math.nan
    )
    usable = not reasons
    return {
        "predicted_AD_mm": candidate_ad if usable else math.nan,
        "predicted_LT_mm": candidate_lt if usable else math.nan,
        "lens_quality": "usable" if usable else "unmeasurable_or_review",
        "lens_gate_reasons": "" if usable else ";".join(reasons),
        "candidate_AD_mm": candidate_ad,
        "candidate_LT_mm": candidate_lt,
        "selector_LT_mm": selector_lt,
        "algorithm_disagreement_mm": disagreement,
        "selected_peak_fraction": selected_fraction,
        "n_lens_selected": int(window.get("n_selected", 0)),
        "n_ascan_usable": len(scans),
        "lens_front_position": window_front,
        "lens_back_position": window_back,
        "front_support_fraction": front_selector["support_fraction"],
        "back_support_fraction": back_selector["support_fraction"],
        "LT_sd_mm": window.get("lt_sd_mm", math.nan),
    }


def analyze_esx(path: str | Path) -> list[dict[str, Any]]:
    """Analyze one ESX file and return one result dictionary per eye."""

    record = read_esx(path)
    rows: list[dict[str, Any]] = []
    for eye in ("OD", "OS"):
        try:
            retinal = _retinal_prediction(record, eye)
            lens = _lens_prediction(
                record, eye, float(retinal.get("cornea_back_position", math.nan))
            )
            rows.append(
                {
                    "animal_id": record.animal_id,
                    "eye": eye,
                    **retinal,
                    **lens,
                    "algorithm_version": MODEL_VERSION,
                    "source_file": record.path.name,
                }
            )
        except Exception as exc:  # Preserve the other eye if only one fails.
            rows.append(
                {
                    "animal_id": record.animal_id,
                    "eye": eye,
                    "predicted_AL_mm": math.nan,
                    "AL_quality": "review",
                    "predicted_CCT_mm": math.nan,
                    "CCT_quality": "review",
                    "predicted_AD_mm": math.nan,
                    "predicted_LT_mm": math.nan,
                    "predicted_RT_mm": math.nan,
                    "lens_quality": "unmeasurable_or_review",
                    "lens_gate_reasons": "eye_processing_error",
                    "processing_error": str(exc),
                    "algorithm_version": MODEL_VERSION,
                    "source_file": record.path.name,
                }
            )
    return rows


def analyze_many(paths: Iterable[str | Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        rows.extend(analyze_esx(path))
    return rows
