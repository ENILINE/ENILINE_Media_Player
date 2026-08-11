"""Convert icon.svg to icon.png."""
import os

from PyQt5.QtCore import QByteArray, Qt
from PyQt5.QtGui import QPainter, QPixmap
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtWidgets import QApplication

app = QApplication([])

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
svg_path = os.path.join(root, "icon.svg")
png_path = os.path.join(root, "icon.png")

with open(svg_path, "rb") as f:
    svg_data = f.read()

renderer = QSvgRenderer(QByteArray(svg_data))
pm = QPixmap(256, 256)
pm.fill(Qt.transparent)
painter = QPainter(pm)
renderer.render(painter)
painter.end()
pm.save(png_path, "PNG")
print(f"Saved {png_path}")