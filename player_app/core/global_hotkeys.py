"""Global hotkeys via Win32 RegisterHotKey, disabled by default (empty strings)."""
import ctypes
from ctypes import wintypes

from PyQt5.QtCore import QAbstractNativeEventFilter, QObject, pyqtSignal

MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
MOD_NOREPEAT = 0x4000
WM_HOTKEY = 0x0312

MOD_NAMES = [(MOD_CONTROL, "Ctrl"), (MOD_ALT, "Alt"), (MOD_SHIFT, "Shift"), (MOD_WIN, "Win")]

# Set up proper argtypes/restype for 64-bit Windows — HWND is pointer-sized,
# and without this ctypes defaults to 32-bit int, truncating the handle.
_user32 = ctypes.windll.user32
_user32.RegisterHotKey.argtypes = [wintypes.HWND, wintypes.INT, wintypes.UINT, wintypes.UINT]
_user32.RegisterHotKey.restype = wintypes.BOOL
_user32.UnregisterHotKey.argtypes = [wintypes.HWND, wintypes.INT]
_user32.UnregisterHotKey.restype = wintypes.BOOL

_VK_MAP: dict[str, int] = {
    # Letters
    "A": 0x41, "B": 0x42, "C": 0x43, "D": 0x44, "E": 0x45, "F": 0x46,
    "G": 0x47, "H": 0x48, "I": 0x49, "J": 0x4A, "K": 0x4B, "L": 0x4C,
    "M": 0x4D, "N": 0x4E, "O": 0x4F, "P": 0x50, "Q": 0x51, "R": 0x52,
    "S": 0x53, "T": 0x54, "U": 0x55, "V": 0x56, "W": 0x57, "X": 0x58,
    "Y": 0x59, "Z": 0x5A,
    # Main numbers
    "0": 0x30, "1": 0x31, "2": 0x32, "3": 0x33, "4": 0x34,
    "5": 0x35, "6": 0x36, "7": 0x37, "8": 0x38, "9": 0x39,
    # Numpad (distinct from main keyboard numbers)
    "Num0": 0x60, "Num1": 0x61, "Num2": 0x62, "Num3": 0x63, "Num4": 0x64,
    "Num5": 0x65, "Num6": 0x66, "Num7": 0x67, "Num8": 0x68, "Num9": 0x69,
    "Num*": 0x6A, "Num+": 0x6B, "Num-": 0x6D, "Num.": 0x6E, "Num/": 0x6F,
    # Function keys
    "F1": 0x70, "F2": 0x71, "F3": 0x72, "F4": 0x73, "F5": 0x74, "F6": 0x75,
    "F7": 0x76, "F8": 0x77, "F9": 0x78, "F10": 0x79, "F11": 0x7A, "F12": 0x7B,
    # Special
    "Space": 0x20, "Tab": 0x09, "Return": 0x0D, "Backspace": 0x08,
    "Delete": 0x2E, "Insert": 0x2D, "Home": 0x24, "End": 0x23,
    "PageUp": 0x21, "PageDown": 0x22,
    "Up": 0x26, "Down": 0x28, "Left": 0x25, "Right": 0x27,
    "Escape": 0x1B, "Print": 0x2C, "ScrollLock": 0x91,
    "Pause": 0x13, "Menu": 0x5D, "CapsLock": 0x14, "NumLock": 0x90,
    ";": 0xBA, "=": 0xBB, ",": 0xBC, "-": 0xBD, ".": 0xBE,
    "/": 0xBF, "`": 0xC0, "[": 0xDB, "\\": 0xDC, "]": 0xDD, "'": 0xDE,
}

_VK_TO_NAME: dict[int, str] = {vk: name for name, vk in _VK_MAP.items()}


class GlobalHotkeyManager(QObject, QAbstractNativeEventFilter):
    play_pause_pressed = pyqtSignal()
    prev_pressed = pyqtSignal()
    next_pressed = pyqtSignal()

    def __init__(self, parent=None):
        QObject.__init__(self, parent)
        self._hotkeys: dict[int, tuple] = {}
        self._next_id = 1

    def parse(self, s: str) -> tuple:
        """Parse a key string like 'Ctrl+Shift+P' into (modifiers, vk). Returns (0,0) if empty."""
        if not s or not s.strip():
            return 0, 0
        parts = s.strip().split("+")
        mods = 0
        vk = 0
        for part in parts:
            p = part.strip()
            for m, name in MOD_NAMES:
                if p.lower() == name.lower():
                    mods |= m
                    break
            else:
                vk = _VK_MAP.get(p, 0)
        return mods, vk

    def to_string(self, mods: int, vk: int) -> str:
        """Serialize modifiers + vk back to a display string."""
        if vk == 0:
            return ""
        parts = [name for m, name in MOD_NAMES if mods & m]
        key_name = _VK_TO_NAME.get(vk, f"VK{vk}")
        parts.append(key_name)
        return "+".join(parts)

    def register(self, hwnd: int, hotkey_id: int, s: str) -> bool:
        """Register a hotkey string. Returns True on success.

        Empty string = disabled (returns True).
        Single key without modifiers = rejected (returns False).
        """
        mods, vk = self.parse(s)
        if vk == 0:
            return True  # empty = disabled, not a failure
        if mods == 0:
            print(f"[hotkey] REJECTED bare key: '{s}' — requires at least one modifier")
            return False
        ok = _user32.RegisterHotKey(hwnd, hotkey_id, mods | MOD_NOREPEAT, vk)
        err = ctypes.get_last_error() if not ok else 0
        print(f"[hotkey] RegisterHotKey(hwnd=0x{hwnd:X}, id={hotkey_id}, mods=0x{mods|MOD_NOREPEAT:04X}, vk=0x{vk:02X}) -> {bool(ok)} err={err}")
        return bool(ok)

    def unregister(self, hwnd: int, hotkey_id: int):
        _user32.UnregisterHotKey(hwnd, hotkey_id)

    def unregister_all(self, hwnd: int):
        for hid in list(self._hotkeys):
            self.unregister(hwnd, hid)
        self._hotkeys.clear()

    def apply(self, hwnd: int, hotkeys: dict) -> dict:
        """Apply hotkey dict {'play': 'Ctrl+Shift+P', ...}. Returns applied dict with failures cleared."""
        self.unregister_all(hwnd)
        self._next_id = 1
        key_map = {
            "play": (1, self.play_pause_pressed),
            "prev": (2, self.prev_pressed),
            "next": (3, self.next_pressed),
        }
        result = {}
        for setting_key, (hid, signal) in key_map.items():
            s = hotkeys.get(setting_key, "")
            if self.register(hwnd, hid, s):
                result[setting_key] = s
                self._hotkeys[hid] = (signal, s)
            else:
                result[setting_key] = ""
        return result

    def nativeEventFilter(self, event_type, message):
        msg = wintypes.MSG.from_address(int(message))
        if msg.message == WM_HOTKEY:
            hid = msg.wParam
            print(f"[hotkey] WM_HOTKEY received: id={hid}")
            entry = self._hotkeys.get(hid)
            if entry:
                print(f"[hotkey] emitting signal for id={hid}")
                entry[0].emit()
            else:
                print(f"[hotkey] unknown id={hid}, registered={list(self._hotkeys.keys())}")
            return True, 0
        return False, 0