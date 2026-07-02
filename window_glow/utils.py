import ctypes
from ctypes import wintypes
import math

if not hasattr(wintypes, "HCURSOR"):
    wintypes.HCURSOR = wintypes.HICON

# ─── Constants ───────────────────────────────────────────────────────────────

WS_POPUP = 0x80000000
WS_EX_LAYERED = 0x00080000
WS_EX_TRANSPARENT = 0x00000020
WS_EX_TOPMOST = 0x00000008
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_NOACTIVATE = 0x08000000

ULW_ALPHA = 0x00000002
AC_SRC_OVER = 0x00
AC_SRC_ALPHA = 0x01

DIB_RGB_COLORS = 0
BI_RGB = 0

SM_CXSCREEN = 0
SM_CYSCREEN = 1
SM_XVIRTUALSCREEN = 76
SM_YVIRTUALSCREEN = 77
SM_CXVIRTUALSCREEN = 78
SM_CYVIRTUALSCREEN = 79

DWMWA_EXTENDED_FRAME_BOUNDS = 9

WM_HOTKEY = 0x0312
WM_DESTROY = 0x0002
WM_CLOSE = 0x0010
WM_QUIT = 0x0012

MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008

PM_REMOVE = 0x0001
PM_NOREMOVE = 0x0000

SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SWP_NOACTIVATE = 0x0010
SWP_SHOWWINDOW = 0x0040

DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 = ctypes.c_void_p(-4)

# Try modern DPI API
_user32_init = ctypes.windll.user32
try:
    _user32_init.SetProcessDpiAwarenessContext(DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2)
except Exception:
    _user32_init.SetProcessDPIAware()

HWND_TOPMOST = wintypes.HWND(-1)

# ─── Structures ──────────────────────────────────────────────────────────────

class RECT(ctypes.Structure):
    _fields_ = [
        ("left",   ctypes.c_long),
        ("top",    ctypes.c_long),
        ("right",  ctypes.c_long),
        ("bottom", ctypes.c_long),
    ]

class POINT(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_long),
        ("y", ctypes.c_long),
    ]

class SIZE(ctypes.Structure):
    _fields_ = [
        ("cx", ctypes.c_long),
        ("cy", ctypes.c_long),
    ]

class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize",          ctypes.c_uint32),
        ("biWidth",         ctypes.c_int32),
        ("biHeight",        ctypes.c_int32),
        ("biPlanes",        ctypes.c_uint16),
        ("biBitCount",      ctypes.c_uint16),
        ("biCompression",   ctypes.c_uint32),
        ("biSizeImage",     ctypes.c_uint32),
        ("biXPelsPerMeter", ctypes.c_int32),
        ("biYPelsPerMeter", ctypes.c_int32),
        ("biClrUsed",       ctypes.c_uint32),
        ("biClrImportant",  ctypes.c_uint32),
    ]

class BITMAPINFO(ctypes.Structure):
    _fields_ = [
        ("bmiHeader", BITMAPINFOHEADER),
    ]

class BLENDFUNCTION(ctypes.Structure):
    _fields_ = [
        ("BlendOp",             ctypes.c_byte),
        ("BlendFlags",          ctypes.c_byte),
        ("SourceConstantAlpha", ctypes.c_byte),
        ("AlphaFormat",         ctypes.c_byte),
    ]

class WNDCLASSEXW(ctypes.Structure):
    _fields_ = [
        ("cbSize",        ctypes.c_uint),
        ("style",         ctypes.c_uint),
        ("lpfnWndProc",   ctypes.c_void_p),
        ("cbClsExtra",    ctypes.c_int),
        ("cbWndExtra",    ctypes.c_int),
        ("hInstance",     wintypes.HINSTANCE),
        ("hIcon",         wintypes.HICON),
        ("hCursor",       wintypes.HCURSOR),
        ("hbrBackground", wintypes.HBRUSH),
        ("lpszMenuName",  ctypes.c_wchar_p),
        ("lpszClassName", ctypes.c_wchar_p),
        ("hIconSm",       wintypes.HICON),
    ]

