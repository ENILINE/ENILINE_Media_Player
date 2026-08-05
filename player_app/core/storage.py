"""JSON persistence for playlists, per-file resume positions and settings.

All writes are atomic (temp file + os.replace) to survive crashes.
Data lives under %APPDATA%/VideoPlayer.
"""
import json
import os
import tempfile

from PyQt5.QtCore import QStandardPaths


def _data_dir() -> str:
    base = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
    if not base:
        base = os.path.join(os.path.expanduser("~"), "AppData", "Roaming", "VideoPlayer")
    os.makedirs(base, exist_ok=True)
    return base


def _load_json(path: str, default):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default
    return default


def _atomic_write(path: str, data) -> None:
    d = os.path.dirname(path)
    fd, tmp = tempfile.mkstemp(dir=d, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass
        raise


class Storage:
    def __init__(self):
        d = _data_dir()
        self.playlists_path = os.path.join(d, "playlists.json")
        self.resume_path = os.path.join(d, "resume.json")
        self.settings_path = os.path.join(d, "settings.json")

    def load_playlists(self) -> list:
        return _load_json(self.playlists_path, [])

    def save_playlists(self, collection) -> None:
        _atomic_write(self.playlists_path, collection.to_dict())

    def load_resume(self) -> dict:
        return _load_json(self.resume_path, {})

    def save_resume(self, data: dict) -> None:
        _atomic_write(self.resume_path, data)

    def load_settings(self) -> dict:
        return _load_json(self.settings_path, {})

    def save_settings(self, data: dict) -> None:
        _atomic_write(self.settings_path, data)