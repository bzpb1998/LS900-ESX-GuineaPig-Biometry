"""Generate the Windows application icon from simple vector-like primitives."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
ASSETS.mkdir(exist_ok=True)


def make_icon(size: int = 512) -> Image.Image:
    image = Image.new("RGBA", (size, size), (27, 42, 74, 255))
    draw = ImageDraw.Draw(image)
    margin = int(size * 0.045)
    draw.rounded_rectangle(
        (margin, margin, size - margin, size - margin),
        radius=int(size * 0.21),
        outline=(60, 118, 230, 255),
        width=max(4, int(size * 0.038)),
    )
    eye = [
        (int(size * 0.17), int(size * 0.50)),
        (int(size * 0.34), int(size * 0.32)),
        (int(size * 0.66), int(size * 0.32)),
        (int(size * 0.83), int(size * 0.50)),
        (int(size * 0.66), int(size * 0.68)),
        (int(size * 0.34), int(size * 0.68)),
    ]
    draw.polygon(eye, fill=(247, 249, 255, 255))
    draw.ellipse(
        (int(size * 0.36), int(size * 0.36), int(size * 0.64), int(size * 0.64)),
        fill=(47, 97, 213, 255),
    )
    draw.ellipse(
        (int(size * 0.445), int(size * 0.445), int(size * 0.555), int(size * 0.555)),
        fill=(11, 18, 34, 255),
    )
    tick = (127, 167, 245, 255)
    width = max(3, int(size * 0.025))
    for x in (int(size * 0.25), int(size * 0.75)):
        draw.line((x, int(size * 0.20), x, int(size * 0.31)), fill=tick, width=width)
        draw.line((x, int(size * 0.69), x, int(size * 0.80)), fill=tick, width=width)
    return image


icon = make_icon()
icon.save(ASSETS / "app_icon.png")
icon.save(
    ASSETS / "app_icon.ico",
    sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
)
print(ASSETS / "app_icon.ico")
