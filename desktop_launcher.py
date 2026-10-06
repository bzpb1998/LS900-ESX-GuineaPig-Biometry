"""Windows desktop launcher: hidden local server, browser UI and tray icon."""

from __future__ import annotations

import ctypes
import logging
import os
import socket
import sys
import threading
import time
import webbrowser
from pathlib import Path


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from PIL import Image, ImageDraw  # noqa: E402
from pystray import Icon, Menu, MenuItem  # noqa: E402
from waitress import create_server  # noqa: E402

from ls900_biometry.webapp import create_app  # noqa: E402


APP_NAME = "LS900 Biometry Analyzer"
HOST = "127.0.0.1"
MUTEX_NAME = "Local\\LS900_ESX_GuineaPig_Biometry_Analyzer"
ERROR_ALREADY_EXISTS = 183


def _app_data_dir() -> Path:
    base = Path(os.environ.get("LOCALAPPDATA", Path.home()))
    target = base / APP_NAME
    target.mkdir(parents=True, exist_ok=True)
    return target


APP_DATA = _app_data_dir()
PORT_FILE = APP_DATA / "server.port"
logging.basicConfig(
    filename=APP_DATA / "app.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)


def _message_box(message: str, title: str = APP_NAME) -> None:
    if os.name == "nt":
        ctypes.windll.user32.MessageBoxW(None, message, title, 0x10)
    else:
        print(f"{title}: {message}", file=sys.stderr)


def _find_port() -> int:
    requested = os.environ.get("LS900_PORT")
    candidates = [int(requested)] if requested else list(range(8765, 8796))
    for port in candidates:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                probe.bind((HOST, port))
                return port
            except OSError:
                continue
    raise RuntimeError("无法找到可用的本机端口（8765–8795）。")


def _tray_image() -> Image.Image:
    size = 96
    image = Image.new("RGBA", (size, size), (27, 42, 74, 255))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((4, 4, 91, 91), radius=20, outline=(60, 118, 230, 255), width=4)
    draw.polygon([(17, 48), (33, 31), (63, 31), (79, 48), (63, 65), (33, 65)], fill=(245, 248, 255, 255))
    draw.ellipse((35, 35, 61, 61), fill=(47, 97, 213, 255))
    draw.ellipse((43, 43, 53, 53), fill=(12, 20, 37, 255))
    for x in (24, 72):
        draw.line((x, 22, x, 31), fill=(127, 167, 245, 255), width=3)
        draw.line((x, 65, x, 74), fill=(127, 167, 245, 255), width=3)
    return image


def _acquire_single_instance():
    if os.name != "nt":
        return None, True
    handle = ctypes.windll.kernel32.CreateMutexW(None, False, MUTEX_NAME)
    first = ctypes.windll.kernel32.GetLastError() != ERROR_ALREADY_EXISTS
    return handle, first


def _open_existing() -> bool:
    try:
        port = int(PORT_FILE.read_text(encoding="ascii").strip())
    except (OSError, ValueError):
        return False
    webbrowser.open(f"http://{HOST}:{port}")
    return True


def main() -> None:
    mutex_handle, first_instance = _acquire_single_instance()
    if not first_instance:
        if not _open_existing():
            _message_box("程序已经在运行，但无法读取其地址。请从任务栏托盘退出后重试。")
        return

    state: dict[str, object] = {}
    stopped = threading.Event()

    def stop_application(*_args) -> None:
        if stopped.is_set():
            return
        stopped.set()
        server = state.get("server")
        tray = state.get("tray")
        try:
            if server is not None:
                server.close()
        except Exception:
            logging.exception("Failed to close local server")
        try:
            if tray is not None:
                tray.stop()
        except Exception:
            logging.exception("Failed to stop tray icon")
        try:
            PORT_FILE.unlink(missing_ok=True)
        except OSError:
            logging.exception("Failed to remove port file")

    try:
        port = _find_port()
        url = f"http://{HOST}:{port}"
        app = create_app(shutdown_callback=stop_application)
        server = create_server(app, host=HOST, port=port, threads=4)
        state["server"] = server
        PORT_FILE.write_text(str(port), encoding="ascii")
        server_thread = threading.Thread(target=server.run, name="ls900-server", daemon=True)
        server_thread.start()
        time.sleep(0.35)

        if os.environ.get("LS900_NO_BROWSER") != "1":
            webbrowser.open(url)

        if os.environ.get("LS900_NO_TRAY") == "1":
            stopped.wait()
        else:
            tray = Icon(
                "ls900-biometry-analyzer",
                _tray_image(),
                APP_NAME,
                Menu(
                    MenuItem("打开分析页面", lambda *_: webbrowser.open(url), default=True),
                    MenuItem("退出程序", stop_application),
                ),
            )
            state["tray"] = tray
            tray.run()
    except Exception as exc:
        logging.exception("Application startup failed")
        _message_box(f"程序启动失败：\n{exc}\n\n日志位置：{APP_DATA / 'app.log'}")
    finally:
        stop_application()
        if os.name == "nt" and mutex_handle:
            ctypes.windll.kernel32.CloseHandle(mutex_handle)


if __name__ == "__main__":
    main()
