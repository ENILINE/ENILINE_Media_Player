from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget


class VideoSurface(QWidget):
    """A plain native window that mpv renders into via its `wid` handle."""

    def __init__(self, parent=None):
        super().__init__(parent)
        # Keep a stable native window handle so mpv's wid stays valid.
        self.setAttribute(Qt.WA_NativeWindow, True)
        self.setAttribute(Qt.WA_OpaquePaintEvent, True)
        self.setFocusPolicy(Qt.NoFocus)
        self.setMinimumSize(320, 180)