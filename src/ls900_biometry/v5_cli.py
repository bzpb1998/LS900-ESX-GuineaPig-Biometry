"""Explicit opt-in V5 experimental batch runner; uses the compact Excel layout."""
from __future__ import annotations
import argparse
from datetime import datetime
from importlib.resources import files
import json
import math
from pathlib import Path

from . import inference as legacy
from .esx_reader import read_esx
from .exporter import export_report
from .v5 import predict_retina


MODEL_PATH=files("ls900_biometry").joinpath("models/v5_model.json")


def analyze_file(path: Path, model: dict) -> list[dict]:
    record=read_esx(path)
    rows=[]
    for eye in ("OD","OS"):
        if not any(m.eye==eye and not m.is_placeholder and len(m.scan) for m in record.measurements):
            continue
        try:
            retinal=predict_retina(record,eye,model)
            cct=float(retinal.get("predicted_CCT_mm",math.nan))
            retinal["CCT_quality"]="high" if math.isfinite(cct) and .12<=cct<=.30 else "review"
            lens=legacy._lens_prediction(record,eye,retinal["cornea_back_position"],model["lens"])
            rows.append({"animal_id":record.animal_id,"eye":eye,**retinal,**lens,
                         "algorithm_version":model["version"],"source_file":path.name,
                         "source_key":str(path.resolve())})
        except (ValueError,KeyError,IndexError,ArithmeticError) as exc:
            rows.append({"animal_id":record.animal_id,"eye":eye,"source_file":path.name,
                         "source_key":str(path.resolve()),"algorithm_version":model["version"],
                         "predicted_AL_mm":math.nan,"predicted_CCT_mm":math.nan,
                         "predicted_AD_mm":math.nan,"predicted_LT_mm":math.nan,
                         "predicted_RT_mm":math.nan,"AL_quality":"review",
                         "lens_quality":"unmeasurable_or_review","lens_gate_reasons":"eye_processing_error",
                         "processing_error":str(exc)})
    return rows


def main():
    parser=argparse.ArgumentParser(description="Experimental V5: local ESX files to compact Excel")
    parser.add_argument("--input",type=Path,required=True,help="One ESX file or directory (nonrecursive)")
    parser.add_argument("--output",type=Path,required=True,help="Output .xlsx file")
    args=parser.parse_args()
    if args.output.suffix.lower()!=".xlsx":
        parser.error("--output must end in .xlsx")
    with MODEL_PATH.open("r",encoding="utf-8") as handle:
        model=json.load(handle)
    paths=[args.input] if args.input.is_file() else sorted(args.input.glob("*.esx"))
    if not paths:
        parser.error("No ESX files found")
    predictions=[];errors=[]
    for path in paths:
        try:
            predictions.extend(analyze_file(path,model))
        except (ValueError,OSError) as exc:
            errors.append(f"{path.name}: {exc}")
    if not predictions:
        raise ValueError("No eyes successfully parsed")
    args.output.parent.mkdir(parents=True,exist_ok=True)
    export_report(predictions,args.output,title="LS900_Biometry_"+datetime.now().strftime("%Y%m%d_%H%M%S"),
                  extra_notes=["V5 实验模型；现有评价为回顾性，尚待新动物前瞻性验证。",
                               "质量等级为启发式判断，不是准确概率；异常解剖和含混视网膜峰需复核。"],
                  file_errors=errors)
    print(args.output)


if __name__=="__main__":main()
