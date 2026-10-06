"""Start the local browser application on this computer only."""

from __future__ import annotations

import sys
import threading
import webbrowser
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from ls900_biometry.webapp import create_app  # noqa: E402


HOST = "127.0.0.1"
PORT = int(os.environ.get("LS900_PORT", "8765"))


def main() -> None:
    app = create_app()
    url = f"http://{HOST}:{PORT}"
    if os.environ.get("LS900_NO_BROWSER") != "1":
        threading.Timer(1.2, lambda: webbrowser.open(url)).start()
    print(f"LS900 analyzer is running at {url}")
    print("Keep this window open while using the page. Press Ctrl+C to stop.")
    try:
        from waitress import serve

        serve(app, host=HOST, port=PORT, threads=4)
    except ImportError:
        app.run(host=HOST, port=PORT, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
