"""Minimal, read-only ESX parser used by the inference pipeline."""

from __future__ import annotations

import base64
import re
import zlib
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from lxml import etree


@dataclass(slots=True)
class Measurement:
    eye: str
    start: str
    scan: np.ndarray
    cursors: dict[int, float]
    raw_ascans: list[np.ndarray]

    @property
    def is_placeholder(self) -> bool:
        return self.start.startswith("1970.")


@dataclass(slots=True)
class EsxRecord:
    path: Path
    animal_id: str
    measurements: list[Measurement]


def _decode_scan(text: str | None) -> np.ndarray:
    if not text:
        return np.empty(0, dtype=np.float32)
    payload = zlib.decompress(base64.b64decode(text))
    return np.frombuffer(payload, dtype=">f4").astype(np.float32, copy=False)


def _animal_id(path: Path) -> str:
    match = re.search(r"(?:ZA|UA)[ _-]*(\d+)", path.stem, re.IGNORECASE)
    if match:
        return str(int(match.group(1)))
    tokens = re.findall(r"(?<!\d)(\d{1,3})(?!\d)", path.stem)
    return str(int(tokens[0])) if tokens else path.stem


def read_esx(path: str | Path) -> EsxRecord:
    """Parse one ESX file without modifying it."""

    source = Path(path)
    parser = etree.XMLParser(
        huge_tree=True, recover=False, resolve_entities=False, no_network=True
    )
    tree = etree.parse(str(source), parser)
    measurements: list[Measurement] = []

    for node in tree.xpath("//MEASUREMENT"):
        result = node.find("BIOMETRYRESULT")
        if result is None:
            continue
        cursors: dict[int, float] = {}
        for cursor in result.findall("CURSOR"):
            element_text = cursor.findtext("CURSORELEMENT")
            position_text = cursor.findtext("SCANPOS")
            if element_text is None or position_text is None:
                continue
            cursors[int(element_text)] = float(position_text)

        raw_ascans: list[np.ndarray] = []
        for ascan in node.findall("ASCAN"):
            if (ascan.findtext("USED") or "").lower() != "true":
                continue
            if (ascan.findtext("SATURATED") or "").lower() == "true":
                continue
            scan = _decode_scan(ascan.findtext("SCANDATA"))
            if len(scan) >= 11000:
                raw_ascans.append(scan)

        measurements.append(
            Measurement(
                eye=node.get("eye", ""),
                start=result.getparent().findtext("START") or "",
                scan=_decode_scan(result.findtext("SCANDATA")),
                cursors=cursors,
                raw_ascans=raw_ascans,
            )
        )

    if not measurements:
        raise ValueError("文件中未找到可解析的 BIOMETRYRESULT 数据")
    return EsxRecord(source, _animal_id(source), measurements)
