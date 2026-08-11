"""Single-instance IPC via QLocalServer/QLocalSocket on Windows named pipes."""
import json

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtNetwork import QLocalServer, QLocalSocket

SERVER_NAME = "ENILINE_Media_Player_IPC"


def try_send_to_existing(paths: list[str]) -> bool:
    """Try to send paths to an already-running instance. Returns True if sent."""
    sock = QLocalSocket()
    sock.connectToServer(SERVER_NAME)
    if not sock.waitForConnected(2000):
        sock.close()
        return False
    data = json.dumps(paths, ensure_ascii=False).encode("utf-8")
    sock.write(data)
    sock.waitForBytesWritten(2000)
    sock.disconnectFromServer()
    sock.close()
    return True


class IPCServer(QObject):
    paths_received = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._server = QLocalServer(self)
        self._server.newConnection.connect(self._on_connection)
        QLocalServer.removeServer(SERVER_NAME)
        ok = self._server.listen(SERVER_NAME)
        self._ok = ok

    def _on_connection(self):
        sock = self._server.nextPendingConnection()
        if sock is None:
            return
        while sock.waitForReadyRead(500):
            pass
        data = bytes(sock.readAll())
        sock.disconnectFromServer()
        sock.close()
        try:
            paths = json.loads(data.decode("utf-8"))
            if isinstance(paths, list):
                self.paths_received.emit(paths)
        except Exception:
            pass

    def close(self):
        try:
            self._server.close()
            QLocalServer.removeServer(SERVER_NAME)
        except Exception:
            pass