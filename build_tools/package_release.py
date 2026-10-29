"""Assemble an audited portable ZIP, notices, dependency licenses and SHA256."""
import hashlib
from importlib import metadata
import json
import platform
from pathlib import Path
import shutil
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist/LS900 Biometry Analyzer V5"
RELEASE = ROOT / "release"


def main():
    if not (DIST / "LS900 Biometry Analyzer.exe").is_file():
        raise SystemExit("Build the V5 executable first")
    for source, name in (("LICENSE","LICENSE"), ("THIRD_PARTY_NOTICES.md","THIRD_PARTY_NOTICES.md"),
                         ("docs/USER_GUIDE.md","使用说明.md"), ("docs/REPRODUCIBILITY.md","REPRODUCIBILITY.md")):
        shutil.copy2(ROOT/source, DIST/name)
    licenses = DIST / "THIRD_PARTY_LICENSES"
    licenses.mkdir(exist_ok=True)
    distributions = ("numpy","lxml","openpyxl","et_xmlfile","Pillow","PySide6-Essentials","shiboken6","PyInstaller")
    versions = {}
    for name in distributions:
        distribution = metadata.distribution(name)
        versions[name] = distribution.version
        folder = licenses / name
        folder.mkdir(exist_ok=True)
        copied = 0
        for relative in distribution.files or []:
            if any(word in relative.name.lower() for word in ("license", "copying", "notice", "authors")):
                source = Path(distribution.locate_file(relative))
                if source.is_file():
                    # Preserve paths to avoid overwriting equal license names.
                    target = folder / str(relative).replace("..", "_")
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, target)
                    copied += 1
        if not copied:
            (folder/"SOURCE.txt").write_text(str(distribution.metadata.get("Home-page") or "https://pypi.org/project/"+name)+"\n", encoding="utf-8")
    qt = licenses / "Qt"
    qt.mkdir(exist_ok=True)
    for name in ("LGPL-3.0-only.txt","GPL-3.0-only.txt","GPL-2.0-only.txt"):
        target = qt/name
        shutil.copy2(ROOT/"licenses/Qt"/name, target)
    source_model = ROOT / "src/ls900_biometry/models/v5_model.json"
    from ls900_biometry.analysis import MODEL_SHA256, MODEL_VERSION
    from ls900_biometry import __version__
    digest = hashlib.sha256(source_model.read_bytes()).hexdigest().upper()
    assert digest == MODEL_SHA256
    (DIST/"RELEASE_MANIFEST.json").write_text(json.dumps({"software":__version__,"model":MODEL_VERSION,
       "model_sha256":digest,"python":platform.python_version(),"platform":"Windows x64","dependencies":versions},indent=2),encoding="utf-8")
    for path in DIST.rglob("*"):
        if path.suffix.lower() in {".esx",".eesx",".csv",".tsv",".db",".sqlite",".pkl",".npz",".npy"}:
            raise ValueError("Forbidden research data in release: "+str(path))
        if path.suffix.lower()==".xlsx" and path.name!="output_template.xlsx":
            raise ValueError("Non-template Excel in release")
    RELEASE.mkdir(exist_ok=True)
    target = RELEASE/f"LS900-ESX-GuineaPig-Biometry-v{__version__}-V5-windows-x64.zip"
    with zipfile.ZipFile(target,"w",zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for path in sorted(DIST.rglob("*")):
            if path.is_file():
                archive.write(path,path.relative_to(DIST))
    with zipfile.ZipFile(target) as archive:
        assert archive.testzip() is None
    sha = hashlib.sha256(target.read_bytes()).hexdigest()
    target.with_suffix(target.suffix+".sha256.txt").write_text(sha+"  "+target.name+"\n",encoding="ascii")
    print(f"{target}\nSHA256 {sha}\nSize {target.stat().st_size} bytes")


if __name__=="__main__":
    main()
