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
    def __init__(self, name: str, id: str | None = None, is_temp: bool = False):
        self.id = id or str(uuid.uuid4())
        self.name = name
        self.is_temp = is_temp
        self.entries: list[Entry] = []

    def to_dict(self) -> dict:
        d = {
            "id": self.id,
            "name": self.name,
            "entries": [{"path": e.path, "name": e.display_name} for e in self.entries] if not self.is_temp else [],
        }
        if self.is_temp:
            d["is_temp"] = True
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "Playlist":
        p = cls(d["name"], d.get("id"), d.get("is_temp", False))
        if not p.is_temp:
            p.entries = [Entry(e["path"], e.get("name")) for e in d.get("entries", [])]
        return p

    def remove_invalid(self) -> int:
        """Remove entries whose files don't exist, aren't media, or can't be decoded.
        Uses ffprobe (parallel) to check content validity for existing media files."""
        import subprocess
        from concurrent.futures import ThreadPoolExecutor, as_completed

        old = len(self.entries)

        # Pre-filter: existence + extension
        candidates = [e for e in self.entries if os.path.isfile(e.path)
                      and is_media_file(e.path)]

        if not candidates:
            self.entries = []
            return old

        def _ok(path):
            try:
                r = subprocess.run(
                    ["ffprobe", "-v", "quiet", "-show_entries", "format=format_name",
                     "-of", "default=noprint_wrappers=1:nokey=1", path],
                    capture_output=True, text=True, timeout=10,
                    creationflags=subprocess.CREATE_NO_WINDOW
                    if hasattr(subprocess, "CREATE_NO_WINDOW") else 0,
                )
                return r.returncode == 0 and bool(r.stdout.strip())
            except Exception:
                return False

        ok_paths: set[str] = set()
        with ThreadPoolExecutor(max_workers=8) as ex:
            futures = {ex.submit(_ok, e.path): e.path for e in candidates}
            for future in as_completed(futures):
                path = futures[future]
                try:
                    if future.result():
                        ok_paths.add(os.path.normcase(path))
                except Exception:
                    pass

        self.entries = [e for e in self.entries
                        if os.path.normcase(e.path) in ok_paths]
        return old - len(self.entries)

    def dedupe(self) -> int:
        """Keep first occurrence of each path. Returns count removed."""
        seen = set()
        deduped = []
        for e in self.entries:
            norm = os.path.normcase(e.path)
            if norm not in seen:
                seen.add(norm)
                deduped.append(e)
        removed = len(self.entries) - len(deduped)
        self.entries = deduped
        return removed

    def sort_by_name(self):
        self.entries.sort(key=lambda e: e.display_name.lower())

    def sort_by_mtime(self):
        self.entries.sort(key=lambda e: os.path.getmtime(e.path) if os.path.isfile(e.path) else 0)

    def sort_by_duration(self):
        """Sort by media duration using ffprobe. Missing/unprobeable files go last."""
        import subprocess
        from concurrent.futures import ThreadPoolExecutor, as_completed

        durations = {}

        def _probe(path):
            if not os.path.isfile(path):
                return path, -1
            try:
                r = subprocess.run(
                    ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
                     "-of", "default=noprint_wrappers=1:nokey=1", path],
                    capture_output=True, text=True, timeout=15,
                    creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0,
                )
                return path, float(r.stdout.strip()) if r.stdout.strip() else 0
            except Exception:
                return path, -1

        with ThreadPoolExecutor(max_workers=8) as ex:
            futures = [ex.submit(_probe, e.path) for e in self.entries]
            for future in as_completed(futures):
                p, d = future.result()
                durations[p] = d

        self.entries.sort(key=lambda e: (durations.get(e.path, -1) < 0, durations.get(e.path, 0)))

    def shuffle(self):
        import random
        random.shuffle(self.entries)


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