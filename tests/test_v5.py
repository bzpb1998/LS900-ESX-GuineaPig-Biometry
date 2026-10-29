from __future__ import annotations
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from ls900_biometry.esx_reader import EsxRecord,Measurement
from ls900_biometry.v5 import extract_features,predict_retina
from ls900_biometry.v5_cli import analyze_file,MODEL_PATH


class V5IntegrityTests(unittest.TestCase):
    def test_frozen_parameter_identity(self):
        digest=hashlib.sha256(Path(MODEL_PATH).read_bytes()).hexdigest().upper()
        self.assertEqual(digest,"80BDF7AC628A3F27F2CAE2CBD8D7D88B458FF6E248840AA406D09FFCAAE6100B")

    def test_manual_retina_cursors_are_not_input_features(self):
        x=np.arange(18000,dtype=float)
        signal=sum(height*np.exp(-.5*((x-centre)/12)**2)
                   for centre,height in ((14500,5),(14720,8),(14940,3)))+.001
        def record(ilm,rpe):
            m=Measurement("OD","2026.10.16",signal,{0:1000,1:1320,6:ilm,7:rpe},[signal]*4)
            return EsxRecord(Path("synthetic.esx"),"synthetic",[m])
        a=extract_features(record(14000,14200),"OD","raw50")
        b=extract_features(record(16000,16500),"OD","raw50")
        np.testing.assert_array_equal(a.pairs,b.pairs)
        np.testing.assert_array_equal(a.matrix,b.matrix)

    def test_unavailable_backup_is_reviewed(self):
        model=json.loads(Path(MODEL_PATH).read_text(encoding="utf-8"))
        features=SimpleNamespace(front=1000.,back=1320.,n_scans=5)
        prediction={"ilm":14500,"rpe":14700,"margin":.5,"support":.9,
                    "backup_ilm":-1,"disagreement":float("nan")}
        with patch("ls900_biometry.v5.extract_features",return_value=features), \
             patch("ls900_biometry.v5.score_features",return_value=prediction):
            result=predict_retina(None,"OD",model)
        self.assertEqual(result["AL_quality"],"review")
        self.assertIn("backup_selector_unavailable",result["AL_gate_reasons"])

    def test_single_eye_file_does_not_fabricate_other_eye(self):
        model=json.loads(Path(MODEL_PATH).read_text(encoding="utf-8"))
        measurement=Measurement("OD","2026.10.16",np.ones(18000),{0:1000,1:1320},[])
        record=EsxRecord(Path("synthetic.esx"),"synthetic",[measurement])
        with patch("ls900_biometry.v5_cli.read_esx",return_value=record), \
             patch("ls900_biometry.v5_cli.predict_retina",return_value={"cornea_back_position":1320.}), \
             patch("ls900_biometry.v5_cli.legacy._lens_prediction",return_value={}):
            result=analyze_file(Path("synthetic.esx"),model)
        self.assertEqual([r["eye"] for r in result],["OD"])


if __name__=="__main__":unittest.main()
