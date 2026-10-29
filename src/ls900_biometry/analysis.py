"""Shared public V5 inference entry point; no training occurs at runtime."""
from functools import lru_cache
import hashlib
from importlib.resources import files
import json
from pathlib import Path

MODEL_VERSION = "guinea-lenstar-v5.0.0-animal-grouped-2026-10-16"
MODEL_SHA256 = "80BDF7AC628A3F27F2CAE2CBD8D7D88B458FF6E248840AA406D09FFCAAE6100B"


@lru_cache(maxsize=1)
def load_model() -> dict:
    payload = files("ls900_biometry").joinpath("models/v5_model.json").read_bytes()
    if hashlib.sha256(payload).hexdigest().upper() != MODEL_SHA256:
        raise ValueError("V5 model integrity check failed. Re-download the official release.")
    model = json.loads(payload)
    if model["version"] != MODEL_VERSION:
        raise ValueError("Unexpected V5 model version")
    return model


def analyze_esx(path: str | Path) -> list[dict]:
    from .v5_cli import analyze_file
    return analyze_file(Path(path), load_model())
