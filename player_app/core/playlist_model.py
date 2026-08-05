"""Playlist data model. Playlists hold references to file paths, never copies,
so the same video can live in many lists and renaming never touches disk."""
import os
import uuid

MEDIA_EXTENSIONS = {
    ".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".ts", ".m4v",
    ".mpg", ".mpeg", ".3gp", ".mp3", ".flac", ".wav", ".ogg", ".oga", ".aac",
    ".m4a", ".wma", ".opus", ".mka",
}


def is_media_file(path: str) -> bool:
    return os.path.splitext(path)[1].lower() in MEDIA_EXTENSIONS


class Entry:
    def __init__(self, path: str, display_name: str | None = None):
        self.path = path
        self.display_name = display_name or os.path.basename(path)


class Playlist:
    def __init__(self, name: str, id: str | None = None):
        self.id = id or str(uuid.uuid4())
        self.name = name
        self.entries: list[Entry] = []

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "entries": [{"path": e.path, "name": e.display_name} for e in self.entries],
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Playlist":
        p = cls(d["name"], d.get("id"))
        p.entries = [Entry(e["path"], e.get("name")) for e in d.get("entries", [])]
        return p


class PlaylistCollection:
    def __init__(self):
        self.playlists: list[Playlist] = []

    def find(self, pid: str) -> Playlist | None:
        return next((p for p in self.playlists if p.id == pid), None)

    def index_of(self, pid: str) -> int:
        for i, p in enumerate(self.playlists):
            if p.id == pid:
                return i
        return -1

    def to_dict(self) -> list[dict]:
        return [p.to_dict() for p in self.playlists]

    @classmethod
    def from_dict(cls, lst: list[dict]) -> "PlaylistCollection":
        c = cls()
        c.playlists = [Playlist.from_dict(d) for d in lst or []]
        return c