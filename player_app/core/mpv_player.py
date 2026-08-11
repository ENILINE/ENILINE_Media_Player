"""libmpv wrapper embedding into a Qt window handle.

python-mpv runs its own event thread; all mpv callbacks are marshalled to the
UI thread through MpvSignals (queued Qt signals), so UI code never touches mpv
objects from the wrong thread.
"""
import mpv  # requires libmpv on PATH; main.py sets that up before import

from PyQt5.QtCore import QObject, pyqtSignal


class MpvSignals(QObject):
    time_changed = pyqtSignal(float)
    duration_changed = pyqtSignal(float)
    file_loaded = pyqtSignal(str)
    eof_reached = pyqtSignal()
    paused_changed = pyqtSignal(bool)
    playback_error = pyqtSignal(str)


class MpvPlayer:
    def __init__(self, surface_winid):
        self.signals = MpvSignals()
        self._muted = False  # mute state tracked locally; reading mpv's `mute` property can crash
        self._player = mpv.MPV(
            wid=str(int(surface_winid)),
            vo="gpu",
            hwdec="auto",
            af="scaletempo2=max-speed=32.0",
            osc=False,
            input_default_bindings=False,
            input_vo_keyboard=False,
            keep_open="yes",
            volume=60,
        )
        self._player.observe_property("time-pos", self._on_time)
        self._player.observe_property("duration", self._on_duration)
        self._player.observe_property("pause", self._on_pause)
        self._player.observe_property("eof-reached", self._on_eof)
        self._player.register_event_callback(self._on_event)

    # -- mpv callbacks (event thread) -> Qt signals -----------------------
    def _on_time(self, name, value):
        if value is not None:
            self.signals.time_changed.emit(float(value))

    def _on_duration(self, name, value):
        if value is not None:
            self.signals.duration_changed.emit(float(value))

    def _on_pause(self, name, value):
        self.signals.paused_changed.emit(bool(value))

    def _on_eof(self, name, value):
        if value:
            self.signals.eof_reached.emit()

    def _on_event(self, event):
        try:
            d = event.as_dict(decoder=lambda b: b.decode("utf-8", "replace"))
            event_name = d.get("event", "")
            if event_name == "file-loaded":
                self.signals.file_loaded.emit(self._player.path or "")
            elif event_name == "end-file":
                if d.get("reason", 0) == 2:  # error
                    self.signals.playback_error.emit(self._player.path or "")
        except Exception:
            pass

    # -- public API --------------------------------------------------------
    def load(self, path: str, start: bool = True):
        self._player.command("loadfile", path)
        if start:
            self._player.pause = False

    def play(self):
        self._player.pause = False

    def pause(self):
        self._player.pause = True

    def toggle_play(self):
        self._player.pause = not bool(self._player.pause)

    def seek(self, seconds: float, relative: bool = True):
        if relative:
            self._player.command("seek", str(seconds), "relative")
        else:
            self._player.command("seek", str(seconds), "absolute")

    def get_speed(self) -> float:
        v = self._player.speed
        return float(v) if v else 1.0

    def set_speed(self, v: float):
        self._player.speed = float(v)

    def get_volume(self) -> int:
        v = self._player.volume
        return int(v) if v is not None else 0

    def set_volume(self, v: int):
        v = max(0, min(int(v), 130))
        self._player.command("set", "volume", str(v))

    def toggle_mute(self):
        self.set_mute(not self._muted)

    def set_mute(self, on: bool):
        self._muted = bool(on)
        self._player.command("set", "mute", "yes" if self._muted else "no")

    def is_muted(self) -> bool:
        return self._muted

    _BASE_AF = "scaletempo2=max-speed=32.0"

    def set_volume_normalization(self, on: bool):
        if on:
            self._player.af = self._BASE_AF + ",lavfi=[loudnorm=I=-16:TP=-1.5:LRA=11]"
        else:
            self._player.af = self._BASE_AF

    # -- subtitles ------------------------------------------------------------
    def set_sub_visibility(self, on: bool):
        self._player.command("set", "sub-visibility", "yes" if on else "no")

    def apply_subtitle_style(self, style: int):
        if style == 2:
            self._player.command("set", "sub-ass-override", "force")
            self._player.command("set", "sub-color", "#FFFFFF")
            self._player.command("set", "sub-back-color", "#DE18191C")
            self._player.command("set", "sub-border-size", "0")
            self._player.command("set", "sub-shadow-offset", "0")
            self._player.command("set", "sub-blur", "1")
        else:
            self._player.command("set", "sub-ass-override", "force")
            self._player.command("set", "sub-color", "#FFFFFF")
            self._player.command("set", "sub-border-color", "#000000")
            self._player.command("set", "sub-border-size", "3")
            self._player.command("set", "sub-shadow-offset", "0")
            self._player.command("set", "sub-back-color", "0.0")

    def set_sub_pos(self, pos: int):
        """Set subtitle vertical position, 0=top 100=bottom."""
        self._player.command("set", "sub-pos", str(int(max(0, min(100, pos)))))

    # -- position / duration --------------------------------------------------
    def get_position(self) -> float:
        v = self._player.time_pos
        return float(v) if v is not None else 0.0

    def get_duration(self) -> float:
        v = self._player.duration
        return float(v) if v is not None else 0.0

    def is_playing(self) -> bool:
        return not bool(self._player.pause)

    def shutdown(self):
        try:
            self._player.terminate()
        except Exception:
            pass