import sys
import os
import time
import ctypes
import signal

from . import utils
from .config import Config
from .overlay import OverlayWindow
from .tracker import ForegroundTracker
from .animation import Animation
from .renderer import generate_glow_bitmap
from .tray import TrayIcon


def main():
    config_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(config_dir, "config.json")
    config = Config(config_path)

    overlay = OverlayWindow()
    overlay.create()

    tracker = ForegroundTracker(config.excluded_classes)
    anim = Animation(config)

    current_rect = None
    fading_out = False
    last_multiplier = 0.0
    enabled = True
    running = True

    def toggle():
        nonlocal enabled
        enabled = not enabled
        if not enabled:
            anim.hide()

    def on_exit():
        nonlocal running
        running = False

    tray = TrayIcon(toggle, on_exit)
    tray.start()

    signal.signal(signal.SIGINT, lambda *a: on_exit())
    signal.signal(signal.SIGTERM, lambda *a: on_exit())

    try:
        border = config.border_width
        start_hue = config.start_hue
        end_hue = config.end_hue
        frame_budget = 1.0 / 120.0

        move_streak = 0
        dragging = False
        stationary_frames = 0
        DRAG_THRESHOLD = 3
        RESUME_DELAY = 12

        while running:
            loop_start = time.perf_counter()

            msg = utils.MSG()
            msg_count = 0
            while msg_count < 5 and utils.user32.PeekMessageW(
                ctypes.byref(msg), None, 0, 0, utils.PM_REMOVE
            ):
                msg_count += 1
                if msg.message == utils.WM_QUIT:
                    running = False
                    break
                utils.user32.TranslateMessage(ctypes.byref(msg))
                utils.user32.DispatchMessageW(ctypes.byref(msg))

            if not running:
                break

            if not enabled:
                if overlay._visible:
                    overlay.hide()
                    current_rect = None
                    fading_out = False
                time.sleep(0.05)
                continue

            result = tracker.poll()
            if result:
                action = result[0]
                if action == "show":
                    _, _hwnd, x, y, w, h = result
                    overlay.show(x, y, w, h, _hwnd)
                    current_rect = (x, y, w, h)
                    fading_out = False
                    anim.show()
                    last_multiplier = -1.0
                    move_streak = 0
                    dragging = False
                    stationary_frames = 0
                elif action == "move":
                    _, _hwnd, x, y, w, h = result
                    overlay.show(x, y, w, h, _hwnd)
                    current_rect = (x, y, w, h)
                    fading_out = False
                    overlay.reposition(border)
                    move_streak += 1
                    if move_streak >= DRAG_THRESHOLD:
                        dragging = True
                    stationary_frames = 0
                elif action == "hide":
                    fading_out = True
                    anim.hide()
            else:
                if move_streak > 0:
                    move_streak = max(0, move_streak - 1)
                if dragging:
                    stationary_frames += 1
                    if stationary_frames > RESUME_DELAY:
                        dragging = False
                        stationary_frames = 0
                        last_multiplier = -1.0

            multiplier = anim.tick()
            changed = abs(multiplier - last_multiplier) > 0.003

            need_render = current_rect and multiplier > 0.001 and changed
            if dragging:
                need_render = False

            if need_render:
                x, y, w, h = current_rect
                buf, tw, th = generate_glow_bitmap(
                    w, h, border, start_hue, end_hue, multiplier,
                )
                overlay.update_frame(border, buf, tw, th)
                last_multiplier = multiplier

            if fading_out and multiplier <= 0.001:
                overlay.hide()
                current_rect = None
                fading_out = False

            elapsed = time.perf_counter() - loop_start
            sleep_time = frame_budget - elapsed
            if sleep_time > 0.001:
                time.sleep(sleep_time)

    except KeyboardInterrupt:
        pass
    finally:
        overlay.destroy()
        tray.stop()


if __name__ == "__main__":
    main()
