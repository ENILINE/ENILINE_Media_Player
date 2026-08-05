import os

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from ..core.playlist_model import is_media_file

MEDIA_FILTER = "媒体文件 (*" + " *".join(
    "*.mp4 *.mkv *.avi *.mov *.wmv *.flv *.webm *.ts *.m4v *.mpg *.mpeg *.3gp "
    "*.mp3 *.flac *.wav *.ogg *.oga *.aac *.m4a *.wma *.opus *.mka".split()
) + ")"


def collect_media_files(directory: str) -> list[str]:
    out = []
    for root, _dirs, files in os.walk(directory):
        for f in files:
            p = os.path.join(root, f)
            if is_media_file(p):
                out.append(p)
    return out


class PlaylistPanel(QWidget):
    playlist_selected = pyqtSignal(str)
    play_requested = pyqtSignal(str, int)
    add_paths_requested = pyqtSignal(str, list)
    cut_requested = pyqtSignal(str, list)
    copy_requested = pyqtSignal(str, list)
    paste_requested = pyqtSignal(str)
    remove_requested = pyqtSignal(str, list)
    rename_entry_requested = pyqtSignal(str, int)
    create_requested = pyqtSignal()
    delete_requested = pyqtSignal(str)
    rename_requested = pyqtSignal(str)
    copy_list_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._updating = False
        self.current_pid = None
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        split = QSplitter(Qt.Horizontal)

        # -- left: playlist list + actions ---------------------------------
        left = QWidget()
        lv = QVBoxLayout(left)
        lv.setContentsMargins(0, 0, 0, 0)
        self.list_list = QListWidget()
        self.list_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.list_list.itemSelectionChanged.connect(self._on_list_selection)
        self.list_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_list.customContextMenuRequested.connect(self._list_menu)
        lv.addWidget(self.list_list, 1)

        btns = QHBoxLayout()
        self.new_btn = QPushButton("新建")
        self.del_btn = QPushButton("删除")
        self.ren_btn = QPushButton("重命名")
        self.cpy_btn = QPushButton("复制")
        for b in (self.new_btn, self.del_btn, self.ren_btn, self.cpy_btn):
            b.setFocusPolicy(Qt.NoFocus)
            btns.addWidget(b)
        self.new_btn.clicked.connect(self.create_requested.emit)
        self.del_btn.clicked.connect(lambda: self._current_pid() and self.delete_requested.emit(self._current_pid()))
        self.ren_btn.clicked.connect(lambda: self._current_pid() and self.rename_requested.emit(self._current_pid()))
        self.cpy_btn.clicked.connect(lambda: self._current_pid() and self.copy_list_requested.emit(self._current_pid()))
        lv.addLayout(btns)

        # -- right: entries --------------------------------------------------
        right = QWidget()
        rv = QVBoxLayout(right)
        rv.setContentsMargins(0, 0, 0, 0)
        self.entry_list = QListWidget()
        self.entry_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.entry_list.itemDoubleClicked.connect(self._on_entry_activated)
        self.entry_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.entry_list.customContextMenuRequested.connect(self._entry_menu)
        self.entry_list.setAcceptDrops(True)
        self.entry_list.setDragEnabled(False)
        self.entry_list.setDefaultDropAction(Qt.CopyAction)
        rv.addWidget(self.entry_list, 1)

        split.addWidget(left)
        split.addWidget(right)
        split.setSizes([220, 380])
        outer.addWidget(split)

    # -- helpers ------------------------------------------------------------
    def _current_pid(self):
        row = self.list_list.currentRow()
        if row < 0:
            return None
        return self._pid_by_row(row)

    def _pid_by_row(self, row):
        item = self.list_list.item(row)
        return item.data(Qt.UserRole) if item else None

    def _selected_rows(self):
        return sorted(i.row() for i in self.entry_list.selectedIndexes())

    def _entry_at(self, row):
        item = self.entry_list.item(row)
        return item.data(Qt.UserRole) if item else None

    # -- model -> view ------------------------------------------------------
    def refresh(self, collection, current_pid, current_index):
        self._updating = True
        try:
            self.list_list.blockSignals(True)
            self.list_list.clear()
            for pl in collection.playlists:
                item = QListWidgetItem(pl.name)
                item.setData(Qt.UserRole, pl.id)
                self.list_list.addItem(item)
            row = collection.index_of(current_pid) if current_pid else -1
            self.list_list.setCurrentRow(max(row, 0))
            self.list_list.blockSignals(False)

            self.entry_list.clear()
            pl = collection.find(current_pid) if current_pid else None
            if pl:
                for idx, e in enumerate(pl.entries):
                    item = QListWidgetItem(e.display_name)
                    item.setData(Qt.UserRole, idx)
                    item.setToolTip(e.path)
                    self.entry_list.addItem(item)
                if current_index is not None and 0 <= current_index < len(pl.entries):
                    self.entry_list.setCurrentRow(current_index)
        finally:
            self._updating = False

    # -- user interactions ----------------------------------------------------
    def _on_list_selection(self):
        if self._updating:
            return
        pid = self._current_pid()
        if pid:
            self.playlist_selected.emit(pid)

    def _on_entry_activated(self, item):
        pid = self._current_pid()
        if pid and item:
            self.play_requested.emit(pid, item.data(Qt.UserRole))

    def _list_menu(self, pos):
        menu = QMenu(self)
        menu.addAction("新建列表", self.create_requested.emit)
        pid = self._current_pid()
        if pid:
            menu.addSeparator()
            menu.addAction("重命名", lambda: self.rename_requested.emit(pid))
            menu.addAction("复制", lambda: self.copy_list_requested.emit(pid))
            menu.addAction("删除", lambda: self.delete_requested.emit(pid))
        menu.exec_(self.list_list.mapToGlobal(pos))

    def _entry_menu(self, pos):
        pid = self._current_pid()
        if not pid:
            return
        rows = self._selected_rows()
        menu = QMenu(self)
        menu.addAction("添加文件", self._add_files)
        menu.addAction("添加目录", self._add_directory)
        menu.addSeparator()
        if rows:
            menu.addAction("剪切", lambda: self.cut_requested.emit(pid, rows))
            menu.addAction("复制", lambda: self.copy_requested.emit(pid, rows))
        menu.addAction("粘贴", lambda: self.paste_requested.emit(pid))
        if rows:
            menu.addSeparator()
            menu.addAction("重命名", lambda: self.rename_entry_requested.emit(pid, rows[0]))
            menu.addAction("删除", lambda: self.remove_requested.emit(pid, rows))
        menu.exec_(self.entry_list.mapToGlobal(pos))

    def _add_files(self):
        pid = self._current_pid()
        if not pid:
            return
        files, _ = QFileDialog.getOpenFileNames(self, "添加文件", "", MEDIA_FILTER)
        if files:
            self.add_paths_requested.emit(pid, files)

    def _add_directory(self):
        pid = self._current_pid()
        if not pid:
            return
        directory = QFileDialog.getExistingDirectory(self, "添加目录")
        if directory:
            files = collect_media_files(directory)
            if not files:
                QMessageBox.information(self, "播放列表", "该目录下没有找到媒体文件。")
                return
            self.add_paths_requested.emit(pid, files)

    # -- drag & drop from Explorer --------------------------------------------
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        pid = self._current_pid()
        if not pid:
            return
        paths = []
        for url in event.mimeData().urls():
            p = url.toLocalFile()
            if p and is_media_file(p):
                paths.append(p)
        if paths:
            self.add_paths_requested.emit(pid, paths)