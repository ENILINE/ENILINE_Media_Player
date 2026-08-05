"""Vector icons rendered from inline SVGs (no external asset files)."""
from PyQt5.QtCore import QByteArray, Qt
from PyQt5.QtGui import QIcon, QPainter, QPixmap
from PyQt5.QtSvg import QSvgRenderer

_SVGS = {
    "play": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">'
            '<path fill="{color}" d="M8 5v14l11-7z"/></svg>',
    "pause": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">'
             '<path fill="{color}" d="M6 5h4v14H6z"/><path fill="{color}" d="M14 5h4v14h-4z"/></svg>',
    "prev": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">'
            '<path fill="{color}" d="M6 5h2v14H6z"/><path fill="{color}" d="M20 5v14l-11-7z"/></svg>',
    "next": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">'
            '<path fill="{color}" d="M16 5h2v14h-2z"/><path fill="{color}" d="M4 5v14l11-7z"/></svg>',
    "volume": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">'
              '<path fill="{color}" d="M3 9v6h4l5 5V4L7 9H3z"/>'
              '<path fill="{color}" fill-opacity="0.55" d="M16.5 12a4.5 4.5 0 0 0-2.5-4v8a4.5 4.5 0 0 0 2.5-4z"/>'
              '<path fill="{color}" fill-opacity="0.35" d="M14 3.2v2.1a7 7 0 0 1 0 13.4v2.1a9 9 0 0 0 0-17.6z"/></svg>',
    "volume_muted": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">'
                    '<path fill="{color}" d="M3 9v6h4l5 5V4L7 9H3z"/>'
                    '<path fill="{color}" d="M16 9l6 6M22 9l-6 6" stroke="{color}" stroke-width="2" fill="none"/>'
                    '</svg>',
    "fullscreen": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">'
                  '<path fill="none" stroke="{color}" stroke-width="2" d="M4 9V4h5M15 4h5v5M20 15v5h-5M9 20H4v-5"/>'
                  '</svg>',
    "fullscreen_exit": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">'
                       '<path fill="none" stroke="{color}" stroke-width="2" d="M4 4h5v5H4zM20 4h-5v5h5zM20 20h-5v-5h5zM4 20h5v-5H4z"/>'
                       '</svg>',
}

_cache = {}


def icon(name: str, color: str = "#e0e0e0", size: int = 16) -> QIcon:
    key = (name, color, size)
    cached = _cache.get(key)
    if cached is not None:
        return cached
    svg = _SVGS[name].replace("{color}", color)
    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    painter = QPainter(pm)
    renderer.render(painter)
    painter.end()
    qicon = QIcon(pm)
    _cache[key] = qicon
    return qicon