class MSG(ctypes.Structure):
    _fields_ = [
        ("hwnd",    wintypes.HWND),
        ("message", ctypes.c_uint),
        ("wParam",  wintypes.WPARAM),
        ("lParam",  wintypes.LPARAM),
        ("time",    ctypes.c_uint32),
        ("pt",      POINT),
    ]

# ─── DLL Bindings ────────────────────────────────────────────────────────────

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32
kernel32 = ctypes.windll.kernel32
dwmapi = ctypes.windll.dwmapi

_user32_funcs = {
    "GetForegroundWindow":   ([], wintypes.HWND),
    "GetWindowRect":         ([wintypes.HWND, ctypes.POINTER(RECT)], wintypes.BOOL),
    "GetWindowLongPtrW":     ([wintypes.HWND, ctypes.c_int], ctypes.c_longlong),
    "GetSystemMetrics":      ([ctypes.c_int], ctypes.c_int),
    "SetProcessDPIAware":    ([], wintypes.BOOL),
    "DestroyWindow":         ([wintypes.HWND], wintypes.BOOL),
    "PostQuitMessage":       ([ctypes.c_int], None),
    "DefWindowProcW":        ([wintypes.HWND, ctypes.c_uint, wintypes.WPARAM, wintypes.LPARAM], ctypes.c_longlong),
    "TranslateMessage":      ([ctypes.POINTER(MSG)], wintypes.BOOL),
    "DispatchMessageW":      ([ctypes.POINTER(MSG)], ctypes.c_longlong),
    "PeekMessageW":          ([ctypes.POINTER(MSG), wintypes.HWND, ctypes.c_uint, ctypes.c_uint, ctypes.c_uint], wintypes.BOOL),
    "RegisterHotKey":        ([wintypes.HWND, ctypes.c_int, ctypes.c_uint, ctypes.c_uint], wintypes.BOOL),
    "UnregisterHotKey":      ([wintypes.HWND, ctypes.c_int], wintypes.BOOL),
    "GetClassNameW":         ([wintypes.HWND, ctypes.c_wchar_p, ctypes.c_int], ctypes.c_int),
    "IsWindowVisible":       ([wintypes.HWND], wintypes.BOOL),
    "IsIconic":              ([wintypes.HWND], wintypes.BOOL),
    "GetWindowThreadProcessId": ([wintypes.HWND, ctypes.POINTER(ctypes.c_uint32)], ctypes.c_uint32),
    "ShowWindow":            ([wintypes.HWND, ctypes.c_int], wintypes.BOOL),
}

for name, (argtypes, restype) in _user32_funcs.items():
    func = getattr(user32, name)
    if argtypes:
        func.argtypes = argtypes
    func.restype = restype

_gdi32_funcs = {
    "CreateCompatibleDC":    ([wintypes.HDC], wintypes.HDC),
    "DeleteDC":              ([wintypes.HDC], wintypes.BOOL),
    "CreateDIBSection":      ([wintypes.HDC, ctypes.POINTER(BITMAPINFO), ctypes.c_uint, ctypes.POINTER(ctypes.c_void_p), wintypes.HANDLE, ctypes.c_uint32], wintypes.HBITMAP),
    "DeleteObject":          ([wintypes.HGDIOBJ], wintypes.BOOL),
    "SelectObject":          ([wintypes.HDC, wintypes.HGDIOBJ], wintypes.HGDIOBJ),
}

for name, (argtypes, restype) in _gdi32_funcs.items():
    func = getattr(gdi32, name)
    if argtypes:
        func.argtypes = argtypes
    func.restype = restype

kernel32.GetModuleHandleW.argtypes = [ctypes.c_wchar_p]
kernel32.GetModuleHandleW.restype = wintypes.HINSTANCE

