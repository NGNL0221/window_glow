import json
import os


DEFAULT_CONFIG = {
    "border_width": 15,
    "color": {
        "start_hue": 180,
        "end_hue": 270
    },
    "animation": {
        "enabled": False,
        "speed": 0.8,
        "intensity": 0.3,
        "fade_duration_ms": 200
    },
    "poll_interval_ms": 30,
    "hotkey": {
        "enabled": True,
        "modifiers": "Alt",
        "key": "B"
    },
    "excluded_classes": [
        "Progman", "WorkerW", "Shell_TrayWnd",
        "Windows.UI.Core.CoreWindow", "ApplicationFrameWindow",
        "MultitaskingViewFrame", "TaskSwitcherWnd",
        "ImmersiveLauncher", "MSCTFIME UI"
    ]
}


class Config:
    def __init__(self, path=None):
        self.data = {k: v for k, v in DEFAULT_CONFIG.items()}
        self._path = path
        if path and os.path.isfile(path):
            self._load(path)

    def _load(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            self._merge(self.data, loaded)
        except (json.JSONDecodeError, IOError):
            pass

    def _merge(self, base, override):
        for k, v in override.items():
            if k in base and isinstance(base[k], dict) and isinstance(v, dict):
                self._merge(base[k], v)
            else:
                base[k] = v

    @property
    def border_width(self):
        return self.data["border_width"]

    @property
    def start_hue(self):
        return self.data["color"]["start_hue"]

    @property
    def end_hue(self):
        return self.data["color"]["end_hue"]

    @property
    def animation_enabled(self):
        return self.data["animation"]["enabled"]

    @property
    def animation_speed(self):
        return self.data["animation"]["speed"]

    @property
    def animation_intensity(self):
        return self.data["animation"]["intensity"]

    @property
    def fade_duration_ms(self):
        return self.data["animation"]["fade_duration_ms"]

    @property
    def poll_interval_ms(self):
        return self.data["poll_interval_ms"]

    @property
    def hotkey_enabled(self):
        return self.data["hotkey"]["enabled"]

    @property
    def hotkey_modifiers(self):
        return self.data["hotkey"]["modifiers"]

    @property
    def hotkey_key(self):
        return self.data["hotkey"]["key"]

    @property
    def excluded_classes(self):
        return set(self.data["excluded_classes"])
