import time
import math


class Animation:
    def __init__(self, config):
        self.enabled = config.animation_enabled
        self.speed = config.animation_speed
        self.intensity = config.animation_intensity
        self.fade_duration = config.fade_duration_ms / 1000.0
        self._start_time = time.perf_counter()
        self._visible = False
        self._fade_start = 0.0
        self._fade_from = 0.0
        self._fade_multiplier = 0.0
        self._last_value = 0.0

    def show(self):
        self._visible = True
        self._fade_start = time.perf_counter()
        self._fade_from = max(self._fade_multiplier, 0.6)

    def hide(self):
        self._visible = False
        self._fade_start = time.perf_counter()
        self._fade_from = self._fade_multiplier

    def tick(self) -> float:
        now = time.perf_counter()

        if self._visible:
            target = 1.0
        else:
            target = 0.0

        if self.fade_duration <= 0:
            self._fade_multiplier = target
        else:
            elapsed = now - self._fade_start
            t = min(elapsed / self.fade_duration, 1.0)
            self._fade_multiplier = self._fade_from + (target - self._fade_from) * t

        if self._fade_multiplier < 0.001:
            self._last_value = 0.0
            return 0.0

        base = 0.0

        if self.enabled:
            period = 2.0 / self.speed
            phase = (now % period) / period
            wave = 0.5 - 0.5 * math.cos(phase * 2.0 * math.pi)
            breath = 0.12 + 0.88 * wave
        else:
            breath = 1.0

        result = breath * self._fade_multiplier
        result = max(0.0, min(1.0, result))
        self._last_value = result
        return result

    @property
    def multiplier(self) -> float:
        return self._last_value
