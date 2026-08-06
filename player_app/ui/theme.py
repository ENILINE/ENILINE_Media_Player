"""Dark modern stylesheet (VS Code-like) applied app-wide."""

QSS = """
* {
    font-family: "Consolas";
    font-size: 16px;
}
QMainWindow, QWidget {
    background: #1e1e1e;
    color: #e0e0e0;
}
QToolTip {
    background: #252526;
    color: #e0e0e0;
    border: 1px solid #3f3f46;
}
QPushButton, QToolButton {
    background: #2d2d30;
    border: 1px solid #3f3f46;
    border-radius: 4px;
    padding: 5px 12px;
    color: #e0e0e0;
}
QPushButton:hover, QToolButton:hover {
    background: #3f3f46;
}
QPushButton:pressed, QToolButton:pressed {
    background: #0e639c;
}
QPushButton:disabled, QToolButton:disabled {
    color: #6a6a6a;
    background: #2d2d30;
}
QToolButton {
    padding: 5px;
}
QDoubleSpinBox, QLineEdit {
    background: #333333;
    border: 1px solid #3f3f46;
    border-radius: 3px;
    padding: 2px 4px;
    selection-background-color: #094771;
}
QDoubleSpinBox:focus, QLineEdit:focus {
    border: 1px solid #0e639c;
}

/* Sliders */
QSlider::groove:horizontal {
    height: 4px;
    background: #3f3f46;
    border-radius: 2px;
}
QSlider::sub-page:horizontal {
    background: #0e639c;
    border-radius: 2px;
}
QSlider::handle:horizontal {
    width: 16px;
    height: 16px;
    margin: -6px 0;
    border-radius: 8px;
    background: #e0e0e0;
}
QSlider::handle:horizontal:hover {
    background: #ffffff;
}

/* Tree */
QTreeWidget {
    background: #252526;
    border: none;
    outline: none;
    color: #e0e0e0;
}
QTreeWidget::item {
    height: 32px;
    padding-left: 4px;
    border-radius: 3px;
}
QTreeWidget::item:hover {
    background: #2d2d30;
}
QTreeWidget::item:selected {
    background: #094771;
}

QMenu {
    background: #252526;
    border: 1px solid #3f3f46;
    padding: 4px;
}
QMenu::item {
    padding: 5px 24px;
    border-radius: 3px;
}
QMenu::item:selected {
    background: #094771;
}
QMenu::separator {
    height: 1px;
    background: #3f3f46;
    margin: 4px 8px;
}

QLabel {
    background: transparent;
    color: #e0e0e0;
}
"""