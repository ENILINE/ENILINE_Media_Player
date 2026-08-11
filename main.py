"""Entry point. Must put the libmpv DLL directory on PATH before importing mpv."""
import os
import sys


def _bootstrap_mpv():
    if os.name != "nt":
        return
    if getattr(sys, "frozen", False):
        candidates = [
            os.path.dirname(sys.executable),
            getattr(sys, "_MEIPASS", None),
        ]
    else:
        candidates = [os.path.join(os.path.dirname(os.path.abspath(__file__)), "bin")]
    for d in candidates:
        if not d or not os.path.isdir(d):
            continue
        dll_dir = os.path.abspath(d)
        if os.path.isfile(os.path.join(dll_dir, "libmpv-2.dll")):
            os.environ["PATH"] = dll_dir + os.pathsep + os.environ.get("PATH", "")
            try:
                os.add_dll_directory(dll_dir)
            except (AttributeError, OSError):
                pass
            return


_bootstrap_mpv()

from PyQt5.QtCore import QByteArray, Qt
from PyQt5.QtGui import QIcon, QPainter, QPixmap
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtWidgets import QApplication  # noqa: E402

from player_app.ui.main_window import MainWindow  # noqa: E402
from player_app.ui.theme import QSS  # noqa: E402


def _load_app_icon() -> QIcon:
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS if hasattr(sys, "_MEIPASS") else os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(base, "icon.svg")
    if os.path.exists(icon_path):
        with open(icon_path, "r", encoding="utf-8") as f:
            svg_data = f.read()
        renderer = QSvgRenderer(QByteArray(svg_data.encode("utf-8")))
        pm = QPixmap(256, 256)
        pm.fill(Qt.transparent)
        painter = QPainter(pm)
        renderer.render(painter)
        painter.end()
        return QIcon(pm)
    return QIcon()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("ENILINE Media Player")
    app.setOrganizationName("ENILINE")
    icon = _load_app_icon()
    if not icon.isNull():
        app.setWindowIcon(icon)
    app.setStyleSheet(QSS)
    startup_paths = []
    for arg in sys.argv[1:]:
        arg = arg.strip()
        if arg and os.path.exists(arg):
            startup_paths.append(os.path.abspath(arg))
    win = MainWindow(startup_paths=startup_paths)
    if not icon.isNull():
        win.setWindowIcon(icon)
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()