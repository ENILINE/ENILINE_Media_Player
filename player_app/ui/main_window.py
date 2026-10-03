import random

from PyQt5.QtCore import QByteArray, QEvent, Qt, QTimer
from PyQt5.QtWidgets import (
    QAbstractSpinBox,
    QApplication,
    QComboBox,
    QHBoxLayout,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..core.commands import (
    add_entries_cmd,
    copy_playlist_cmd,
    create_playlist_cmd,
    delete_playlist_cmd,
    paste_cmd,
    remove_entries_cmd,
    rename_entry_cmd,
    rename_playlist_cmd,
    UndoRedoStack,
)
from ..core.mpv_player import MpvPlayer
from ..core.playlist_model import Entry, Playlist, PlaylistCollection, is_media_file
from ..core.speed import speed_for_turbo
from .controls import Controls
from .playlist_panel import PlaylistPanel
from .video_surface import VideoSurface

MODE_ONCE = 0
MODE_LIST_LOOP = 1
MODE_SINGLE_LOOP = 2
MODE_SHUFFLE = 3
MODE_LABELS = ["播完暂停", "列表循环", "单集循环", "随机播放"]

TURBO_HOLD_MS = 250


class MainWindow(QMainWindow):
    def __init__(self, controller, startup_paths=None):
        super().__init__()
        self.setWindowTitle("ENILINE Media Player")
        self.resize(1100, 700)

        self.controller = controller
        self.storage = controller.storage
        self.collection = PlaylistCollection.from_dict(self.storage.load_playlists())
        self._ensure_builtin_lists()
        self.stack = UndoRedoStack()
        self.player = None

        self.current_pid = None
        self.playing_pid = None
        self.playing_index = -1
        self.playback_mode = MODE_LIST_LOOP
        self.clipboard = None
        self._current_path = None
        self._at_eof = False

        self._turbo_active = False
        self._base_speed = 1.0
        self._right_pressed = False
        self._right_timer = QTimer(self)
        self._right_timer.setSingleShot(True)
        self._right_timer.timeout.connect(self._on_right_long_press)
        self._right_ctrl = False
        self._right_long_press = False
        self._refresh_queued = False

        self._startup_paths = startup_paths or []
        self._fullscreen_hide_timer = QTimer(self)
        self._fullscreen_hide_timer.setSingleShot(True)
        self._fullscreen_hide_timer.timeout.connect(self._hide_controls_fs)
        self._controls_hovered = False

        self._subtitle_enabled = True
        self._subtitle_style = 1
        self._subtitle_pos = 100
        self._error_queue = []          # paths queued for error popup
        self._error_processing = False  # prevent cascading error handlers
        self._error_popup_open = False  # prevent duplicate popups

        self._load_timeout_timer = QTimer(self)
        self._load_timeout_timer.setSingleShot(True)
        self._load_timeout_timer.timeout.connect(self._on_load_timeout)

        self.controller.playlists_changed.connect(self._on_playlists_changed)
        self.controller.settings_changed.connect(self._on_remote_settings)

        self._build_ui()
        self._load_settings()
        if self._pending_splitter_sizes:
            self.splitter.setSizes(self._pending_splitter_sizes)
        self._wire_controls()
        self._refresh_panel()

        app = QApplication.instance()
        app.installEventFilter(self)

        self._resume_timer = QTimer(self)
        self._resume_timer.setInterval(5000)
        self._resume_timer.timeout.connect(self._save_resume)
        self._resume_timer.start()

        self._sub_pos_save_timer = QTimer(self)
        self._sub_pos_save_timer.setSingleShot(True)
        self._sub_pos_save_timer.setInterval(500)
        self._sub_pos_save_timer.timeout.connect(self._save_sub_pos)

        self.controller.register_window(self)

    def _ensure_builtin_lists(self):
        import os as _os
        self.collection.playlists = [p for p in self.collection.playlists if not p.is_temp]
        temp = Playlist("临时列表", is_temp=True)
        self.collection.playlists.insert(0, temp)
        if not _os.path.exists(self.storage.playlists_path):
            default = Playlist("默认列表")
            self.collection.playlists.insert(1, default)

    # -- UI construction ----------------------------------------------------
    def _build_ui(self):
        self.video_surface = VideoSurface()
        self.video_surface.files_dropped.connect(self._on_video_drop)
        self.video_surface.settings_requested.connect(self._open_settings)
        self.video_surface.about_requested.connect(self._show_about)
        self.video_surface.browse_file_requested.connect(self._browse_file)
        self.video_surface.subtitle_pos_changed.connect(self._on_sub_pos_dragged)
        self.controls = Controls()

        self.panel = PlaylistPanel()
        self.panel.playlist_selected.connect(self.select_playlist)
        self.panel.play_requested.connect(self.play_index)
        self.panel.add_paths_requested.connect(self.add_paths)
        self.panel.cut_requested.connect(self.cut_entries)
        self.panel.copy_requested.connect(self.copy_entries)
        self.panel.paste_requested.connect(self.paste_entries)
        self.panel.remove_requested.connect(self.remove_entries)
        self.panel.create_requested.connect(self.create_playlist)
        self.panel.delete_requested.connect(self.delete_playlist)
        self.panel.rename_list_requested.connect(self.rename_playlist)
        self.panel.copy_list_requested.connect(self.copy_playlist)
        self.panel.rename_entry_requested.connect(self.rename_entry)
        self.panel.browse_file_requested.connect(self._browse_file)
        self.panel.clean_invalid_requested.connect(self._clean_invalid)
        self.panel.dedupe_requested.connect(self._dedupe)
        self.panel.sort_by_name_requested.connect(self._sort_by_name)
        self.panel.sort_by_mtime_requested.connect(self._sort_by_mtime)
        self.panel.sort_by_duration_requested.connect(self._sort_by_duration)
        self.panel.shuffle_requested.connect(self._shuffle_list)

        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setHandleWidth(3)
        self.splitter.addWidget(self.panel)
        self.splitter.addWidget(self.video_surface)
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setSizes([260, 740])
        self.splitter.splitterMoved.connect(self._on_splitter_moved)

        central = QWidget()
        central.setMouseTracking(True)
        v = QVBoxLayout(central)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)
        v.addWidget(self.splitter, 1)
        v.addWidget(self.controls)
        self.setCentralWidget(central)

    def _on_splitter_moved(self):
        self.panel.update()
        self.panel.tree.update()
        self.video_surface.update()

    def _hide_controls_fs(self):
        if self.isFullScreen() and not self._controls_hovered:
            self.controls.hide()

    def _show_controls_fs(self):
        if self.isFullScreen():
            self.controls.show()
            self._fullscreen_hide_timer.start(1500)

    def showEvent(self, event):
        super().showEvent(event)
        if self.player is None:
            self.player = MpvPlayer(self.video_surface.winId())
            self.player.set_volume(self._stored_volume)
            if not self._subtitle_enabled:
                self.player.set_sub_visibility(False)
            self.player.apply_subtitle_style(self._subtitle_style)
            self.player.set_sub_pos(self._subtitle_pos)
            self._connect_player()
            self._process_startup_paths()
        self.controller.on_window_shown(self)

    def _process_startup_paths(self):
        if not self._startup_paths:
            return
        paths = self._startup_paths
        self._startup_paths = []
        entries = self._collect_media_from_paths(paths)
        if entries:
            temp_pid = self._temp_list_pid()
            if temp_pid:
                self._run(add_entries_cmd(self.collection, temp_pid, entries))
                self._play_index(temp_pid, 0)

    def _temp_list_pid(self):
        for p in self.collection.playlists:
            if p.is_temp:
                return p.id
        return None

    def _collect_media_from_paths(self, paths):
        import os as _os
        entries = []
        seen = set()
        for p in paths:
            p = _os.path.abspath(p)
            if _os.path.isfile(p) and is_media_file(p):
                if p not in seen:
                    entries.append(Entry(p))
                    seen.add(p)
            elif _os.path.isdir(p):
                for root, _dirs, files in _os.walk(p):
                    for f in files:
                        fp = _os.path.join(root, f)
                        if is_media_file(fp) and fp not in seen:
                            entries.append(Entry(fp))
                            seen.add(fp)
        return entries

    def _connect_player(self):
        s = self.player.signals
        s.time_changed.connect(self.controls.set_position)
        s.duration_changed.connect(self.controls.set_duration)
        s.paused_changed.connect(self._on_pause_changed)
        s.file_loaded.connect(self._on_file_loaded)
        s.eof_reached.connect(self._on_eof)
        s.playback_error.connect(self._on_playback_error)
        self.controls.seek_requested.connect(self._on_controls_seek)
        self._error_count = 0

    def _wire_controls(self):
        self.controls.play_toggled.connect(self._toggle_play)
        self.controls.prev_requested.connect(self._play_prev)
        self.controls.next_requested.connect(self._play_next)
        self.controls.speed_changed.connect(lambda v: self.player and self.player.set_speed(v))
        self.controls.volume_changed.connect(self._on_volume_change)
        self.controls.mute_toggled.connect(self._toggle_mute)
        self.controls.mode_cycle_requested.connect(self._cycle_mode)
        self.controls.fullscreen_requested.connect(self._toggle_fullscreen)

    # -- settings / persistence ----------------------------------------------
    def _load_settings(self):
        st = self.storage.load_settings()
        mode = st.get("mode", MODE_LIST_LOOP)
        if mode not in MODE_LABELS:
            mode = MODE_LIST_LOOP
        self.playback_mode = mode
        self.controls.set_mode(MODE_LABELS[mode])
        self._stored_volume = st.get("volume", 60)
        self.controls.set_volume_display(self._stored_volume)
        self._last_pid = st.get("last_pid")
        self._last_index = st.get("last_index", -1)
        if self._last_pid and self.collection.find(self._last_pid):
            self.current_pid = self._last_pid
        geo_hex = st.get("geometry")
        if geo_hex:
            try:
                from PyQt5.QtCore import QByteArray
                self.restoreGeometry(QByteArray(bytes.fromhex(geo_hex)))
            except Exception:
                pass
        sizes = st.get("splitter_sizes")
        if sizes and isinstance(sizes, list) and len(sizes) == 2:
            self._pending_splitter_sizes = sizes
        else:
            self._pending_splitter_sizes = None
        self._subtitle_enabled = st.get("subtitle_enabled", True)
        self._subtitle_style = st.get("subtitle_style", 1)
        self._subtitle_pos = st.get("subtitle_pos", 100)

    def _update_settings(self, updates: dict):
        data = self.storage.load_settings()
        data.update(updates)
        self.storage.save_settings(data)

    def _save_settings(self):
        self._update_settings({
            "mode": self.playback_mode,
            "volume": self.player.get_volume() if self.player else 60,
            "last_pid": self.current_pid,
            "last_index": self.playing_index,
        })

    # -- mpv signal handlers --------------------------------------------------
    def _on_pause_changed(self, paused):
        if self.player:
            self.controls.set_playing(self.player.is_playing() and not self._at_eof)
        if paused:
            self._save_resume()

    def _on_file_loaded(self, path):
        self._load_timeout_timer.stop()
        self._current_path = path
        self._error_count = 0
        self._error_processing = False
        self._error_queue.clear()
        self.video_surface.set_current_path(path)
        self.controls.set_playing(True)
        settings = self.storage.load_settings()
        if settings.get("remember_position", True):
            pos = self.storage.load_resume().get(path)
            if pos:
                QTimer.singleShot(300, lambda: self._apply_resume(path, pos))

    def _apply_resume(self, path, pos):
        if self._current_path != path or not self.player:
            return
        dur = self.player.get_duration()
        if pos > 10 and (dur <= 0 or dur - pos > 5):
            self.player.seek(pos, relative=False)

    def _on_eof(self):
        self._at_eof = True
        self.controls.set_playing(False)
        if self.playback_mode == MODE_SINGLE_LOOP:
            self.player.seek(0, relative=False)
            self.player.play()
            self._at_eof = False
            self.controls.set_playing(True)
        elif self.playback_mode in (MODE_LIST_LOOP, MODE_SHUFFLE):
            nxt = self._next_index()
            if nxt is not None:
                self._play_index(self.playing_pid, nxt)

    def _next_index(self):
        pl = self.collection.find(self.playing_pid)
        if pl is None or not pl.entries:
            return None
        n = len(pl.entries)
        if self.playback_mode == MODE_SHUFFLE:
            if n == 1:
                return self.playing_index
            return random.choice([i for i in range(n) if i != self.playing_index])
        nxt = self.playing_index + 1
        if nxt >= n:
            nxt = 0
        return nxt

    # -- playback --------------------------------------------------------------
    def _toggle_play(self):
        if not self.player:
            return
        if self._at_eof:
            self._at_eof = False
            self.player.seek(0, relative=False)
            self.player.play()
            self.controls.set_playing(True)
            return
        self.player.toggle_play()

    def _on_controls_seek(self, t):
        if not self.player or not self._current_path:
            return
        self._at_eof = False
        self.player.seek(t, relative=False)
        self.player.play()
        self.controls.set_playing(True)

    def _seek(self, seconds):
        if not self.player or not self._current_path:
            return
        was_eof = self._at_eof
        self._at_eof = False
        self.player.seek(seconds)
        if was_eof:
            self.player.play()

    def _on_volume_change(self, v):
        if self.player:
            self.player.set_volume(v)
            if self.player.is_muted():
                self.player.set_mute(False)
                self.controls.set_muted_display(False)
            self.controls.set_volume_display(v)
            self.controller.settings_changed.emit(self, {"volume": v})

    def _toggle_mute(self, force_unmute=False):
        if self.player:
            if force_unmute and self.player.is_muted():
                self.player.set_mute(False)
                self.controls.set_muted_display(False)
                self.controls.set_volume_display(self.player.get_volume())
            elif not force_unmute:
                self.player.toggle_mute()
                muted = self.player.is_muted()
                self.controls.set_muted_display(muted)
                if muted:
                    self.controls.set_volume_display(0)
                else:
                    self.controls.set_volume_display(self.player.get_volume())

    def _cycle_mode(self):
        self.playback_mode = (self.playback_mode + 1) % len(MODE_LABELS)
        self.controls.set_mode(MODE_LABELS[self.playback_mode])
        self._save_settings()
        self.controller.settings_changed.emit(self, {"mode": self.playback_mode})

    def _toggle_fullscreen(self):
        if self.isFullScreen():
            self._fullscreen_hide_timer.stop()
            self.controls.show()
            self.showNormal()
            self.panel.show()
            self.controls.set_fullscreen(False)
        else:
            self.panel.hide()
            self.showFullScreen()
            self.controls.set_fullscreen(True)
            self.controls.show()
            self._fullscreen_hide_timer.start(1500)

    def play_index(self, pid, index):
        self._play_index(pid, index)

    def _play_index(self, pid, index):
        pl = self.collection.find(pid)
        if pl is None or not (0 <= index < len(pl.entries)):
            return
        if self._current_path:
            self._save_resume()
        self.playing_pid = pid
        self.playing_index = index
        self.current_pid = pid
        self._at_eof = False
        path = pl.entries[index].path
        import os as _os
        if not _os.path.isfile(path):
            self._cancel_right_press()
            self._on_playback_error(path)
            return
        self._cancel_right_press(resync=False)  # loading the next file flushes audio
        self._current_path = None  # cleared until file-loaded confirms; keeps a stale path from surviving a failed load
        self._loading_path = path
        self.player.load(path)
        self._load_timeout_timer.start(4000)  # 4s timeout for invalid formats
        self.controls.set_playing(True)
        self._refresh_panel()

    def _play_prev(self):
        self._advance_play(-1)

    def _play_next(self):
        self._advance_play(1)

    def _advance_play(self, direction):
        if not self.player:
            return
        pid = self.playing_pid or self.current_pid
        pl = self.collection.find(pid)
        if pl is None or not pl.entries:
            return
        n = len(pl.entries)
        cur = self.playing_index if self.playing_pid == pl.id else -1
        if direction > 0 and self.playback_mode == MODE_SHUFFLE and n > 1 and cur >= 0:
            nxt = random.choice([i for i in range(n) if i != cur])
        elif direction > 0:
            nxt = (cur + 1) % n
        else:
            nxt = (cur - 1) if cur > 0 else n - 1
        self._play_index(pl.id, nxt)

    def select_playlist(self, pid):
        # Called from the tree's selection-changed signal; must not rebuild the
        # tree (that would clear() it from inside its own signal handler).
        self.current_pid = pid

    def _refresh_panel(self):
        # Defer to the next event-loop turn: rebuilds clear() the tree, which
        # must not happen while Qt is still inside a widget event handler
        # (e.g. the tree's own keyPressEvent after Ctrl+X / Delete).
        if self._refresh_queued:
            return
        self._refresh_queued = True
        QTimer.singleShot(0, self._do_refresh_panel)

    def _do_refresh_panel(self):
        self._refresh_queued = False
        hi = self.playing_index if self.playing_pid == self.current_pid else None
        self.panel.refresh(self.collection, self.current_pid, hi, self.playing_pid)

    # -- playlist operations (undoable) ----------------------------------------
    def _run(self, cmd):
        if cmd is None:
            return
        self.stack.execute(cmd)
        self._after_change()

    def _after_change(self):
        self._validate_state()
        self.storage.save_playlists(self.collection)
        self.controller.playlists_changed.emit(self)
        self._refresh_panel()
        self._save_settings()

    def _validate_state(self):
        if self.current_pid and self.collection.find(self.current_pid) is None:
            self.current_pid = self.collection.playlists[0].id if self.collection.playlists else None
        if self.playing_pid:
            pl = self.collection.find(self.playing_pid)
            if pl is None:
                self.playing_pid = None
                self.playing_index = -1
            elif self.playing_index >= len(pl.entries):
                self.playing_index = -1

    def create_playlist(self, name):
        name = (name or "").strip()
        if not name:
            return
        cmd, pid = create_playlist_cmd(self.collection, name)
        self._run(cmd)
        self.current_pid = pid
        self._refresh_panel()

    def delete_playlist(self, pid):
        pl = self.collection.find(pid)
        if pl is None:
            return
        if pl.is_temp:
            return
        ret = QMessageBox.question(
            self, "删除播放列表",
            f"确定删除列表「{pl.name}」吗?本地文件不会被修改。",
        )
        if ret != QMessageBox.Yes:
            return
        if self.playing_pid == pid:
            if self.player:
                self.player.pause()
            self.playing_pid = None
            self.playing_index = -1
        if self.current_pid == pid:
            self.current_pid = None
        cmd = delete_playlist_cmd(self.collection, pid)
        self._run(cmd)

    def rename_playlist(self, pid, new_name):
        pl = self.collection.find(pid)
        new_name = (new_name or "").strip()
        if pl is None or not new_name or new_name == pl.name:
            return
        self._run(rename_playlist_cmd(self.collection, pid, new_name))

    def copy_playlist(self, pid):
        cmd, new_id = copy_playlist_cmd(self.collection, pid)
        self._run(cmd)
        if new_id:
            self.current_pid = new_id
            self._refresh_panel()

    def _on_video_drop(self, paths):
        entries = self._collect_media_from_paths(paths)
        if entries:
            temp_pid = self._temp_list_pid()
            if temp_pid:
                self._run(add_entries_cmd(self.collection, temp_pid, entries))
                if not self._current_path:
                    self._play_index(temp_pid, 0)

    def add_paths(self, pid, paths):
        entries = [Entry(p) for p in paths if p and is_media_file(p)]
        if not entries:
            return
        was_empty = not self._current_path
        pl = self.collection.find(pid)
        old_len = len(pl.entries) if pl else 0
        self._run(add_entries_cmd(self.collection, pid, entries))
        if was_empty and pl and pl.is_temp:
            self._play_index(pid, old_len)

    def remove_entries(self, pid, indices):
        cmd = remove_entries_cmd(self.collection, pid, indices)
        if cmd is None:
            return
        removed_before = sum(1 for i in indices if self.playing_pid == pid and i < self.playing_index)
        removed_self = self.playing_pid == pid and self.playing_index in indices
        self._run(cmd)
        if removed_self:
            self.playing_index = -1
        elif removed_before:
            self.playing_index -= removed_before

    def cut_entries(self, pid, indices):
        pl = self.collection.find(pid)
        if pl is None or not indices:
            return
        snapshot = [Entry(pl.entries[i].path, pl.entries[i].display_name) for i in indices]
        self.clipboard = {"mode": "cut", "entries": snapshot}
        self.remove_entries(pid, indices)

    def copy_entries(self, pid, indices):
        pl = self.collection.find(pid)
        if pl is None or not indices:
            return
        snapshot = [Entry(pl.entries[i].path, pl.entries[i].display_name) for i in indices]
        self.clipboard = {"mode": "copy", "entries": snapshot}

    def paste_entries(self, pid):
        if not self.clipboard:
            return
        cmd = paste_cmd(self.collection, pid, self.clipboard["entries"])
        self._run(cmd)
        if self.clipboard.get("mode") == "cut":
            self.clipboard = None

    def rename_entry(self, pid, index, new_name):
        pl = self.collection.find(pid)
        new_name = (new_name or "").strip()
        if pl is None or not (0 <= index < len(pl.entries)):
            return
        if new_name and new_name != pl.entries[index].display_name:
            self._run(rename_entry_cmd(self.collection, pid, index, new_name))

    def undo(self):
        if self.stack.undo():
            self._after_change()

    def redo(self):
        if self.stack.redo():
            self._after_change()

    # -- resume ---------------------------------------------------------------
    def _save_resume(self):
        if not self.player or not self._current_path:
            return
        settings = self.storage.load_settings()
        if not settings.get("remember_position", True):
            return
        pos = self.player.get_position()
        dur = self.player.get_duration()
        r = self.storage.load_resume()
        if pos > 10 and (dur <= 0 or pos < dur - 5):
            r[self._current_path] = round(pos, 1)
        else:
            r.pop(self._current_path, None)
        self.storage.save_resume(r)

    # -- keyboard handling -------------------------------------------------------
    def _is_text_input_focused(self):
        w = QApplication.focusWidget()
        return isinstance(w, (QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QAbstractSpinBox))

    def _tree_has_focus(self):
        fw = QApplication.focusWidget()
        return fw is not None and self.panel.isAncestorOf(fw) and not self._is_text_input_focused()

    def nativeEvent(self, eventType, message):
        """Forward WM_HOTKEY to the controller's hotkey manager."""
        import ctypes
        msg = ctypes.wintypes.MSG.from_address(int(message))
        return self.controller.hotkey_mgr.handle(msg.hWnd, msg.message, msg.wParam, msg.lParam)

    def eventFilter(self, obj, event):
        if event.type() in (QEvent.KeyPress, QEvent.KeyRelease):
            # Normal shortcuts go to the active window only.
            if QApplication.activeWindow() is not self:
                return False
            if event.type() == QEvent.KeyPress:
                return self._on_key_press(event)
            return self._on_key_release(event)

        if isinstance(obj, QWidget) and obj.window() is not self:
            return False
        if event.type() == QEvent.WindowDeactivate and self._right_pressed:
            self._cancel_right_press()
        if QApplication.activePopupWidget() is not None:
            return False
        if event.type() == QEvent.MouseMove and self.isFullScreen():
            self._show_controls_fs()
            local = self.controls.mapFromGlobal(event.globalPos())
            self._controls_hovered = self.controls.rect().contains(local)
        return False

    def _on_key_press(self, event):
        if self._is_text_input_focused():
            return False
        key = event.key()
        ctrl = bool(event.modifiers() & Qt.ControlModifier)

        if ctrl and key == Qt.Key_Z:
            if event.modifiers() & Qt.ShiftModifier:
                self.redo()
            else:
                self.undo()
            return True
        if ctrl and key == Qt.Key_Y:
            self.redo()
            return True
        if key == Qt.Key_Space:
            self._toggle_play()
            return True
        if key == Qt.Key_F11:
            self._toggle_fullscreen()
            return True
        if key == Qt.Key_Escape and self.isFullScreen():
            self._toggle_fullscreen()
            return True
        if self._tree_has_focus():
            return False  # arrows / delete / ctrl+x/c/v / enter -> tree handles them
        if key == Qt.Key_Left:
            self._seek(-30 if ctrl else -5)
            return True
        if key == Qt.Key_Right:
            if event.isAutoRepeat() or self._right_pressed:
                return True
            if not self.player or not self._current_path:
                return True
            self._right_pressed = True
            self._right_ctrl = ctrl
            self._right_long_press = False
            self._enter_turbo()
            self._right_timer.start(TURBO_HOLD_MS)
            return True
        if key == Qt.Key_Up:
            if self.player:
                if self.player.is_muted():
                    self.player.set_mute(False)
                    self.controls.set_muted_display(False)
                v = min(self.player.get_volume() + 5, 130)
                self.player.set_volume(v)
                self.controls.set_volume_display(v)
            return True
        if key == Qt.Key_Down:
            if self.player:
                if self.player.is_muted():
                    self.player.set_mute(False)
                    self.controls.set_muted_display(False)
                self.player.set_volume(self.player.get_volume() - 5)
                self.controls.set_volume_display(self.player.get_volume())
            return True
        return False

    def _on_key_release(self, event):
        if event.key() == Qt.Key_Right and not event.isAutoRepeat():
            if not self._right_pressed:
                return True
            was_long = self._right_long_press
            ctrl = self._right_ctrl
            self._cancel_right_press(resync=was_long)  # a short press seeks next
            if not was_long:
                self._seek(30 if ctrl else 5)
            return True
        if self._is_text_input_focused():
            return False
        if self._tree_has_focus():
            return False
        return False

    def _cancel_right_press(self, resync=True):
        self._right_timer.stop()
        if self._turbo_active:
            self.player.stop_turbo(self._base_speed, refresh_audio=resync)
            self.controls.set_speed_display(self._base_speed)
            self._turbo_active = False
        self._right_pressed = False
        self._right_long_press = False
        self._right_ctrl = False

    def _enter_turbo(self):
        self._turbo_active = True
        self._base_speed = self.player.get_speed()
        self.player.start_turbo(speed_for_turbo(self._base_speed))

    def _on_right_long_press(self):
        self._right_long_press = True

    # -- context menu actions --------------------------------------------------
    def _open_settings(self):
        from .settings_dialog import SettingsDialog
        hk = self.controller.hotkey_settings
        settings = {
            "remember_position": self.storage.load_settings().get("remember_position", True),
            "subtitle_enabled": self._subtitle_enabled,
            "subtitle_style": self._subtitle_style,
            "hotkey_play": hk.get("play", ""),
            "hotkey_prev": hk.get("prev", ""),
            "hotkey_next": hk.get("next", ""),
        }
        dlg = SettingsDialog(settings, self)
        if dlg.exec_():
            vals = dlg.values()
            self._subtitle_enabled = vals["subtitle_enabled"]
            self._subtitle_style = vals["subtitle_style"]
            self.controller.hotkey_settings = {
                "play": vals["hotkey_play"],
                "prev": vals["hotkey_prev"],
                "next": vals["hotkey_next"],
            }
            self._apply_subtitle_settings()
            self.controller.apply_hotkeys(self)
            self.controller.update_settings({
                "remember_position": vals["remember_position"],
                "subtitle_enabled": vals["subtitle_enabled"],
                "subtitle_style": vals["subtitle_style"],
                "hotkey_play": vals["hotkey_play"],
                "hotkey_prev": vals["hotkey_prev"],
                "hotkey_next": vals["hotkey_next"],
            })
            self.controller.settings_changed.emit(self, {
                "subtitle_enabled": vals["subtitle_enabled"],
                "subtitle_style": vals["subtitle_style"],
            })

    def _show_about(self):
        QMessageBox.about(
            self, "关于",
            "ENILINE Media Player\n\nhttps://github.com/ENILINE/ENILINE_Media_Player",
        )

    def _browse_file(self, path):
        import os as _os
        if not path or not _os.path.isfile(path):
            ret = QMessageBox.question(
                self, "文件不存在",
                f"找不到文件:\n{path}\n\n是否从列表中删除？",
            )
            if ret == QMessageBox.Yes:
                self._remove_by_path(path)
            return
        from .video_surface import open_file_location
        open_file_location(path)

    def _remove_by_path(self, path):
        """Remove an entry by path from whatever playlist contains it."""
        import os as _os
        norm = _os.path.normcase(path)
        for pl in self.collection.playlists:
            for i, e in enumerate(pl.entries):
                if _os.path.normcase(e.path) == norm:
                    cmd = remove_entries_cmd(self.collection, pl.id, [i])
                    if cmd:
                        self._run(cmd)
                    return

    def _on_playback_error(self, path):
        self.controls.set_playing(False)
        self._load_timeout_timer.stop()
        self._error_count += 1
        self._error_queue.append(path)
        if not self._error_processing:
            self._error_processing = True
            QTimer.singleShot(0, self._process_errors)

    def _on_load_timeout(self):
        """mpv didn't emit file-loaded within 4s — treat as playback error."""
        path = getattr(self, "_loading_path", "")
        if path:
            self._on_playback_error(path)

    def _process_errors(self):
        pl = self.collection.find(self.playing_pid)
        total = len(pl.entries) if pl else 0

        # Skip through consecutive invalid files.
        # _play_index triggers _on_playback_error for each bad file; stop
        # when a load succeeds (no new error added) or the list is exhausted.
        while self._error_count < total:
            nxt = self._next_index_internal()
            if nxt is None:
                break
            err_before = self._error_count
            self._play_index(self.playing_pid, nxt)
            if self._error_count == err_before:
                break  # file accepted, wait for mpv async result

        if self._error_count >= total:
            self._error_count = 0
            self._error_queue.clear()
            self._error_processing = False
            if self.player:
                self.player.pause()
            QMessageBox.warning(self, "播放失败", "当前列表中所有文件均无法播放。")
            return

        # Show popup for the first error (the one user clicked on)
        if self._error_queue and not self._error_popup_open:
            path = self._error_queue[0]
            self._error_queue.clear()
            self._error_popup_open = True
            ret = QMessageBox.question(
                self, "播放失败",
                f"无法播放:\n{path}\n\n是否从列表中删除？",
            )
            if ret == QMessageBox.Yes:
                self._remove_by_path(path)
            self._error_popup_open = False

        self._error_processing = False

    def _next_index_internal(self):
        """Return the next index to play (1 step forward). Doesn't play it."""
        pl = self.collection.find(self.playing_pid)
        if pl is None or not pl.entries:
            return None
        n = len(pl.entries)
        cur = self.playing_index if self.playing_pid == pl.id else -1
        nxt = (cur + 1) % n
        return nxt

    def _clean_invalid(self, pid):
        pl = self.collection.find(pid)
        if pl is None:
            return
        pl.remove_invalid()
        self._playlist_op_done(pid)

    def _dedupe(self, pid):
        pl = self.collection.find(pid)
        if pl is None:
            return
        pl.dedupe()
        self._playlist_op_done(pid)

    def _sort_by_name(self, pid):
        pl = self.collection.find(pid)
        if pl is None:
            return
        pl.sort_by_name()
        self._playlist_op_done(pid)

    def _sort_by_mtime(self, pid):
        pl = self.collection.find(pid)
        if pl is None:
            return
        pl.sort_by_mtime()
        self._playlist_op_done(pid)

    def _sort_by_duration(self, pid):
        pl = self.collection.find(pid)
        if pl is None:
            return
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            pl.sort_by_duration()
        finally:
            QApplication.restoreOverrideCursor()
        self._playlist_op_done(pid)

    def _shuffle_list(self, pid):
        pl = self.collection.find(pid)
        if pl is None:
            return
        pl.shuffle()
        self._playlist_op_done(pid)

    def _playlist_op_done(self, pid, msg=None):
        # Update playing_index if the playing entry moved
        if self.playing_pid == pid and self.playing_index >= 0:
            pl = self.collection.find(pid)
            if pl and self._current_path:
                import os as _os
                norm = _os.path.normcase(self._current_path)
                for i, e in enumerate(pl.entries):
                    if _os.path.normcase(e.path) == norm:
                        self.playing_index = i
                        break
                else:
                    self.playing_index = -1
        self.storage.save_playlists(self.collection)
        self.controller.playlists_changed.emit(self)
        self._refresh_panel()
        self._save_settings()
        if msg:
            self.statusBar().showMessage(msg, 3000)

    # -- cross-window sync ------------------------------------------------------
    def _on_playlists_changed(self, source):
        if source is self:
            return
        named_new = [p.to_dict() for p in PlaylistCollection.from_dict(self.storage.load_playlists()).playlists if not p.is_temp]
        named_cur = [p.to_dict() for p in self.collection.playlists if not p.is_temp]
        if named_new == named_cur:
            return
        temp = next((p for p in self.collection.playlists if p.is_temp), Playlist("临时列表", is_temp=True))
        self.collection.playlists[:] = [temp] + [Playlist.from_dict(d) for d in named_new]
        self.stack = UndoRedoStack()
        self._validate_state()
        self._refresh_panel()

    def _on_remote_settings(self, source, updates):
        if source is self:
            return
        if "mode" in updates:
            mode = updates["mode"]
            if mode in MODE_LABELS:
                self.playback_mode = mode
                self.controls.set_mode(MODE_LABELS[mode])
        if "volume" in updates:
            v = updates["volume"]
            self._stored_volume = v
            if self.player:
                self.player.set_volume(v)
            self.controls.set_volume_display(v)
        if any(k in updates for k in ("subtitle_enabled", "subtitle_style", "subtitle_pos")):
            st = self.storage.load_settings()
            self._subtitle_enabled = updates.get("subtitle_enabled", st.get("subtitle_enabled", True))
            self._subtitle_style = updates.get("subtitle_style", st.get("subtitle_style", 1))
            self._subtitle_pos = updates.get("subtitle_pos", st.get("subtitle_pos", 100))
            self._apply_subtitle_settings()

    # -- subtitles ------------------------------------------------------------
    def _apply_subtitle_settings(self):
        self.video_surface.set_subtitle_enabled(self._subtitle_enabled)
        self.video_surface.set_sub_drag_start_pos(self._subtitle_pos)
        if self.player:
            self.player.set_sub_visibility(self._subtitle_enabled)
            self.player.apply_subtitle_style(self._subtitle_style)
            self.player.set_sub_pos(self._subtitle_pos)

    def _on_sub_pos_dragged(self, pos):
        self._subtitle_pos = pos
        self.video_surface.set_sub_drag_start_pos(pos)
        if self.player:
            self.player.set_sub_pos(pos)
        self._sub_pos_save_timer.start()

    def _save_sub_pos(self):
        self._update_settings({"subtitle_pos": self._subtitle_pos})
        self.controller.settings_changed.emit(self, {"subtitle_pos": self._subtitle_pos})

    # -- teardown ---------------------------------------------------------------
    def closeEvent(self, event):
        self._save_resume()
        self._update_settings({
            "geometry": bytes(self.saveGeometry()).hex(),
            "splitter_sizes": self.splitter.sizes(),
        })
        self._save_settings()
        if self.player:
            self.player.shutdown()
        self.controller.unregister_window(self)
        super().closeEvent(event)
