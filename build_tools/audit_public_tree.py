"""Fail if publishable Git files include raw records, outputs or credentials."""
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parents[1]
ALLOWED={".py",".md",".txt",".json",".yml",".yaml",".ps1",".bat",".spec",".cff",".css",".js",".html",".toml",".svg"}
IMAGES={"assets/app_icon.png","assets/app_icon.ico","assets/desktop-preview.png"}
TEMPLATE="src/ls900_biometry/assets/output_template.xlsx"
RAW_EXT={".esx",".eesx",".xml",".csv",".tsv",".db",".sqlite",".sqlite3",".pkl",".npz",".npy",".ndjson",".pdf",".zip"}


def inspect_path(name,check_content=True):
    path=ROOT/name
    suffix=path.suffix.lower()
    if suffix in RAW_EXT:
        return "research/raw-data extension"
    if suffix==".xlsx" and name!=TEMPLATE:
        return "non-template workbook"
    if suffix in {".png",".jpg",".jpeg",".ico",".bmp"} and name not in IMAGES:
        return "non-application image"
    if suffix not in ALLOWED and name not in IMAGES|{TEMPLATE,"LICENSE",".gitignore"}:
        return "unexpected file type"
    if check_content and suffix in ALLOWED:
        text=path.read_text(encoding="utf-8")
        for pattern in (r"gh[pousr]_[A-Za-z0-9]{30,}",r"-----BEGIN (?:[A-Z]+ )?PRIVATE KEY-----"):
            if re.search(pattern,text):
                return "credential-like content"
    return None


def main():
    tracked=subprocess.check_output(["git","ls-files","--cached","--others","--exclude-standard"],cwd=ROOT,text=True).splitlines()
    failures=[(name,reason) for name in tracked if (reason:=inspect_path(name))]
    history=subprocess.check_output(["git","log","--all","--format=","--name-only"],cwd=ROOT,text=True).splitlines()
    failures += [(name,"forbidden data extension in Git history") for name in sorted(set(history))
                 if name and Path(name).suffix.lower() in RAW_EXT]
    if failures:
        raise SystemExit("Publication audit failed: "+repr(failures))
    print(f"Publication audit passed: {len(tracked)} Git files; no raw ESX, research tables, waveform caches, non-icon screenshots or credential patterns.")


if __name__=="__main__":main()
