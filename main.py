"""Entry point. Must put the libmpv DLL directory on PATH before importing mpv."""
import os
import sys


def _bootstrap_mpv():
    if os.name != "nt":
        return
    if getattr(sys, "frozen", False):
        candidates = [
            os.path.dirname(sys.executable),
            getattr(sys, "_MEIPASS", None),
        ]
    else:
        candidates = [os.path.join(os.path.dirname(os.path.abspath(__file__)), "bin")]
    for d in candidates:
        if not d or not os.path.isdir(d):
            continue
        dll_dir = os.path.abspath(d)
        if os.path.isfile(os.path.join(dll_dir, "libmpv-2.dll")):
            os.environ["PATH"] = dll_dir + os.pathsep + os.environ.get("PATH", "")
            try:
                os.add_dll_directory(dll_dir)
            except (AttributeError, OSError):
                pass
            return


_bootstrap_mpv()

from PyQt5.QtWidgets import QApplication  # noqa: E402

from player_app.ui.main_window import MainWindow  # noqa: E402


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("VideoPlayer")
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()