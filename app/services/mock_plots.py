"""Gera SVGs fake de scatter plot (medido×previsto e resíduos), sem depender
de matplotlib/numpy. Só pra ter algo visual no protótipo — no app real esses
PNGs vêm do worker (S3, via URL pré-assinada).
"""

import random

WIDTH, HEIGHT = 420, 300
MARGIN = 40
GOOD_COLOR = "#198754"
BAD_COLOR = "#dc3545"


def _scale(value, vmin, vmax, pmin, pmax):
    if vmax == vmin:
        return (pmin + pmax) / 2
    return pmin + (value - vmin) / (vmax - vmin) * (pmax - pmin)


def _generate_points(seed, quality, n=40):
    rng = random.Random(seed)
    noise_scale = (1 - quality) * 35 + 2
    points = []
    for _ in range(n):
        measured = rng.uniform(0, 100)
        predicted = measured + rng.gauss(0, noise_scale) + (1 - quality) * rng.uniform(-10, 10)
        points.append((measured, predicted))
    return points


def measured_predicted_svg(seed, quality):
    points = _generate_points(seed, quality)
    color = GOOD_COLOR if quality >= 0.6 else BAD_COLOR
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    vmin, vmax = min(xs + ys) - 5, max(xs + ys) + 5

    def px(v):
        return _scale(v, vmin, vmax, MARGIN, WIDTH - 20)

    def py(v):
        return _scale(v, vmin, vmax, HEIGHT - MARGIN, 20)

    circles = "".join(
        f'<circle cx="{px(x):.1f}" cy="{py(y):.1f}" r="3.5" fill="{color}" fill-opacity="0.65" />'
        for x, y in points
    )
    ref_line = (
        f'<line x1="{px(vmin):.1f}" y1="{py(vmin):.1f}" x2="{px(vmax):.1f}" y2="{py(vmax):.1f}" '
        f'stroke="#adb5bd" stroke-width="1.5" stroke-dasharray="6,4" />'
    )

    n = len(points)
    mean_x, mean_y = sum(xs) / n, sum(ys) / n
    denom = sum((x - mean_x) ** 2 for x in xs) or 1
    slope = sum((x - mean_x) * (y - mean_y) for x, y in points) / denom
    intercept = mean_y - slope * mean_x
    trend_line = (
        f'<line x1="{px(vmin):.1f}" y1="{py(slope * vmin + intercept):.1f}" '
        f'x2="{px(vmax):.1f}" y2="{py(slope * vmax + intercept):.1f}" '
        f'stroke="{color}" stroke-width="2.5" />'
    )

    return f"""<svg viewBox="0 0 {WIDTH} {HEIGHT}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="measured vs predicted">
  <rect width="{WIDTH}" height="{HEIGHT}" fill="#ffffff" />
  {ref_line}
  {circles}
  {trend_line}
  <text x="{MARGIN}" y="{HEIGHT - 10}" font-size="11" fill="#6c757d">medido</text>
  <text x="8" y="20" font-size="11" fill="#6c757d">previsto</text>
</svg>"""


def residuals_svg(seed, quality):
    points = _generate_points(seed + 1, quality)
    residuals = [(m, p - m) for m, p in points]
    color = GOOD_COLOR if quality >= 0.6 else BAD_COLOR
    xs = [r[0] for r in residuals]
    ys = [r[1] for r in residuals]
    vmax_y = max(abs(min(ys)), abs(max(ys)), 5) * 1.2

    def px(v):
        return _scale(v, min(xs) - 5, max(xs) + 5, MARGIN, WIDTH - 20)

    def py(v):
        return _scale(v, -vmax_y, vmax_y, HEIGHT - MARGIN, 20)

    circles = "".join(
        f'<circle cx="{px(x):.1f}" cy="{py(y):.1f}" r="3.5" fill="{color}" fill-opacity="0.65" />'
        for x, y in residuals
    )
    zero_line = (
        f'<line x1="{MARGIN}" y1="{py(0):.1f}" x2="{WIDTH - 20}" y2="{py(0):.1f}" '
        f'stroke="#adb5bd" stroke-width="1.5" stroke-dasharray="6,4" />'
    )

    return f"""<svg viewBox="0 0 {WIDTH} {HEIGHT}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="residuals">
  <rect width="{WIDTH}" height="{HEIGHT}" fill="#ffffff" />
  {zero_line}
  {circles}
  <text x="{MARGIN}" y="{HEIGHT - 10}" font-size="11" fill="#6c757d">medido</text>
  <text x="8" y="20" font-size="11" fill="#6c757d">resíduo</text>
</svg>"""
