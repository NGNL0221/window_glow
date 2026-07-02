import math


def _hsb(h):
    h = h % 1.0
    h6 = h * 6.0
    i = int(h6)
    f = h6 - i
    q = int(255 * (1.0 - f))
    t = int(255 * f)
    if i == 0:   return 255, t, 0
    elif i == 1: return q, 255, 0
    elif i == 2: return 0, 255, t
    elif i == 3: return 0, q, 255
    elif i == 4: return t, 0, 255
    else:        return 255, 0, q


_BASE_CACHE = None
_BASE_TW = 0
_BASE_TH = 0
_DIST_VER = 2
_CACHE_VER = 0
_COLOR_LUT = None
_COS_LUT = None


def _build_color_lut(start_hue, end_hue):
    r_start, g_start, b_start = _hsb(start_hue / 360.0)
    r_end, g_end, b_end = _hsb(end_hue / 360.0)
    color_lut = [(0, 0, 0)] * 256
    for i in range(256):
        cos_t = (math.cos(i / 256.0 * 2.0 * math.pi) + 1.0) * 0.5
        r = int(r_start + (r_end - r_start) * cos_t)
        g = int(g_start + (g_end - g_start) * cos_t)
        b = int(b_start + (b_end - b_start) * cos_t)
        color_lut[i] = (r, g, b)
    return color_lut


def generate_glow_bitmap(width, height, border, start_hue, end_hue, alpha_multiplier, hue_shift=0.0):
    global _BASE_CACHE, _BASE_TW, _BASE_TH, _COLOR_LUT, _CACHE_VER

    if border <= 0 or width <= 0 or height <= 0 or alpha_multiplier <= 0.001:
        return None, 0, 0

    tw = width + 2 * border
    th = height + 2 * border
    il, it = border, border
    ir, ib = il + width, it + height
    inner = 2
    border_f = float(border)
    cx = tw / 2.0
    cy = th / 2.0

    if _COLOR_LUT is None:
        _COLOR_LUT = _build_color_lut(start_hue, end_hue)

    if _BASE_CACHE is None or _BASE_TW != tw or _BASE_TH != th or _CACHE_VER != _DIST_VER:
        _BASE_TW = tw
        _BASE_TH = th
        _CACHE_VER = _DIST_VER

        def _outer(xs, xe, ys, ye):
            px = []
            for y in range(ys, ye):
                for x in range(xs, xe):
                    if x < il:      dx = il - x
                    elif x >= ir:   dx = x - ir + 1
                    else:           dx = 0
                    if y < it:      dy = it - y
                    elif y >= ib:   dy = y - ib + 1
                    else:           dy = 0
                    if dx == 0 and dy == 0:
                        continue
                    if dx > 0 and dy > 0:
                        d = int(math.sqrt(dx * dx + dy * dy))
                    else:
                        d = dx if dx > 0 else dy
                    if d > border:
                        continue
                    angle = math.atan2(y - cy, x - cx)
                    hi = int((angle / (2.0 * math.pi) + 0.5) * 256.0) & 255
                    px.append((x, y, d, hi))
            return px

        def _inner(xs, xe, ys, ye, fn):
            px = []
            for y in range(ys, ye):
                for x in range(xs, xe):
                    d = fn(x, y)
                    if d > border:
                        continue
                    angle = math.atan2(y - cy, x - cx)
                    hi = int((angle / (2.0 * math.pi) + 0.5) * 256.0) & 255
                    px.append((x, y, d, hi))
            return px

        _BASE_CACHE = (
            _outer(0, tw, 0, border) +
            _outer(0, tw, th - border, th) +
            _outer(0, border, border, th - border) +
            _outer(tw - border, tw, border, th - border) +
            _inner(il, ir, it, it + inner, lambda x, y: y - it) +
            _inner(il, ir, ib - inner, ib, lambda x, y: ib - 1 - y) +
            _inner(il, il + inner, it + inner, ib - inner, lambda x, y: x - il) +
            _inner(ir - inner, ir, it + inner, ib - inner, lambda x, y: ir - 1 - x)
        )

    buffer = bytearray(tw * th * 4)

    lut_size = border + 1
    alpha_lut = bytearray(lut_size)
    darken_lut = bytearray(lut_size)
    for d in range(lut_size):
        t = d / border_f
        alpha_lut[d] = max(0, min(255, int(255.0 * math.cos(t * math.pi * 0.42) * alpha_multiplier)))
        darken_lut[d] = max(51, int(255.0 * math.cos(t * math.pi * 0.42)))

    color_lut = _COLOR_LUT

    for px, py, pd, phi in _BASE_CACHE:
        a = alpha_lut[pd]
        if a == 0:
            continue
        r0, g0, b0 = color_lut[phi]
        dk = darken_lut[pd]
        r = (r0 * dk) >> 8
        g = (g0 * dk) >> 8
        b = (b0 * dk) >> 8
        idx = (py * tw + px) * 4
        buffer[idx] = b
        buffer[idx + 1] = g
        buffer[idx + 2] = r
        buffer[idx + 3] = a

    return buffer, tw, th
