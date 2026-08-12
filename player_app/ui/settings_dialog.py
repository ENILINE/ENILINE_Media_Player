from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
)


class HotkeyCaptureWidget(QLineEdit):
    """Read-only line edit that captures a key combination on click."""

    captured = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setPlaceholderText("点击后按下快捷键...")
        self.setFocusPolicy(Qt.StrongFocus)

    def mousePressEvent(self, event):
        self.setText("按下快捷键...")
        self.setStyleSheet("background: #3f3f46;")
        super().mousePressEvent(event)

    def keyPressEvent(self, event):
        key = event.key()
        # Backspace / Escape alone: clear the hotkey
        if key in (Qt.Key_Backspace, Qt.Key_Escape):
            mods = int(event.modifiers())
            if mods == 0 or mods == Qt.KeypadModifier:
                self.setText("")
                self.setStyleSheet("")
                self.captured.emit()
                return

        if key in (Qt.Key_Control, Qt.Key_Alt, Qt.Key_Shift, Qt.Key_Meta):
            return
        mods = int(event.modifiers())
        parts = []
        if mods & Qt.ControlModifier:
            parts.append("Ctrl")
        if mods & Qt.AltModifier:
            parts.append("Alt")
        if mods & Qt.ShiftModifier:
            parts.append("Shift")
        if mods & Qt.MetaModifier:
            parts.append("Win")
        key_names = {
            Qt.Key_Space: "Space", Qt.Key_Tab: "Tab", Qt.Key_Return: "Return",
            Qt.Key_Backspace: "Backspace", Qt.Key_Delete: "Delete",
            Qt.Key_Insert: "Insert", Qt.Key_Home: "Home", Qt.Key_End: "End",
            Qt.Key_PageUp: "PageUp", Qt.Key_PageDown: "PageDown",
            Qt.Key_Up: "Up", Qt.Key_Down: "Down", Qt.Key_Left: "Left",
            Qt.Key_Right: "Right", Qt.Key_Escape: "Escape",
            Qt.Key_F1: "F1", Qt.Key_F2: "F2", Qt.Key_F3: "F3", Qt.Key_F4: "F4",
            Qt.Key_F5: "F5", Qt.Key_F6: "F6", Qt.Key_F7: "F7", Qt.Key_F8: "F8",
            Qt.Key_F9: "F9", Qt.Key_F10: "F10", Qt.Key_F11: "F11", Qt.Key_F12: "F12",
            Qt.Key_CapsLock: "CapsLock", Qt.Key_NumLock: "NumLock",
            Qt.Key_ScrollLock: "ScrollLock", Qt.Key_Pause: "Pause",
            Qt.Key_Print: "Print", Qt.Key_Menu: "Menu",
        }
        is_numpad = bool(mods & Qt.KeypadModifier)
        name = key_names.get(key)
        if name is None and Qt.Key_A <= key <= Qt.Key_Z:
            name = chr(key)
        elif name is None and Qt.Key_0 <= key <= Qt.Key_9:
            name = ("Num" if is_numpad else "") + chr(key)
        elif name is None and Qt.Key_Semicolon <= key <= Qt.Key_QuoteLeft:
            name = {
                Qt.Key_Semicolon: ";", Qt.Key_Equal: "=", Qt.Key_Comma: ",",
                Qt.Key_Minus: "-", Qt.Key_Period: ".", Qt.Key_Slash: "/",
                Qt.Key_BracketLeft: "[", Qt.Key_Backslash: "\\",
                Qt.Key_BracketRight: "]", Qt.Key_Apostrophe: "'",
                Qt.Key_QuoteLeft: "`",
            }.get(key, "")
        if is_numpad and not name.startswith("Num"):
            numpad_ops = {Qt.Key_Asterisk: "Num*", Qt.Key_Plus: "Num+",
                          Qt.Key_Minus: "Num-", Qt.Key_Period: "Num.",
                          Qt.Key_Slash: "Num/"}
            name = numpad_ops.get(key, name)
        if name:
            parts.append(name)
        display = "+".join(parts)
        self.setText(display)
        self.setStyleSheet("")
        self.captured.emit()

    def focusOutEvent(self, event):
        if self.text() == "按下快捷键...":
            self.setText("")
            self.setStyleSheet("")
        super().focusOutEvent(event)


