import os

from PyQt5.QtCore import QPoint, QRect, QSize, Qt, pyqtSignal
from PyQt5.QtGui import QColor, QPainter, QPalette, QPen, QPolygonF
from PyQt5.QtWidgets import (
    QAbstractItemDelegate,
    QAbstractItemView,
    QCommonStyle,
    QFileDialog,
    QLineEdit,
    QMenu,
    QMessageBox,
    QStyle,
    QStyledItemDelegate,
    QStyleOption,
    QTreeWidget,
    QTreeWidgetItem,
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


class _RenameDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        editor.setMinimumWidth(160)
        return editor


class _BranchStyle(QCommonStyle):
    def drawPrimitive(self, element, option, painter, widget=None):
        if element == QStyle.PE_IndicatorBranch:
            if not (option.state & QStyle.State_Children):
                return  # leaf node, draw nothing
            mid = option.rect.center()
            painter.save()
            pen = QPen(QColor("#a0a0a0"))
            pen.setWidthF(1.5)
            painter.setPen(pen)
            painter.setRenderHint(QPainter.Antialiasing, True)
            sz = 4
            if option.state & QStyle.State_Open:
                tri = QPolygonF([
                    QPoint(mid.x() - sz, mid.y() - sz // 2),
                    QPoint(mid.x() + sz, mid.y() - sz // 2),
                    QPoint(mid.x(), mid.y() + sz),
                ])
            else:
                tri = QPolygonF([
                    QPoint(mid.x() - sz // 2, mid.y() - sz),
                    QPoint(mid.x() + sz, mid.y()),
                    QPoint(mid.x() - sz // 2, mid.y() + sz),
                ])
            painter.drawLine(tri[0].toPoint(), tri[1].toPoint())
            painter.drawLine(tri[1].toPoint(), tri[2].toPoint())
            painter.drawLine(tri[2].toPoint(), tri[0].toPoint())
            painter.restore()
            return
        super().drawPrimitive(element, option, painter, widget)


class _Tree(QTreeWidget):
    def __init__(self, panel):
        super().__init__()
        self._panel = panel
        self.setStyle(_BranchStyle())

    def keyPressEvent(self, event):
        if not self._panel._tree_key(event):
            super().keyPressEvent(event)

    # -- drag & drop ----------------------------------------------------------
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        item = self.itemAt(event.pos())
        pid = self._panel._pid_of_item(item) or self._panel.current_pid
        if not pid:
            return
        paths = []
        for url in event.mimeData().urls():
            p = url.toLocalFile()
            if not p:
                continue
            if os.path.isdir(p):
                paths.extend(collect_media_files(p))
            elif is_media_file(p):
                paths.append(p)
        if paths:
            self._panel.add_paths_requested.emit(pid, paths)


class PlaylistPanel(QWidget):
    playlist_selected = pyqtSignal(str)
    play_requested = pyqtSignal(str, int)
    add_paths_requested = pyqtSignal(str, list)
    cut_requested = pyqtSignal(str, list)
    copy_requested = pyqtSignal(str, list)
    paste_requested = pyqtSignal(str)
    remove_requested = pyqtSignal(str, list)
    create_requested = pyqtSignal(str)
    delete_requested = pyqtSignal(str)
    rename_list_requested = pyqtSignal(str, str)
    copy_list_requested = pyqtSignal(str)
    rename_entry_requested = pyqtSignal(str, int, str)
    browse_file_requested = pyqtSignal(str)
    file_properties_requested = pyqtSignal(str)
    clean_invalid_requested = pyqtSignal(str)
    dedupe_requested = pyqtSignal(str)
    sort_by_name_requested = pyqtSignal(str)
    sort_by_mtime_requested = pyqtSignal(str)
    sort_by_duration_requested = pyqtSignal(str)
    shuffle_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._updating = False
        self._pending = None  # inline-edit context dict
        self._expanded_pids = set()
        self.current_pid = None
        self._build()

    def _build(self):
        self.setAttribute(Qt.WA_OpaquePaintEvent, True)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        self.tree = _Tree(self)
        self.tree.setHeaderHidden(True)
        self.tree.setRootIsDecorated(True)
        self.tree.setAnimated(True)
        self.tree.setUniformRowHeights(True)
        pal = self.tree.palette()
        pal.setColor(QPalette.Text, QColor("#e0e0e0"))
        pal.setColor(QPalette.ButtonText, QColor("#e0e0e0"))
        self.tree.setPalette(pal)
        self.tree.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._context_menu)
        self.tree.itemSelectionChanged.connect(self._on_selection_changed)
        self.tree.itemClicked.connect(self._on_item_clicked)
        self.tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.tree.itemChanged.connect(self._on_item_changed)
        self.tree.itemExpanded.connect(self._on_item_expanded)
        self.tree.itemCollapsed.connect(self._on_item_collapsed)
        self.tree.setItemDelegate(_RenameDelegate(self.tree))
        self.tree.itemDelegate().closeEditor.connect(self._on_editor_closed)
        self.tree.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tree.setAcceptDrops(True)
        self.tree.setDragEnabled(False)
        self.tree.setDefaultDropAction(Qt.CopyAction)
        self.tree.setMinimumWidth(80)
        outer.addWidget(self.tree)
        self.setMinimumWidth(0)

    # -- model -> view -------------------------------------------------------
    def _on_item_expanded(self, item):
        pid = item.data(0, Qt.UserRole)
        if pid:
            self._expanded_pids.add(pid)

    def _on_item_collapsed(self, item):
        pid = item.data(0, Qt.UserRole)
        if pid:
            self._expanded_pids.discard(pid)

    TEMP_ROLE = Qt.UserRole + 1

    def refresh(self, collection, current_pid, current_index, playing_pid=None):
        self._collection = collection
        self._updating = True
        self.tree.blockSignals(True)
        try:
            self.tree.clear()
            selected_pl = None
            selected_entry = None
            for pl in collection.playlists:
                pl_item = QTreeWidgetItem([pl.name])
                pl_item.setData(0, Qt.UserRole, pl.id)
                pl_item.setData(0, self.TEMP_ROLE, pl.is_temp)
                pl_item.setFlags(pl_item.flags() | Qt.ItemIsEditable)
                pl_item.setToolTip(0, pl.name)
                self.tree.addTopLevelItem(pl_item)
                for idx, e in enumerate(pl.entries):
                    label = e.display_name
                    if playing_pid and pl.id == playing_pid and idx == current_index:
                        label = "▶ " + label
                    else:
                        label = "  " + label
                    en_item = QTreeWidgetItem([label])
                    en_item.setData(0, Qt.UserRole, idx)
                    en_item.setFlags(en_item.flags() | Qt.ItemIsEditable)
                    en_item.setToolTip(0, e.path)
                    pl_item.addChild(en_item)
                if pl.id in self._expanded_pids:
                    pl_item.setExpanded(True)
                if pl.id == current_pid:
                    selected_pl = pl_item
                    if current_index is not None and 0 <= current_index < len(pl.entries):
                        selected_entry = pl_item.child(current_index)
            if selected_pl:
                selected_pl.setExpanded(True)
                self.tree.setCurrentItem(selected_entry if selected_entry else selected_pl)
        finally:
            self.tree.blockSignals(False)
            self._updating = False
        self.current_pid = current_pid

    # -- selection / data helpers ----------------------------------------------
    def _current_item(self):
        return self.tree.currentItem()

    def _pid_of_item(self, item):
        if item is None:
            return None
        if item.parent() is None:
            return item.data(0, Qt.UserRole)
        return item.parent().data(0, Qt.UserRole)

    def _selected_playlist_pid(self):
        cur = self._current_item()
        if cur is None:
            return None
        if cur.parent() is None:
            return cur.data(0, Qt.UserRole)
        return cur.parent().data(0, Qt.UserRole)

    def _selected_entry_data(self):
        """Return (pid, [indices]) for entry items selected under the current playlist."""
        cur = self._current_item()
        if cur is None or cur.parent() is None:
            return None
        pl_item = cur.parent()
        pid = pl_item.data(0, Qt.UserRole)
        indices = []
        for item in self.tree.selectedItems():
            if item.parent() is pl_item:
                idx = item.data(0, Qt.UserRole)
                if idx is not None:
                    indices.append(idx)
        return pid, sorted(set(indices))

    # -- user interaction ------------------------------------------------------
    def _on_selection_changed(self):
        if self._updating:
            return
        pid = self._selected_playlist_pid()
        if pid:
            self.playlist_selected.emit(pid)

    def _on_item_clicked(self, item, _col):
        if item.parent() is None:
            item.setExpanded(not item.isExpanded())

    def _on_item_double_clicked(self, item, _col):
        if item.parent() is None:
            return
        pid = item.parent().data(0, Qt.UserRole)
        idx = item.data(0, Qt.UserRole)
        if pid is not None and idx is not None:
            self.play_requested.emit(pid, idx)

    def _tree_key(self, event):
        key = event.key()
        if key == Qt.Key_Delete:
            self._delete_selection()
            return True
        if key == Qt.Key_F2:
            self._rename_current()
            return True
        if key in (Qt.Key_Return, Qt.Key_Enter):
            cur = self._current_item()
            if cur is not None and cur.parent() is not None:
                pid = cur.parent().data(0, Qt.UserRole)
                idx = cur.data(0, Qt.UserRole)
                if pid is not None and idx is not None:
                    self.play_requested.emit(pid, idx)
                    return True
        mods = event.modifiers()
        if mods & Qt.ControlModifier:
            if key == Qt.Key_X:
                self._cut()
                return True
            if key == Qt.Key_C:
                self._copy()
                return True
            if key == Qt.Key_V:
                self._paste()
                return True
        return False

    def _delete_selection(self):
        data = self._selected_entry_data()
        if data:
            pid, indices = data
            self.remove_requested.emit(pid, indices)
            return
        pid = self._selected_playlist_pid()
        if pid:
            self.delete_requested.emit(pid)

    def _rename_current(self):
        cur = self._current_item()
        if cur is None:
            return
        if cur.parent() is None:
            self._pending = {
                "item": cur, "kind": "rename_playlist", "pid": cur.data(0, Qt.UserRole),
                "old": cur.text(0),
            }
        else:
            self._pending = {
                "item": cur, "kind": "rename_entry", "pid": cur.parent().data(0, Qt.UserRole),
                "index": cur.data(0, Qt.UserRole), "old": cur.text(0),
            }
        self.tree.editItem(cur)

    def _cut(self):
        data = self._selected_entry_data()
        if data:
            self.cut_requested.emit(*data)

    def _copy(self):
        data = self._selected_entry_data()
        if data:
            self.copy_requested.emit(*data)

    def _paste(self):
        pid = self._selected_playlist_pid()
        if pid:
            self.paste_requested.emit(pid)

    # -- context menu ----------------------------------------------------------
    def _context_menu(self, pos):
        item = self.tree.itemAt(pos)
        menu = QMenu(self)
        menu.addAction("新建列表", self._create_inline)
        menu.addSeparator()
        if item is not None:
            pid = self._pid_of_item(item)
            is_temp = bool(item.data(0, self.TEMP_ROLE)) if item.parent() is None else bool(item.parent().data(0, self.TEMP_ROLE))
            if item.parent() is None:
                menu.addAction("添加文件", lambda: self._add_files_to(pid))
                menu.addAction("添加目录", lambda: self._add_directory_to(pid))
                menu.addSeparator()
                menu.addAction("重命名", self._rename_current)
                menu.addAction("复制", lambda: self.copy_list_requested.emit(pid))
                if not is_temp:
                    menu.addAction("删除", lambda: self.delete_requested.emit(pid))
                menu.addSeparator()
                ops = menu.addMenu("列表操作")
                ops.addAction("清空无效文件", lambda: self.clean_invalid_requested.emit(pid))
                ops.addAction("去重", lambda: self.dedupe_requested.emit(pid))
                ops.addAction("按名字排序", lambda: self.sort_by_name_requested.emit(pid))
                ops.addAction("按文件时间排序", lambda: self.sort_by_mtime_requested.emit(pid))
                ops.addAction("按长度排序", lambda: self.sort_by_duration_requested.emit(pid))
                ops.addAction("随机排序", lambda: self.shuffle_requested.emit(pid))
            else:
                menu.addAction("添加文件", self._add_files)
                menu.addAction("添加目录", self._add_directory)
                menu.addSeparator()
                menu.addAction("剪切", self._cut)
                menu.addAction("复制", self._copy)
                menu.addAction("粘贴", self._paste)
                menu.addSeparator()
                menu.addAction("重命名", self._rename_current)
                menu.addAction("删除", self._delete_selection)
                menu.addSeparator()
                path = self._entry_path(item)
                menu.addAction("浏览文件", lambda: self.browse_file_requested.emit(path))
                menu.addAction("文件属性", lambda: self.file_properties_requested.emit(path))
        else:
            pid = self.current_pid
            menu.addAction("添加文件", lambda: self._add_files_to(pid))
            menu.addAction("添加目录", lambda: self._add_directory_to(pid))
        menu.exec_(self.tree.viewport().mapToGlobal(pos))

    def _entry_path(self, item):
        if item is None or item.parent() is None:
            return ""
        pid = item.parent().data(0, Qt.UserRole)
        idx = item.data(0, Qt.UserRole)
        if pid is None or idx is None:
            return ""
        col = getattr(self, "_collection", None)
        if col:
            pl = col.find(pid)
            if pl and 0 <= idx < len(pl.entries):
                return pl.entries[idx].path
        return ""

    def _create_inline(self):
        item = QTreeWidgetItem(["新建列表"])
        item.setFlags(item.flags() | Qt.ItemIsEditable)
        self.tree.addTopLevelItem(item)
        self.tree.setCurrentItem(item)
        self._pending = {"item": item, "kind": "create", "old": item.text(0)}
        self.tree.editItem(item)

    # -- inline edit commit ----------------------------------------------------
    def _on_item_changed(self, item, col):
        if self._updating:
            return
        p = self._pending
        if not p or p["item"] is not item:
            return
        text = item.text(0).strip()
        kind = p["kind"]
        if kind == "create":
            if text:
                self.create_requested.emit(text)
            else:
                idx = self.tree.indexOfTopLevelItem(item)
                if idx >= 0:
                    self.tree.takeTopLevelItem(idx)
            self._pending = None
        elif kind == "rename_playlist":
            if text and text != p["old"]:
                self.rename_list_requested.emit(p["pid"], text)
            self._pending = None
        elif kind == "rename_entry":
            if text and text != p["old"]:
                self.rename_entry_requested.emit(p["pid"], p["index"], text)
            self._pending = None

    def _on_editor_closed(self, editor, hint):
        p = self._pending
        if not p:
            return
        if hint == QAbstractItemDelegate.RevertModelCache:
            if p["kind"] == "create":
                idx = self.tree.indexOfTopLevelItem(p["item"])
                if idx >= 0:
                    self.tree.takeTopLevelItem(idx)
            self._pending = None
        elif hint == QAbstractItemDelegate.NoHint:
            # committed; itemChanged normally handled it, but clear if unchanged.
            self._pending = None

    # -- add files / directory --------------------------------------------------
    def _add_files_to(self, pid):
        if not pid:
            return
        files, _ = QFileDialog.getOpenFileNames(self, "添加文件", "", MEDIA_FILTER)
        if files:
            self.add_paths_requested.emit(pid, files)

    def _add_directory_to(self, pid):
        if not pid:
            return
        directory = QFileDialog.getExistingDirectory(self, "添加目录")
        if directory:
            files = collect_media_files(directory)
            if not files:
                QMessageBox.information(self, "播放列表", "该目录下没有找到媒体文件。")
                return
            self.add_paths_requested.emit(pid, files)

    def _add_files(self):
        pid = self._selected_playlist_pid()
        if not pid:
            return
        files, _ = QFileDialog.getOpenFileNames(self, "添加文件", "", MEDIA_FILTER)
        if files:
            self.add_paths_requested.emit(pid, files)

    def _add_directory(self):
        pid = self._selected_playlist_pid()
        if not pid:
            return
        directory = QFileDialog.getExistingDirectory(self, "添加目录")
        if directory:
            files = collect_media_files(directory)
            if not files:
                QMessageBox.information(self, "播放列表", "该目录下没有找到媒体文件。")
                return
            self.add_paths_requested.emit(pid, files)

