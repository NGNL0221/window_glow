from . import utils


_MOD_MAP = {
    "Alt":     utils.MOD_ALT,
    "Ctrl":    utils.MOD_CONTROL,
    "Shift":   utils.MOD_SHIFT,
    "Win":     utils.MOD_WIN,
}

_VK_MAP = {}


def _key_to_vk(key: str) -> int:
    global _VK_MAP
    if not _VK_MAP:
        for ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            _VK_MAP[ch] = ord(ch)
        for ch in "0123456789":
            _VK_MAP[ch] = ord(ch)
        _VK_MAP.update({
            "F1": 0x70, "F2": 0x71, "F3": 0x72, "F4": 0x73,
            "F5": 0x74, "F6": 0x75, "F7": 0x76, "F8": 0x77,
            "F9": 0x78, "F10": 0x79, "F11": 0x7A, "F12": 0x7B,
            "Space": 0x20, "Tab": 0x09, "Enter": 0x0D,
            "Escape": 0x1B, "Backspace": 0x08,
            "Left": 0x25, "Up": 0x26, "Right": 0x27, "Down": 0x28,
            "Insert": 0x2D, "Delete": 0x2E, "Home": 0x24, "End": 0x23,
            "PageUp": 0x21, "PageDown": 0x22,
        })
    return _VK_MAP.get(key, 0)


HOTKEY_ID = 1


def parse_hotkey(mod_str, key_str):
    mod = 0
    if mod_str:
        for part in mod_str.split("+"):
            part = part.strip().capitalize()
            if part in _MOD_MAP:
                mod |= _MOD_MAP[part]
    vk = _key_to_vk(key_str.strip().upper())
    return mod, vk


def register(hwnd, mod, vk):
    return utils.user32.RegisterHotKey(hwnd, HOTKEY_ID, mod, vk)


def unregister(hwnd):
    utils.user32.UnregisterHotKey(hwnd, HOTKEY_ID)
