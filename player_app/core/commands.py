"""Command-pattern undo/redo for playlist operations.

Operations are pure functions that mutate the PlaylistCollection. The caller
(MainWindow) wraps each executed/undone/redone command with persistence and a
UI refresh.
"""
from .playlist_model import Entry, Playlist, PlaylistCollection


class Command:
    __slots__ = ("label", "undo_fn", "redo_fn")

    def __init__(self, label, undo_fn, redo_fn):
        self.label = label
        self.undo_fn = undo_fn
        self.redo_fn = redo_fn


class UndoRedoStack:
    def __init__(self):
        self._undo: list[Command] = []
        self._redo: list[Command] = []

    def execute(self, cmd: Command) -> None:
        cmd.redo_fn()
        self._undo.append(cmd)
        self._redo.clear()

    def undo(self) -> bool:
        if not self._undo:
            return False
        cmd = self._undo.pop()
        cmd.undo_fn()
        self._redo.append(cmd)
        return True

    def redo(self) -> bool:
        if not self._redo:
            return False
        cmd = self._redo.pop()
        cmd.redo_fn()
        self._undo.append(cmd)
        return True


def _remove_by_identity(entries: list, targets: list) -> None:
    ids = {id(e) for e in targets}
    entries[:] = [e for e in entries if id(e) not in ids]


def create_playlist_cmd(collection: PlaylistCollection, name: str):
    pl = Playlist(name)

    def redo():
        collection.playlists.append(pl)

    def undo():
        collection.playlists.remove(pl)

    return Command("新建列表", undo, redo), pl.id


def delete_playlist_cmd(collection: PlaylistCollection, pid: str):
    pl = collection.find(pid)
    if pl is None:
        return None
    idx = collection.playlists.index(pl)

    def redo():
        collection.playlists.pop(idx)

    def undo():
        collection.playlists.insert(idx, pl)

    return Command("删除列表", undo, redo)


def rename_playlist_cmd(collection: PlaylistCollection, pid: str, new_name: str):
    pl = collection.find(pid)
    if pl is None:
        return None
    old = pl.name

    def redo():
        pl.name = new_name

    def undo():
        pl.name = old

    return Command("重命名列表", undo, redo)


def copy_playlist_cmd(collection: PlaylistCollection, pid: str):
    src = collection.find(pid)
    if src is None:
        return None, None
    copy = Playlist(src.name + " 副本")
    copy.entries = [Entry(e.path, e.display_name) for e in src.entries]
    idx = collection.playlists.index(src)

    def redo():
        collection.playlists.insert(idx + 1, copy)

    def undo():
        collection.playlists.remove(copy)

    return Command("复制列表", undo, redo), copy.id


def add_entries_cmd(collection: PlaylistCollection, pid: str, entries: list[Entry]):
    pl = collection.find(pid)
    if pl is None or not entries:
        return None

    def redo():
        pl.entries.extend(entries)

    def undo():
        _remove_by_identity(pl.entries, entries)

    return Command("添加条目", undo, redo)


def remove_entries_cmd(collection: PlaylistCollection, pid: str, indices: list[int]):
    pl = collection.find(pid)
    if pl is None:
        return None
    idxs = sorted(set(i for i in indices if 0 <= i < len(pl.entries)))
    if not idxs:
        return None
    removed = [(i, pl.entries[i]) for i in idxs]

    def redo():
        for i in sorted(idxs, reverse=True):
            del pl.entries[i]

    def undo():
        for i, e in removed:
            pl.entries.insert(min(i, len(pl.entries)), e)

    return Command("删除条目", undo, redo)


def rename_entry_cmd(collection: PlaylistCollection, pid: str, index: int, new_name: str):
    pl = collection.find(pid)
    if pl is None or not (0 <= index < len(pl.entries)):
        return None
    entry = pl.entries[index]
    old = entry.display_name

    def redo():
        entry.display_name = new_name

    def undo():
        entry.display_name = old

    return Command("重命名条目", undo, redo)


def paste_cmd(collection: PlaylistCollection, pid: str, entries: list[Entry]):
    pl = collection.find(pid)
    if pl is None or not entries:
        return None
    created: list[Entry] = []

    def redo():
        created[:] = [Entry(e.path, e.display_name) for e in entries]
        pl.entries.extend(created)

    def undo():
        _remove_by_identity(pl.entries, created)
        created[:] = []

    return Command("粘贴", undo, redo)