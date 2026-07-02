import ctypes
from ctypes import wintypes
from . import utils

_kernel32 = ctypes.windll.kernel32
_user32 = ctypes.windll.user32
_shell32 = ctypes.windll.shell32
_gdi32 = ctypes.windll.gdi32

WM_USER = 0x0400
WM_TRAY = WM_USER + 100
WM_TASKBARCREATED = 0

NIM_ADD = 0x00000000
NIM_MODIFY = 0x00000001
NIM_DELETE = 0x00000002
NIF_MESSAGE = 0x00000001
NIF_ICON = 0x00000002
NIF_TIP = 0x00000004

TPM_RIGHTALIGN = 0x0008
TPM_BOTTOMALIGN = 0x0020
TPM_RETURNCMD = 0x0100

MF_STRING = 0x00000000
MF_SEPARATOR = 0x00000800

ID_TOGGLE = 1001
ID_EXIT = 1002


class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


class NOTIFYICONDATAW(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("hWnd", wintypes.HWND),
        ("uID", wintypes.UINT),
        ("uFlags", wintypes.UINT),
        ("uCallbackMessage", wintypes.UINT),
        ("hIcon", wintypes.HICON),
        ("szTip", wintypes.WCHAR * 128),
        ("dwState", wintypes.DWORD),
        ("dwStateMask", wintypes.DWORD),
        ("szInfo", wintypes.WCHAR * 256),
        ("uTimeout", wintypes.UINT),
        ("szInfoTitle", wintypes.WCHAR * 64),
        ("dwInfoFlags", wintypes.DWORD),
    ]


class ICONINFO(ctypes.Structure):
    _fields_ = [
        ("fIcon", wintypes.BOOL),
        ("xHotspot", wintypes.DWORD),
        ("yHotspot", wintypes.DWORD),
        ("hbmMask", wintypes.HBITMAP),
        ("hbmColor", wintypes.HBITMAP),
    ]


_tray_instance = None


def _create_tray_icon():
    """Create a 16x16 cyan colored circle icon."""
    color_data = bytearray(16 * 16 * 4)
    cx, cy = 7.5, 7.5
    r2 = 6.5 * 6.5
    for y in range(16):
        for x in range(16):
            idx = (y * 16 + x) * 4
            dx = x - cx
            dy = y - cy
            d2 = dx * dx + dy * dy
            if d2 <= r2:
                t = d2 / r2
                r_val = int(255 * t)
                g_val = int(200 - (200 - 128) * t * t)
                b_val = int(100 * (1 - t))
                color_data[idx] = b_val
                color_data[idx + 1] = g_val
                color_data[idx + 2] = r_val
                color_data[idx + 3] = 255
            elif d2 <= r2 + 4:
                t = (d2 - r2) / 4.0
                a = int(255 * (1 - t))
                r_val = int(255 * (r2 / d2))
                g_val = int(150 * (r2 / d2))
                b_val = int(80 * (r2 / d2))
                color_data[idx] = b_val
                color_data[idx + 1] = g_val
                color_data[idx + 2] = r_val
                color_data[idx + 3] = a

    hdc = _gdi32.CreateCompatibleDC(None)
    bmi = utils.BITMAPINFO()
    bmi.bmiHeader.biSize = ctypes.sizeof(utils.BITMAPINFOHEADER)
    bmi.bmiHeader.biWidth = 16
    bmi.bmiHeader.biHeight = -16
    bmi.bmiHeader.biPlanes = 1
    bmi.bmiHeader.biBitCount = 32
    bmi.bmiHeader.biCompression = utils.BI_RGB

    ppv = ctypes.c_void_p()
    hbmp = _gdi32.CreateDIBSection(hdc, ctypes.byref(bmi), utils.DIB_RGB_COLORS, ctypes.byref(ppv), None, 0)
    n_bytes = 16 * 16 * 4
    buf_dst = (ctypes.c_uint8 * n_bytes).from_address(ppv.value)
    buf_src = (ctypes.c_uint8 * n_bytes).from_buffer(color_data)
    ctypes.memmove(buf_dst, buf_src, n_bytes)

    mask_bits = (ctypes.c_uint8 * 32)()
    for i in range(32):
        mask_bits[i] = 0xFF
    hbm_mask = _gdi32.CreateBitmap(16, 16, 1, 1, mask_bits)

    ii = ICONINFO()
    ii.fIcon = True
    ii.hbmColor = hbmp
    ii.hbmMask = hbm_mask
    hicon = _user32.CreateIconIndirect(ctypes.byref(ii))

    _gdi32.DeleteObject(hbmp)
    _gdi32.DeleteObject(hbm_mask)
    _gdi32.DeleteDC(hdc)
    return hicon


