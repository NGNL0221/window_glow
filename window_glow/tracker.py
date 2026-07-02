import ctypes
import time
from . import utils


class ForegroundTracker:
    def __init__(self, excluded_classes):
        self._excluded_classes = excluded_classes
        self._last_hwnd = None
        self._last_rect = None
        self._last_poll = 0.0
        self._interval = 0.0
        self._last_screen_bounds = None

    @staticmethod
    def _get_dwm_rect(hwnd):
        rect = utils.RECT()
        result = utils.dwmapi.DwmGetWindowAttribute(
            hwnd,
            utils.DWMWA_EXTENDED_FRAME_BOUNDS,
            ctypes.byref(rect),
            ctypes.sizeof(rect),
        )
        if result == 0 and (rect.right - rect.left) > 0 and (rect.bottom - rect.top) > 0:
            return (rect.left, rect.top, rect.right, rect.bottom)
        return None

    @staticmethod
    def _get_normal_rect(hwnd):
        rect = utils.RECT()
        if utils.user32.GetWindowRect(hwnd, ctypes.byref(rect)):
            w = rect.right - rect.left
            h = rect.bottom - rect.top
            if w > 0 and h > 0:
                return (rect.left, rect.top, rect.right, rect.bottom)
        return None

    def _get_window_rect(self, hwnd):
        dwm_rect = self._get_dwm_rect(hwnd)
        if dwm_rect is not None:
            return dwm_rect
        return self._get_normal_rect(hwnd)

    def poll(self):
        now = time.perf_counter()
        if now - self._last_poll < self._interval:
            return None

        self._last_poll = now
        hwnd = utils.user32.GetForegroundWindow()
        if hwnd is None or hwnd == 0:
            self._last_hwnd = None
            return ("hide", None, None, None, None)

        if utils.is_special_window(hwnd):
            if self._last_hwnd is not None:
                self._last_hwnd = None
                return ("hide", None, None, None, None)
            return None

        if not utils.user32.IsWindowVisible(hwnd):
            if self._last_hwnd is not None:
                self._last_hwnd = None
                return ("hide", None, None, None, None)
            return None

        if utils.user32.IsIconic(hwnd):
            if self._last_hwnd is not None:
                self._last_hwnd = None
                return ("hide", None, None, None, None)
            return None

        rect_tuple = self._get_window_rect(hwnd)
        if rect_tuple is None:
            if self._last_hwnd is not None:
                self._last_hwnd = None
                return ("hide", None, None, None, None)
            return None

        w = rect_tuple[2] - rect_tuple[0]
        h = rect_tuple[3] - rect_tuple[1]

        screen_bounds = (
            utils.user32.GetSystemMetrics(utils.SM_XVIRTUALSCREEN),
            utils.user32.GetSystemMetrics(utils.SM_YVIRTUALSCREEN),
            utils.user32.GetSystemMetrics(utils.SM_CXVIRTUALSCREEN),
            utils.user32.GetSystemMetrics(utils.SM_CYVIRTUALSCREEN),
        )
        screen_w = screen_bounds[2]
        screen_h = screen_bounds[3]

        if w >= screen_w - 10 and h >= screen_h - 10:
            if self._last_hwnd is not None:
                self._last_hwnd = None
                return ("hide", None, None, None, None)
            return None

        cls = utils.get_window_class(hwnd)
        if cls in self._excluded_classes:
            if self._last_hwnd is not None:
                self._last_hwnd = None
                return ("hide", None, None, None, None)
            return None

        changed = False
        if hwnd != self._last_hwnd:
            changed = True
            self._last_hwnd = hwnd
            self._last_rect = rect_tuple
            return ("show", hwnd, rect_tuple[0], rect_tuple[1], w, h)

        if rect_tuple != self._last_rect:
            self._last_rect = rect_tuple
            return ("move", hwnd, rect_tuple[0], rect_tuple[1], w, h)

        return None
