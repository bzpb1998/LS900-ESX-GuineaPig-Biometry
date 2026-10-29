"""Render the original SVG into reproducible PNG and Windows ICO assets."""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from pathlib import Path
from PySide6.QtGui import QImage, QPainter
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QApplication
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
app = QApplication.instance() or QApplication([])
renderer = QSvgRenderer(str(ROOT / "src/ls900_biometry/assets/logo.svg"))
image = QImage(512, 512, QImage.Format.Format_ARGB32)
image.fill(0)
painter = QPainter(image)
renderer.render(painter)
painter.end()
target = ROOT / "assets/app_icon.png"
image.save(str(target))
with Image.open(target) as png:
    png.save(ROOT / "assets/app_icon.ico", sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])
print(target)
