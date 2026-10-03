"""
Genera le icone dell'applicazione a partire dal master vettoriale assets/icon.svg:
  - assets/icon.png  (256x256, icona finestre Qt e pacchetto Linux)
  - icon.ico         (16-256 px, eseguibile Windows e installer Inno Setup)

Uso: python tools/build_icons.py   (richiede PyQt6 e Pillow)
"""

import io
import sys
from pathlib import Path
from typing import List

from PIL import Image
from PyQt6.QtCore import QBuffer, QIODevice, Qt
from PyQt6.QtGui import QGuiApplication, QImage, QPainter
from PyQt6.QtSvg import QSvgRenderer

ROOT = Path(__file__).resolve().parent.parent
SVG_PATH = ROOT / "assets" / "icon.svg"
PNG_PATH = ROOT / "assets" / "icon.png"
ICO_PATH = ROOT / "icon.ico"
ICO_SIZES: List[int] = [16, 24, 32, 48, 64, 128, 256]


def render_svg(renderer: QSvgRenderer, size: int) -> Image.Image:
    """Renderizza l'SVG alla dimensione indicata e lo converte in immagine Pillow."""
    qimg = QImage(size, size, QImage.Format.Format_ARGB32)
    qimg.fill(Qt.GlobalColor.transparent)
    painter = QPainter(qimg)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    renderer.render(painter)
    painter.end()

    buffer = QBuffer()
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    qimg.save(buffer, "PNG")
    return Image.open(io.BytesIO(bytes(buffer.data()))).convert("RGBA")


def main() -> int:
    app = QGuiApplication.instance() or QGuiApplication(sys.argv)  # noqa: F841 - necessario a QPainter
    renderer = QSvgRenderer(str(SVG_PATH))
    if not renderer.isValid():
        print(f"SVG non valido: {SVG_PATH}", file=sys.stderr)
        return 1

    # Ogni taglia è renderizzata dal vettoriale (più nitida del ridimensionamento)
    images = [render_svg(renderer, s) for s in ICO_SIZES]
    images[-1].save(PNG_PATH, optimize=True)
    images[-1].save(ICO_PATH, format="ICO", sizes=[(s, s) for s in ICO_SIZES],
                    append_images=images[:-1])
    print(f"Generati: {PNG_PATH.relative_to(ROOT)}, {ICO_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
