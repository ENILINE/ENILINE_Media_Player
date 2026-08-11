import ctypes
import os
import subprocess

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QPainter
from PyQt5.QtWidgets import QMenu, QWidget


class VideoSurface(QWidget):
    """A plain native window that mpv renders into via its `wid` handle."""

    files_dropped = pyqtSignal(list)
    settings_requested = pyqtSignal()
    about_requested = pyqtSignal()
    browse_file_requested = pyqtSignal(str)
    file_properties_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_NativeWindow, True)
        self.setAttribute(Qt.WA_OpaquePaintEvent, True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMinimumSize(120, 80)
        self.setAcceptDrops(True)
        self.setMouseTracking(True)
        self._current_path = ""
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._context_menu)

    def set_current_path(self, path: str):
        self._current_path = path

    def _context_menu(self, pos):
        menu = QMenu(self)
        has_file = bool(self._current_path and os.path.isfile(self._current_path))
        menu.addAction("设置", self.settings_requested.emit)
        menu.addAction("关于", self.about_requested.emit)
        if has_file:
            menu.addSeparator()
            menu.addAction("浏览文件", lambda: self.browse_file_requested.emit(self._current_path))
            menu.addAction("属性", lambda: self.file_properties_requested.emit(self._current_path))
        menu.exec_(self.mapToGlobal(pos))

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor("#1e1e1e"))
        p.end()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        paths = []
        for url in event.mimeData().urls():
            p = url.toLocalFile()
            if p:
                paths.append(p)
        if paths:
            self.files_dropped.emit(paths)


def open_file_location(path: str):
    """Open Explorer with the file selected. Falls back to opening the directory."""
    try:
        subprocess.Popen(["explorer", "/select,", os.path.normpath(path)])
    except Exception:
        if os.path.exists(path):
            os.startfile(os.path.dirname(path))


def show_file_properties(path: str):
    """Open the Windows file properties dialog."""
    try:
        ctypes.windll.shell32.ShellExecuteW(
            None, "properties", os.path.normpath(path), None, None, 1
        )
    except Exception:
        pass