class TrayIcon:
    def __init__(self, toggle_cb, exit_cb):
        global _tray_instance
        _tray_instance = self
        self._toggle_cb = toggle_cb
        self._exit_cb = exit_cb
        self._hwnd = None
        self._hicon = None
        self._wnd_proc = None

    def start(self):
        global WM_TASKBARCREATED

        hinst = _kernel32.GetModuleHandleW(None)

        @ctypes.WINFUNCTYPE(ctypes.c_longlong, wintypes.HWND, ctypes.c_uint, wintypes.WPARAM, wintypes.LPARAM)
        def wnd_proc(hwnd, msg, wparam, lparam):
            if msg == WM_TASKBARCREATED:
                self._add_icon()
                return 0
            if msg == WM_TRAY:
                if lparam == 0x0205 or lparam == 0x0204:
                    self._on_rclick()
                elif lparam == 0x0203 or lparam == 0x0202:
                    self._toggle_cb()
                return 0
            return _user32.DefWindowProcW(hwnd, msg, wparam, lparam)

        self._wnd_proc = wnd_proc

        cls_name = "WG_Tray"

        wc = utils.WNDCLASSEXW()
        wc.cbSize = ctypes.sizeof(utils.WNDCLASSEXW)
        wc.lpfnWndProc = ctypes.cast(wnd_proc, ctypes.c_void_p)
        wc.hInstance = hinst
        wc.lpszClassName = cls_name
        _user32.RegisterClassExW(ctypes.byref(wc))

        self._hwnd = _user32.CreateWindowExW(
            0, cls_name, "", 0, 0, 0, 0, 0, None, None, hinst, None,
        )

        self._hicon = _create_tray_icon()
        self._add_icon()

        WM_TASKBARCREATED = _user32.RegisterWindowMessageW("TaskbarCreated")

    def _add_icon(self):
        nid = NOTIFYICONDATAW()
        nid.cbSize = ctypes.sizeof(NOTIFYICONDATAW)
        nid.hWnd = self._hwnd
        nid.uID = 1
        nid.uFlags = NIF_ICON | NIF_MESSAGE | NIF_TIP
        nid.uCallbackMessage = WM_TRAY
        nid.hIcon = self._hicon
        nid.szTip = "WindowGlow"
        _shell32.Shell_NotifyIconW(NIM_ADD, ctypes.byref(nid))

    def _on_rclick(self):
        menu = _user32.CreatePopupMenu()
        _user32.AppendMenuW(menu, MF_STRING, ID_TOGGLE, "Toggle Glow")
        _user32.AppendMenuW(menu, MF_SEPARATOR, 0, None)
        _user32.AppendMenuW(menu, MF_STRING, ID_EXIT, "Exit")

        pt = POINT()
        _user32.GetCursorPos(ctypes.byref(pt))
        cmd = _user32.TrackPopupMenu(
            menu, TPM_RIGHTALIGN | TPM_BOTTOMALIGN | TPM_RETURNCMD,
            pt.x, pt.y, 0, self._hwnd, None,
        )
        _user32.DestroyMenu(menu)

        if cmd == ID_TOGGLE:
            self._toggle_cb()
        elif cmd == ID_EXIT:
            self._exit_cb()

    def _on_dblclick(self):
        self._toggle_cb()

    def stop(self):
        if self._hwnd:
            nid = NOTIFYICONDATAW()
            nid.cbSize = ctypes.sizeof(NOTIFYICONDATAW)
            nid.hWnd = self._hwnd
            nid.uID = 1
            _shell32.Shell_NotifyIconW(NIM_DELETE, ctypes.byref(nid))
            _user32.DestroyWindow(self._hwnd)
            self._hwnd = None
        if self._hicon:
            _user32.DestroyIcon(self._hicon)
            self._hicon = None
