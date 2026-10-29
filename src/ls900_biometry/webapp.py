"""Local-only Flask interface."""

from __future__ import annotations

import io
import tempfile
import threading
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_file
from werkzeug.utils import secure_filename

from .exporter import export_report
from .analysis import analyze_esx


def create_app(shutdown_callback=None) -> Flask:
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024 * 1024
    app.config["DESKTOP_MODE"] = shutdown_callback is not None

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    @app.post("/shutdown")
    def shutdown():
        if shutdown_callback is None:
            return jsonify({"error": "当前运行模式不支持从页面退出。"}), 409
        threading.Timer(0.35, shutdown_callback).start()
        return jsonify({"status": "stopping"})

    @app.post("/analyze")
    def analyze():
        uploads = request.files.getlist("files")
        uploads = [item for item in uploads if item.filename]
        if not uploads:
            return jsonify({"error": "请至少选择一个 ESX 文件。"}), 400
        if any(not item.filename.lower().endswith(".esx") for item in uploads):
            return jsonify({"error": "只能上传 .esx 文件。"}), 400

        predictions: list[dict] = []
        errors: list[str] = []
        with tempfile.TemporaryDirectory(prefix="ls900_") as temp:
            temp_dir = Path(temp)
            for index, upload in enumerate(uploads, start=1):
                safe_name = secure_filename(upload.filename) or f"input_{index}.esx"
                file_dir = temp_dir / f"{index:04d}"
                file_dir.mkdir()
                source = file_dir / safe_name
                upload.save(source)
                try:
                    file_rows = analyze_esx(source)
                    for row in file_rows:
                        row["source_key"] = f"{index:04d}:{upload.filename}"
                    predictions.extend(file_rows)
                except Exception as exc:
                    errors.append(f"{upload.filename}：{exc}")

            if not predictions:
                return jsonify({"error": "没有文件成功解析。", "details": errors}), 422
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_name = f"LS900_Biometry_{stamp}.xlsx"
            output_path = temp_dir / output_name
            export_report(
                predictions,
                output_path,
                title=f"LS900_Biometry_{stamp}",
                file_errors=errors,
            )
            payload = io.BytesIO(output_path.read_bytes())
            payload.seek(0)
            return send_file(
                payload,
                as_attachment=True,
                download_name=output_name,
                mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

    return app
