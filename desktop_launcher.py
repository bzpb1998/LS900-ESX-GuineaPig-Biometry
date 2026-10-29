"""Windowed Windows entry point. No browser or local HTTP server."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

if __name__ == "__main__":
    if "--batch" in sys.argv:
        sys.argv.remove("--batch")
        from ls900_biometry.cli import main
    else:
        from ls900_biometry.desktop import main
    raise SystemExit(main())