class SettingsDialog(QDialog):
    def __init__(self, settings: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.resize(420, 380)
        self._values = dict(settings)

        layout = QVBoxLayout(self)

        # Playback
        gb_play = QGroupBox("播放")
        fl_play = QFormLayout(gb_play)
        self._cb_remember = QCheckBox()
        self._cb_remember.setChecked(self._values.get("remember_position", True))
        fl_play.addRow("记忆播放进度", self._cb_remember)
        layout.addWidget(gb_play)

        # Hotkeys
        gb_hk = QGroupBox("全局快捷键 (留空=禁用)")
        fl_hk = QFormLayout(gb_hk)
        self._hk_play = HotkeyCaptureWidget()
        self._hk_play.setText(self._values.get("hotkey_play", ""))
        self._hk_prev = HotkeyCaptureWidget()
        self._hk_prev.setText(self._values.get("hotkey_prev", ""))
        self._hk_next = HotkeyCaptureWidget()
        self._hk_next.setText(self._values.get("hotkey_next", ""))
        fl_hk.addRow("播放/暂停", self._hk_play)
        fl_hk.addRow("上一首", self._hk_prev)
        fl_hk.addRow("下一首", self._hk_next)
        layout.addWidget(gb_hk)

        # Subtitles
        gb_sub = QGroupBox("字幕")
        fl_sub = QFormLayout(gb_sub)
        self._cb_sub_enabled = QCheckBox()
        self._cb_sub_enabled.setChecked(self._values.get("subtitle_enabled", True))
        fl_sub.addRow("启用字幕", self._cb_sub_enabled)
        self._cmb_sub_style = QComboBox()
        self._cmb_sub_style.addItem("样式1 — 黑边白字")
        self._cmb_sub_style.addItem("样式2 — 白字黑底")
        self._cmb_sub_style.setCurrentIndex(self._values.get("subtitle_style", 1) - 1)
        fl_sub.addRow("字幕样式", self._cmb_sub_style)
        layout.addWidget(gb_sub)

        # Audio
        gb_audio = QGroupBox("音频")
        fl_audio = QFormLayout(gb_audio)
        self._cb_norm = QCheckBox()
        self._cb_norm.setChecked(self._values.get("volume_normalization", False))
        fl_audio.addRow("音量平衡 (EBU R128)", self._cb_norm)
        layout.addWidget(gb_audio)

        # System
        gb_sys = QGroupBox("系统")
        fl_sys = QFormLayout(gb_sys)
        self._cb_tray = QCheckBox()
        self._cb_tray.setChecked(self._values.get("close_to_tray", False))
        fl_sys.addRow("关闭时最小化到任务栏", self._cb_tray)
        layout.addWidget(gb_sys)

    def _save(self):
        self._values["remember_position"] = self._cb_remember.isChecked()
        self._values["subtitle_enabled"] = self._cb_sub_enabled.isChecked()
        self._values["subtitle_style"] = self._cmb_sub_style.currentIndex() + 1
        self._values["volume_normalization"] = self._cb_norm.isChecked()
        self._values["close_to_tray"] = self._cb_tray.isChecked()
        self._values["hotkey_play"] = self._hk_play.text()
        self._values["hotkey_prev"] = self._hk_prev.text()
        self._values["hotkey_next"] = self._hk_next.text()

    def _check_conflicts(self) -> list[str]:
        """Check for duplicate hotkey assignments. Returns list of conflict descriptions."""
        keys = [
            ("播放/暂停", self._hk_play.text()),
            ("上一首", self._hk_prev.text()),
            ("下一首", self._hk_next.text()),
        ]
        warnings = []
        seen = {}
        for label, text in keys:
            if not text:
                continue
            if text in seen:
                warnings.append(f"「{seen[text]}」和「{label}」快捷键冲突: {text}")
            else:
                seen[text] = label
        return warnings

    def closeEvent(self, event):
        conflicts = self._check_conflicts()
        if conflicts:
            QMessageBox.warning(self, "快捷键冲突", "\n".join(conflicts))
        self._save()
        self.accept()
        super().closeEvent(event)

    def values(self) -> dict:
        return dict(self._values)