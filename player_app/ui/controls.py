from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QSlider,
    QToolButton,
    QWidget,
)

SPEED_PRESETS = [0.1, 0.5, 1, 2, 4, 8, 16]


def fmt_time(seconds: float) -> str:
    if seconds is None or seconds < 0:
        seconds = 0
    s = int(seconds)
    h, rem = divmod(s, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


class Controls(QWidget):
    play_toggled = pyqtSignal()
    seek_requested = pyqtSignal(float)
    speed_changed = pyqtSignal(float)
    volume_changed = pyqtSignal(int)
    mute_toggled = pyqtSignal()
    mode_cycle_requested = pyqtSignal()
    fullscreen_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._duration = 0.0
        self._seeking = False
        self._updating = False
        self._build()

    def _build(self):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(6, 4, 6, 4)
        lay.setSpacing(6)

        self.play_btn = QPushButton("播放")
        self.play_btn.setFixedWidth(56)
        self.play_btn.clicked.connect(self.play_toggled.emit)
        lay.addWidget(self.play_btn)

        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setMinimumWidth(110)
        lay.addWidget(self.time_label)

        self.progress = QSlider(Qt.Horizontal)
        self.progress.setRange(0, 1000)
        self.progress.setFocusPolicy(Qt.NoFocus)
        self.progress.sliderPressed.connect(self._on_progress_pressed)
        self.progress.sliderMoved.connect(self._on_progress_moved)
        self.progress.sliderReleased.connect(self._on_progress_released)
        lay.addWidget(self.progress, 1)

        self.speed_btn = QToolButton()
        self.speed_btn.setText("1.0x")
        self.speed_btn.setPopupMode(QToolButton.InstantPopup)
        self.speed_btn.setToolTip("速度预设")
        menu = QMenu(self.speed_btn)
        for v in SPEED_PRESETS:
            act = menu.addAction(f"{v:.1f}x")
            act.setData(v)
            act.triggered.connect(self._on_preset)
        self.speed_btn.setMenu(menu)
        lay.addWidget(self.speed_btn)

        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(1, 160)  # 0.1 .. 16.0
        self.speed_slider.setValue(10)
        self.speed_slider.setFixedWidth(140)
        self.speed_slider.setToolTip("倍速 (0.1-16)")
        self.speed_slider.setFocusPolicy(Qt.NoFocus)
        self.speed_slider.valueChanged.connect(self._on_speed_slider)
        lay.addWidget(self.speed_slider)

        self.vol_btn = QPushButton("音量")
        self.vol_btn.clicked.connect(self.mute_toggled.emit)
        lay.addWidget(self.vol_btn)

        self.vol_slider = QSlider(Qt.Horizontal)
        self.vol_slider.setRange(0, 100)
        self.vol_slider.setValue(60)
        self.vol_slider.setFixedWidth(100)
        self.vol_slider.setFocusPolicy(Qt.NoFocus)
        self.vol_slider.valueChanged.connect(self._on_vol_slider)
        lay.addWidget(self.vol_slider)

        self.mode_btn = QPushButton("列表循环")
        self.mode_btn.setFixedWidth(72)
        self.mode_btn.clicked.connect(self.mode_cycle_requested.emit)
        lay.addWidget(self.mode_btn)

        self.fullscreen_btn = QPushButton("全屏")
        self.fullscreen_btn.setFixedWidth(52)
        self.fullscreen_btn.clicked.connect(self.fullscreen_requested.emit)
        lay.addWidget(self.fullscreen_btn)

    # -- progress ----------------------------------------------------------
    def _on_progress_pressed(self):
        self._seeking = True

    def _on_progress_moved(self, value):
        t = self._duration * value / 1000.0
        self._set_time_label(t, self._duration)

    def _on_progress_released(self):
        t = self._duration * self.progress.value() / 1000.0
        self._seeking = False
        self.seek_requested.emit(t)

    def set_position(self, pos: float):
        if self._seeking:
            return
        if self._duration > 0:
            self.progress.setValue(int(pos / self._duration * 1000))
        self._set_time_label(pos, self._duration)

    def set_duration(self, dur: float):
        self._duration = dur or 0.0
        self._set_time_label(self.progress.value() / 1000.0 * self._duration, self._duration)

    def _set_time_label(self, pos, dur):
        self.time_label.setText(f"{fmt_time(pos)} / {fmt_time(dur)}")

    # -- speed --------------------------------------------------------------
    def _on_speed_slider(self, value):
        if self._updating:
            return
        v = value / 10.0
        self._set_speed_ui(v, move_slider=False)
        self.speed_changed.emit(v)

    def _on_preset(self):
        act = self.sender()
        v = float(act.data())
        self.set_speed_display(v)
        self.speed_changed.emit(v)

    def set_speed_display(self, v: float):
        self._set_speed_ui(v, move_slider=True)

    def _set_speed_ui(self, v: float, move_slider: bool):
        self._updating = True
        try:
            self.speed_btn.setText(f"{v:.1f}x")
            if move_slider:
                self.speed_slider.setValue(int(round(v * 10)))
        finally:
            self._updating = False

    # -- volume ---------------------------------------------------------------
    def _on_vol_slider(self, value):
        if self._updating:
            return
        self.volume_changed.emit(value)

    def set_volume_display(self, v: int):
        self._updating = True
        try:
            self.vol_slider.setValue(int(v))
        finally:
            self._updating = False

    def set_muted_display(self, muted: bool):
        self.vol_btn.setText("静音" if muted else "音量")

    # -- state ---------------------------------------------------------------
    def set_playing(self, playing: bool):
        self.play_btn.setText("暂停" if playing else "播放")

    def set_mode(self, label: str):
        self.mode_btn.setText(label)