"""Process-level singleton coordinating multiple MainWindow instances.

Owns the resources that must exist exactly once per process: the shared
Storage, the single-instance IPC server, and the system-wide global hotkey
registration. Each MainWindow keeps its own player, temp playlist, and
playback state.
"""
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QApplication, QMessageBox

from .global_hotkeys import GlobalHotkeyManager
from .ipc import IPCServer
from .storage import Storage


class AppController(QObject):
    playlists_changed = pyqtSignal(object)       # source window
    settings_changed = pyqtSignal(object, dict)  # source window, changed keys

    def __init__(self):
        super().__init__()
        self.storage = Storage()
        self.windows = []
        self.hotkey_host = None

        st = self.storage.load_settings()
        self.hotkey_settings = {
            "play": st.get("hotkey_play", ""),
            "prev": st.get("hotkey_prev", ""),
            "next": st.get("hotkey_next", ""),
        }

        self.hotkey_mgr = GlobalHotkeyManager(self)
        self.hotkey_mgr.play_pause_pressed.connect(lambda: self._broadcast_hotkey("play"))
        self.hotkey_mgr.prev_pressed.connect(lambda: self._broadcast_hotkey("prev"))
        self.hotkey_mgr.next_pressed.connect(lambda: self._broadcast_hotkey("next"))

        self.ipc_server = IPCServer(self)
        self.ipc_server.paths_received.connect(self.handle_remote_paths)

    # -- windows --------------------------------------------------------------
    def create_window(self, startup_paths):
        from ..ui.main_window import MainWindow
        win = MainWindow(self, startup_paths=startup_paths)
        icon = QApplication.instance().windowIcon()
        if icon is not None and not icon.isNull():
            win.setWindowIcon(icon)
        win.show()
        return win

    def handle_remote_paths(self, paths):
        # Any new media open while running -> spawn a fresh window.
        self.create_window(paths)

    def register_window(self, win):
        self.windows.append(win)

    def on_window_shown(self, win):
        if self.hotkey_host is None:
            self.hotkey_host = win
            self.apply_hotkeys(win)

    def unregister_window(self, win):
        if win in self.windows:
            self.windows.remove(win)
        if self.hotkey_host is win:
            self.hotkey_mgr.unregister_all(int(win.winId()))
            self.hotkey_host = self.windows[0] if self.windows else None
            if self.hotkey_host is not None:
                self.apply_hotkeys(self.hotkey_host)
        if not self.windows:
            self.ipc_server.close()
            QApplication.instance().quit()

    # -- hotkeys --------------------------------------------------------------
    def apply_hotkeys(self, source_win=None):
        if self.hotkey_host is None:
            return
        hwnd = int(self.hotkey_host.winId())
        old = dict(self.hotkey_settings)
        result = self.hotkey_mgr.apply(hwnd, self.hotkey_settings)
        self.hotkey_settings = result
        self.update_settings({
            "hotkey_play": result.get("play", ""),
            "hotkey_prev": result.get("prev", ""),
            "hotkey_next": result.get("next", ""),
        })
        failed = []
        for key, label in [("play", "播放/暂停"), ("prev", "上一首"), ("next", "下一首")]:
            if old.get(key) and not result.get(key):
                failed.append(f"{label}: {old[key]}")
        if failed:
            parent = source_win or self.hotkey_host
            QMessageBox.warning(parent, "快捷键注册失败",
                "以下快捷键可能被其他程序占用,已自动禁用:\n" + "\n".join(failed))

    def _broadcast_hotkey(self, kind):
        for w in list(self.windows):
            {
                "play": w._toggle_play,
                "prev": w._play_prev,
                "next": w._play_next,
            }[kind]()

    # -- settings -------------------------------------------------------------
    def update_settings(self, updates):
        data = self.storage.load_settings()
        data.update(updates)
        self.storage.save_settings(data)