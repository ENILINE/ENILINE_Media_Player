from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QAbstractSpinBox,
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from .icons import icon
from .jump_slider import JumpSlider

SPEED_MIN, SPEED_MAX, SPEED_STEP = 0.1, 16.0, 0.1


def fmt_time(seconds: float) -> str:
    if seconds is None or seconds < 0:
        seconds = 0
    s = int(seconds)
    h, rem = divmod(s, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


class Controls(QWidget):
    prev_requested = pyqtSignal()
    play_toggled = pyqtSignal()
    next_requested = pyqtSignal()
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
        outer = QVBoxLayout(self)
        outer.setContentsMargins(8, 4, 8, 6)
        outer.setSpacing(4)

        # ---- row 1: progress ---------------------------------------------
        row1 = QHBoxLayout()
        row1.setSpacing(8)
        self.time_current = QLabel("00:00")
        self.time_current.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.time_current.setMinimumWidth(70)
        self.progress = JumpSlider(Qt.Horizontal)
        self.progress.setRange(0, 1000)
        self.progress.setFocusPolicy(Qt.NoFocus)
        self.progress.sliderPressed.connect(self._on_progress_pressed)
        self.progress.sliderMoved.connect(self._on_progress_moved)
        self.progress.sliderReleased.connect(self._on_progress_released)
        self.time_total = QLabel("00:00")
        self.time_total.setMinimumWidth(70)
        row1.addWidget(self.time_current)
        row1.addWidget(self.progress, 1)
        row1.addWidget(self.time_total)
        outer.addLayout(row1)

        # ---- row 2: transport + volume + speed + mode + fullscreen ------
        row2 = QHBoxLayout()
        row2.setSpacing(8)

        self.prev_btn = QToolButton()
        self.prev_btn.setIcon(icon("prev", size=20))
        self.prev_btn.setToolTip("上一个")
        self.prev_btn.setAutoRaise(True)
        self.prev_btn.setFocusPolicy(Qt.NoFocus)
        self.prev_btn.clicked.connect(self.prev_requested.emit)
        row2.addWidget(self.prev_btn)

        self.play_btn = QToolButton()
        self.play_btn.setIcon(icon("play", size=24))
        self.play_btn.setToolTip("播放/暂停 (空格)")
        self.play_btn.setAutoRaise(True)
        self.play_btn.setFocusPolicy(Qt.NoFocus)
        self.play_btn.clicked.connect(self.play_toggled.emit)
        row2.addWidget(self.play_btn)

        self.next_btn = QToolButton()
        self.next_btn.setIcon(icon("next", size=20))
        self.next_btn.setToolTip("下一个")
        self.next_btn.setAutoRaise(True)
        self.next_btn.setFocusPolicy(Qt.NoFocus)
        self.next_btn.clicked.connect(self.next_requested.emit)
        row2.addWidget(self.next_btn)

        row2.addSpacing(8)

        self.mute_btn = QToolButton()
        self.mute_btn.setIcon(icon("volume", size=20))
        self.mute_btn.setToolTip("静音")
        self.mute_btn.setAutoRaise(True)
        self.mute_btn.setFocusPolicy(Qt.NoFocus)
        self.mute_btn.clicked.connect(self.mute_toggled.emit)
        row2.addWidget(self.mute_btn)

        self.vol_slider = JumpSlider(Qt.Horizontal)
        self.vol_slider.setRange(0, 100)
        self.vol_slider.setValue(60)
        self.vol_slider.setFixedWidth(100)
        self.vol_slider.setToolTip("音量")
        self.vol_slider.setFocusPolicy(Qt.NoFocus)
        self.vol_slider.valueChanged.connect(self._on_vol_slider)
        row2.addWidget(self.vol_slider)

        self.vol_label = QLabel("60")
        self.vol_label.setMinimumWidth(32)
        self.vol_label.setAlignment(Qt.AlignCenter)
        row2.addWidget(self.vol_label)

        row2.addStretch(1)

        self.speed_minus = QToolButton()
        self.speed_minus.setText("−")
        self.speed_minus.setToolTip("倍速 -0.1")
        self.speed_minus.setAutoRepeat(True)
        self.speed_minus.setFocusPolicy(Qt.NoFocus)
        self.speed_minus.clicked.connect(lambda: self.speed_spin.stepBy(-1))
        row2.addWidget(self.speed_minus)

        self.speed_spin = QDoubleSpinBox()
        self.speed_spin.setRange(SPEED_MIN, SPEED_MAX)
        self.speed_spin.setDecimals(1)
        self.speed_spin.setSingleStep(SPEED_STEP)
        self.speed_spin.setSuffix("x")
        self.speed_spin.setValue(1.0)
        self.speed_spin.setFixedWidth(84)
        self.speed_spin.setKeyboardTracking(False)
        self.speed_spin.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.speed_spin.setFocusPolicy(Qt.WheelFocus)
        self.speed_spin.valueChanged.connect(self._on_speed_spin)
        row2.addWidget(self.speed_spin)

        self.speed_plus = QToolButton()
        self.speed_plus.setText("+")
        self.speed_plus.setToolTip("倍速 +0.1")
        self.speed_plus.setAutoRepeat(True)
        self.speed_plus.setFocusPolicy(Qt.NoFocus)
        self.speed_plus.clicked.connect(lambda: self.speed_spin.stepBy(1))
        row2.addWidget(self.speed_plus)

        row2.addSpacing(8)

        self.mode_btn = QPushButton("列表循环")
        self.mode_btn.setFixedWidth(88)
        self.mode_btn.setFocusPolicy(Qt.NoFocus)
        self.mode_btn.clicked.connect(self.mode_cycle_requested.emit)
        row2.addWidget(self.mode_btn)

        self.fullscreen_btn = QToolButton()
        self.fullscreen_btn.setIcon(icon("fullscreen", size=20))
        self.fullscreen_btn.setToolTip("全屏 (F11)")
        self.fullscreen_btn.setAutoRaise(True)
        self.fullscreen_btn.setFocusPolicy(Qt.NoFocus)
        self.fullscreen_btn.clicked.connect(self.fullscreen_requested.emit)
        row2.addWidget(self.fullscreen_btn)

        outer.addLayout(row2)

    # -- progress ----------------------------------------------------------
    def _on_progress_pressed(self):
        self._seeking = True

    def _on_progress_moved(self, value):
        t = self._duration * value / 1000.0
        self.time_current.setText(fmt_time(t))

    def _on_progress_released(self):
        self._seeking = False
        t = self._duration * self.progress.value() / 1000.0
        self.seek_requested.emit(t)

    def set_position(self, pos: float):
        if self._seeking:
            return
        if self._duration > 0:
            self.progress.setValue(int(pos / self._duration * 1000))
        self.time_current.setText(fmt_time(pos))

    def set_duration(self, dur: float):
        self._duration = dur or 0.0
        self.time_total.setText(fmt_time(dur))

    # -- speed ---------------------------------------------------------------
    def _on_speed_spin(self, value):
        if self._updating:
            return
        self.speed_changed.emit(float(value))

    def set_speed_display(self, v: float):
        self._updating = True
        try:
            self.speed_spin.setValue(round(float(v), 1))
        finally:
            self._updating = False

    # -- volume ----------------------------------------------------------------
    def _on_vol_slider(self, value):
        if self._updating:
            return
        self.vol_label.setText(str(value))
        self.volume_changed.emit(value)

    def set_volume_display(self, v: int):
        self._updating = True
        try:
            self.vol_slider.setValue(int(v))
        finally:
            self._updating = False
        self.vol_label.setText(str(int(v)))

    def set_muted_display(self, muted: bool):
        self.mute_btn.setIcon(icon("volume_muted" if muted else "volume", size=20))
        self.mute_btn.setToolTip("取消静音" if muted else "静音")

    # -- state -----------------------------------------------------------------
    def set_playing(self, playing: bool):
        self.play_btn.setIcon(icon("pause" if playing else "play", size=24))
        self.play_btn.setToolTip("暂停" if playing else "播放 (空格)")

    def set_mode(self, label: str):
        self.mode_btn.setText(label)

    def set_fullscreen(self, fs: bool):
        self.fullscreen_btn.setIcon(icon("fullscreen_exit" if fs else "fullscreen", size=20))
        self.fullscreen_btn.setToolTip("退出全屏 (F11)" if fs else "全屏 (F11)")