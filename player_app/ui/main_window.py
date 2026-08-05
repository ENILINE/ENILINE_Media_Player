import random

from PyQt5.QtCore import QEvent, Qt, QTimer
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
from ..core.storage import Storage
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
    def __init__(self, startup_paths=None):
        super().__init__()
        self.setWindowTitle("本地视频播放器")
        self.resize(1100, 700)

        self.storage = Storage()
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
        self._right_timer = None
        self._right_ctrl = False
        self._refresh_queued = False

        self._startup_paths = startup_paths or []

        self._build_ui()
        self._load_settings()
        self._wire_controls()
        self._refresh_panel()

        app = QApplication.instance()
        app.installEventFilter(self)

        self._resume_timer = QTimer(self)
        self._resume_timer.setInterval(5000)
        self._resume_timer.timeout.connect(self._save_resume)
        self._resume_timer.start()

    def _ensure_builtin_lists(self):
        # Remove stale temp lists from saved data; always recreate fresh.
        self.collection.playlists = [p for p in self.collection.playlists if not p.is_temp]
        temp = Playlist("临时列表", is_temp=True)
        self.collection.playlists.insert(0, temp)
        if not any(p.name == "默认列表" and not p.is_temp for p in self.collection.playlists):
            default = Playlist("默认列表")
            self.collection.playlists.insert(1, default)

    # -- UI construction ----------------------------------------------------
    def _build_ui(self):
        self.video_surface = VideoSurface()
        self.video_surface.files_dropped.connect(self._on_video_drop)
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

        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setHandleWidth(3)
        self.splitter.addWidget(self.panel)
        self.splitter.addWidget(self.video_surface)
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setSizes([260, 740])
        self.splitter.splitterMoved.connect(self._on_splitter_moved)

        central = QWidget()
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

    def showEvent(self, event):
        super().showEvent(event)
        if self.player is None:
            self.player = MpvPlayer(self.video_surface.winId())
            self.player.set_volume(self._stored_volume)
            self._connect_player()
            self._process_startup_paths()

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
        self.controls.seek_requested.connect(self._on_controls_seek)

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

    def _save_settings(self):
        self.storage.save_settings({
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
        self._current_path = path
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
        if not self.player:
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

    def _toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
            self.panel.show()
            self.controls.set_fullscreen(False)
        else:
            self.panel.hide()
            self.showFullScreen()
            self.controls.set_fullscreen(True)

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
        self.player.load(pl.entries[index].path)
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
        self.panel.refresh(self.collection, self.current_pid, hi)

    # -- playlist operations (undoable) ----------------------------------------
    def _run(self, cmd):
        if cmd is None:
            return
        self.stack.execute(cmd)
        self._after_change()

    def _after_change(self):
        self._validate_state()
        self.storage.save_playlists(self.collection)
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

    def add_paths(self, pid, paths):
        entries = [Entry(p) for p in paths if p and is_media_file(p)]
        if not entries:
            return
        self._run(add_entries_cmd(self.collection, pid, entries))

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

    def eventFilter(self, obj, event):
        if QApplication.activePopupWidget() is not None:
            return False
        if event.type() == QEvent.WindowDeactivate and (self._turbo_active or self._right_timer):
            if self._turbo_active:
                self.player.set_speed(self._base_speed)
                self.controls.set_speed_display(self._base_speed)
                self._turbo_active = False
            if self._right_timer:
                self._right_timer.stop()
            self._right_timer = None
        if event.type() == QEvent.KeyPress:
            return self._on_key_press(event)
        if event.type() == QEvent.KeyRelease:
            return self._on_key_release(event)
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
        if self._tree_has_focus():
            return False  # arrows / delete / ctrl+x/c/v / enter -> tree handles them
        if key == Qt.Key_Left:
            self._seek(-30 if ctrl else -5)
            return True
        if key == Qt.Key_Right:
            if event.isAutoRepeat():
                return True
            self._right_ctrl = ctrl
            self._right_timer = QTimer(self)
            self._right_timer.setSingleShot(True)
            self._right_timer.timeout.connect(self._enter_turbo)
            self._right_timer.start(TURBO_HOLD_MS)
            return True
        if key == Qt.Key_Up:
            if self.player:
                if self.player.is_muted():
                    self.player.set_mute(False)
                    self.controls.set_muted_display(False)
                self.player.set_volume(self.player.get_volume() + 5)
                self.controls.set_volume_display(self.player.get_volume())
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
        if self._is_text_input_focused():
            return False
        if self._tree_has_focus():
            return False
        if event.key() == Qt.Key_Right and not event.isAutoRepeat():
            if self._turbo_active:
                self.player.set_speed(self._base_speed)
                self.controls.set_speed_display(self._base_speed)
                self._turbo_active = False
            elif self._right_timer is not None:
                self._right_timer.stop()
                self._seek(30 if self._right_ctrl else 5)
            self._right_timer = None
            self._right_ctrl = False
            return True
        return False

    def _enter_turbo(self):
        self._turbo_active = True
        self._base_speed = self.player.get_speed()
        self.player.set_speed(speed_for_turbo(self._base_speed))

    # -- teardown ---------------------------------------------------------------
    def closeEvent(self, event):
        if self.player:
            self._save_resume()
            self._save_settings()
            self.player.shutdown()
        super().closeEvent(event)