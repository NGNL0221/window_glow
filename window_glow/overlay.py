import ctypes
from . import utils


_simple_proc = None


@utils.WNDPROC
def _simple_wnd_proc(hwnd, msg, wparam, lparam):
    if msg == utils.WM_HOTKEY:
        overlay = _overlays.get(hwnd)
        if overlay and overlay._hotkey_callback:
            overlay._hotkey_callback()
            return 0
    return utils.user32.DefWindowProcW(hwnd, msg, wparam, lparam)


_overlays = {}


class OverlayWindow:
    def __init__(self):
        self._hwnd = None
        self._hdc_mem = None
        self._hbitmap = None
        self._hbitmap_old = None
        self._ppv_bits = None
        self._class_atom = None
        self._tw = 0
        self._th = 0
        self._visible = False
        self._x = 0
        self._y = 0
        self._w = 0
        self._h = 0
        self._target_hwnd = None
        self._hotkey_callback = None

    def create(self):
        if self._hwnd is not None:
            return

        hinst = utils.kernel32.GetModuleHandleW(None)
        cls_name = "WindowGlowOv3"

        wcex = utils.WNDCLASSEXW()
        wcex.cbSize = ctypes.sizeof(utils.WNDCLASSEXW)
        wcex.lpfnWndProc = ctypes.cast(_simple_wnd_proc, ctypes.c_void_p)
        wcex.hInstance = hinst
        wcex.lpszClassName = cls_name

        if not utils.user32.RegisterClassExW(ctypes.byref(wcex)):
            err = ctypes.get_last_error()
            if err != 1410:
                raise OSError(f"RegisterClassExW failed: {err}")

        ex_style = (
            utils.WS_EX_LAYERED
            | utils.WS_EX_TRANSPARENT
            | utils.WS_EX_TOOLWINDOW
            | utils.WS_EX_NOACTIVATE
        )

        self._hwnd = utils.user32.CreateWindowExW(
            ex_style, cls_name, "",
            utils.WS_POPUP,
            0, 0, 0, 0,
            None, None, hinst, None,
        )

        if self._hwnd is None or self._hwnd == 0:
            err = ctypes.get_last_error()
            raise OSError(f"CreateWindowExW failed: {err}")

        _overlays[self._hwnd] = self

    def destroy(self):
        if self._hwnd is None:
            return
        self._free_bitmap()
        _overlays.pop(self._hwnd, None)
        utils.user32.DestroyWindow(self._hwnd)
        self._hwnd = None

    def _free_bitmap(self):
        if self._hdc_mem:
            if self._hbitmap_old:
                utils.gdi32.SelectObject(self._hdc_mem, self._hbitmap_old)
                self._hbitmap_old = None
            utils.gdi32.DeleteDC(self._hdc_mem)
            self._hdc_mem = None
        if self._hbitmap:
            utils.gdi32.DeleteObject(self._hbitmap)
            self._hbitmap = None
        self._ppv_bits = None
        self._tw = 0
        self._th = 0

    def show(self, x, y, w, h, target_hwnd=None):
        self._x, self._y, self._w, self._h = x, y, w, h
        self._target_hwnd = target_hwnd
        self._visible = True

    def hide(self):
        if self._hwnd is None:
            return
        self._visible = False
        utils.user32.ShowWindow(self._hwnd, 0)
        self._free_bitmap()

    def reposition(self, border):
        if not self._visible or self._hwnd is None or self._hdc_mem is None:
            return
        ox = self._x - border
        oy = self._y - border

        pt_dst = utils.POINT(ox, oy)
        sz = utils.SIZE(self._tw, self._th)
        pt_src = utils.POINT(0, 0)
        bf = utils.BLENDFUNCTION()
        bf.BlendOp = utils.AC_SRC_OVER
        bf.BlendFlags = 0
        bf.SourceConstantAlpha = 255
        bf.AlphaFormat = utils.AC_SRC_ALPHA

        utils.user32.UpdateLayeredWindow(
            self._hwnd, None,
            ctypes.byref(pt_dst), ctypes.byref(sz),
            self._hdc_mem, ctypes.byref(pt_src),
            0, ctypes.byref(bf),
            utils.ULW_ALPHA,
        )

    def update_frame(self, border, buffer_data, tw, th):
        if not self._visible or self._hwnd is None:
            return
        if buffer_data is None:
            return

        if self._tw != tw or self._th != th or self._hbitmap is None:
            self._free_bitmap()

            if tw <= 0 or th <= 0:
                return

            self._hdc_mem = utils.gdi32.CreateCompatibleDC(None)
            if self._hdc_mem is None or self._hdc_mem == 0:
                self._free_bitmap()
                return

            bmi = utils.BITMAPINFO()
            bmi.bmiHeader.biSize = ctypes.sizeof(utils.BITMAPINFOHEADER)
            bmi.bmiHeader.biWidth = tw
            bmi.bmiHeader.biHeight = -th
            bmi.bmiHeader.biPlanes = 1
            bmi.bmiHeader.biBitCount = 32
            bmi.bmiHeader.biCompression = utils.BI_RGB

            ppv = ctypes.c_void_p()
            self._hbitmap = utils.gdi32.CreateDIBSection(
                self._hdc_mem, ctypes.byref(bmi),
                utils.DIB_RGB_COLORS, ctypes.byref(ppv),
                None, 0,
            )
            if self._hbitmap is None or self._hbitmap == 0:
                self._free_bitmap()
                return

            self._hbitmap_old = utils.gdi32.SelectObject(self._hdc_mem, self._hbitmap)
            self._ppv_bits = ppv
            self._tw = tw
            self._th = th

        if self._ppv_bits is None or self._ppv_bits.value is None or self._ppv_bits.value == 0:
            return

        n_bytes = tw * th * 4
        buf_size = len(buffer_data)
        copy_bytes = min(n_bytes, buf_size)

        # Direct memory copy: source = bytearray pointer, dest = DIB bits
        src_ptr = (ctypes.c_char * buf_size).from_buffer(buffer_data)
        dst_arr = (ctypes.c_uint8 * n_bytes).from_address(self._ppv_bits.value)
        ctypes.memmove(dst_arr, src_ptr, copy_bytes)

        ox = self._x - border
        oy = self._y - border
        after = self._target_hwnd or utils.HWND_TOPMOST

        utils.user32.SetWindowPos(
            self._hwnd, after,
            ox, oy, tw, th,
            utils.SWP_NOACTIVATE | utils.SWP_SHOWWINDOW,
        )

        pt_dst = utils.POINT(ox, oy)
        sz = utils.SIZE(tw, th)
        pt_src = utils.POINT(0, 0)
        bf = utils.BLENDFUNCTION()
        bf.BlendOp = utils.AC_SRC_OVER
        bf.BlendFlags = 0
        bf.SourceConstantAlpha = 255
        bf.AlphaFormat = utils.AC_SRC_ALPHA

        result = utils.user32.UpdateLayeredWindow(
            self._hwnd, None,
            ctypes.byref(pt_dst), ctypes.byref(sz),
            self._hdc_mem, ctypes.byref(pt_src),
            0, ctypes.byref(bf),
            utils.ULW_ALPHA,
        )
        if not result:
            err = ctypes.get_last_error()
            print(f"[WindowGlow] UpdateLayeredWindow FAILED: err={err}")