dwmapi.DwmGetWindowAttribute.argtypes = [wintypes.HWND, ctypes.c_uint32, ctypes.c_void_p, ctypes.c_uint32]
dwmapi.DwmGetWindowAttribute.restype = ctypes.c_long

# ─── SetWindowPos ────────────────────────────────────────────────────────────

user32.SetWindowPos.argtypes = [
    wintypes.HWND, wintypes.HWND,
    ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
    ctypes.c_uint,
]
user32.SetWindowPos.restype = wintypes.BOOL

# ─── CreateWindowExW ─────────────────────────────────────────────────────────

user32.CreateWindowExW.argtypes = [
    ctypes.c_uint32,           # dwExStyle
    ctypes.c_wchar_p,          # lpClassName
    ctypes.c_wchar_p,          # lpWindowName
    ctypes.c_uint32,           # dwStyle
    ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,  # x, y, w, h
    wintypes.HWND,             # hWndParent
    wintypes.HMENU,            # hMenu
    wintypes.HINSTANCE,        # hInstance
    wintypes.LPVOID,           # lpParam
]
user32.CreateWindowExW.restype = wintypes.HWND

# ─── UpdateLayeredWindow ─────────────────────────────────────────────────────

user32.UpdateLayeredWindow.argtypes = [
    wintypes.HWND,                    # hWnd
    wintypes.HDC,                     # hdcDst  (NULL = use screen)
    ctypes.POINTER(POINT),            # pptDst
    ctypes.POINTER(SIZE),             # psize
    wintypes.HDC,                     # hdcSrc
    ctypes.POINTER(POINT),            # pptSrc
    ctypes.c_uint32,                  # crKey
    ctypes.POINTER(BLENDFUNCTION),    # pblend
    ctypes.c_uint32,                  # dwFlags
]
user32.UpdateLayeredWindow.restype = wintypes.BOOL

# ─── RegisterClassExW ────────────────────────────────────────────────────────

user32.RegisterClassExW.argtypes = [ctypes.POINTER(WNDCLASSEXW)]
user32.RegisterClassExW.restype = wintypes.ATOM

# ─── WNDPROC type ────────────────────────────────────────────────────────────

WNDPROC = ctypes.WINFUNCTYPE(ctypes.c_longlong, wintypes.HWND, ctypes.c_uint, wintypes.WPARAM, wintypes.LPARAM)

# ─── Color helpers ───────────────────────────────────────────────────────────

_TAU = math.pi * 2

def _hue_to_rgb(p, q, t):
    if t < 0:
        t += 1
    if t > 1:
        t -= 1
    if t < 1 / 6:
        return p + (q - p) * 6 * t
    if t < 1 / 2:
        return q
    if t < 2 / 3:
        return p + (q - p) * (2 / 3 - t) * 6
    return p

def hsl_to_rgb(h, s, l):
    if s == 0:
        v = int(l * 255)
        return v, v, v
    q = l * (1 + s) if l < 0.5 else l + s - l * s
    p = 2 * l - q
    r = _hue_to_rgb(p, q, h + 1 / 3)
    g = _hue_to_rgb(p, q, h)
    b = _hue_to_rgb(p, q, h - 1 / 3)
    return int(r * 255), int(g * 255), int(b * 255)


SPECIAL_CLASSES = {
    "Progman", "WorkerW", "Shell_TrayWnd",
    "Windows.UI.Core.CoreWindow", "ApplicationFrameWindow",
    "MultitaskingViewFrame", "TaskSwitcherWnd",
    "ImmersiveLauncher", "MSCTFIME UI",
}

def get_window_class(hwnd):
    buf = ctypes.create_unicode_buffer(256)
    if user32.GetClassNameW(hwnd, buf, 256):
        return buf.value
    return ""

def is_special_window(hwnd):
    cls = get_window_class(hwnd)
    if cls in SPECIAL_CLASSES:
        return True
    if cls.startswith("Windows.UI.Core"):
        return True
    return False
