"""Reproducible V5 command-line entry point."""
import argparse
from pathlib import Path
from .analysis import MODEL_SHA256, MODEL_VERSION
from .batch import run_batch, save_report


def main() -> int:
    parser = argparse.ArgumentParser(description="Local V5 guinea-pig ESX biometry to Excel")
    parser.add_argument("--input", type=Path, help="An ESX file or a directory (nonrecursive)")
    parser.add_argument("--output", type=Path, help="Output .xlsx file")
    parser.add_argument("--version", action="store_true")
    args = parser.parse_args()
    if args.version:
        print(MODEL_VERSION + "\nSHA256 " + MODEL_SHA256)
        return 0
    if not args.input or not args.output:
        parser.error("--input and --output are required")
    paths = ([args.input] if args.input.is_file() else
             sorted(p for p in args.input.iterdir() if p.is_file() and p.suffix.lower() == ".esx"))
    if not paths:
        parser.error("No ESX files found")
    if args.output.exists():
        parser.error("Output already exists; choose a new path to preserve previous results")
    result = run_batch(paths)
    for error in result.errors:
        print("WARNING: " + error)
    try:
        print(save_report(result, args.output))
    except ValueError as exc:
        parser.error(str(exc))
    print(f"Files {result.completed}/{result.total}; AL eyes {result.usable_eyes}")
    return 0 if result.completed == result.total else 2


if __name__ == "__main__":
    raise SystemExit(main())
