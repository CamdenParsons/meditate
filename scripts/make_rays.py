#!/usr/bin/env python3
"""Composite a radiant halo around the Buddha.

Build-time, not runtime: writes art/buddha.txt from art/figure.txt, which
the app simply reads. Re-run to retune.

Two things make this read as light rather than noise:

  * everything is computed in *visual* space, where one unit is one
    character height and half a character width, so the halo is round on
    screen instead of a squashed ellipse;
  * strokes are spaced evenly by arc length, not by angle - equal angles
    on an oval bunch up at the ends of the short axis and leave the long
    axis bare.
"""
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIGURE = ROOT / "art" / "figure.txt"
OUT = ROOT / "art" / "buddha.txt"

ASPECT = 2.0
PAD_X, PAD_Y = 14, 6
RAYS = 24
GAP = 1.2
LONG, SHORT = 3.2, 1.8
CLEAR_R, CLEAR_C = 0, 1   # cells kept blank immediately around the figure


def glyph(nx, ny):
    dx = nx * ASPECT
    if abs(dx) < 1e-9:
        return "|"
    s = ny / dx
    a = abs(s)
    if a < 0.35:
        return "-"
    if a < 1.2:
        return "/" if s < 0 else "\\"
    return "|"


def main():
    fig = FIGURE.read_text().rstrip("\n").split("\n")
    fw, fh = max(len(l) for l in fig), len(fig)
    W, H = fw + PAD_X * 2, fh + PAD_Y * 2
    fx, fy = PAD_X, PAD_Y
    cx, cy = fx + fw / 2.0, fy + fh / 2.0

    blocked = set()
    for r, line in enumerate(fig):
        for c, ch in enumerate(line):
            if ch == " ":
                continue
            for dr in range(-CLEAR_R, CLEAR_R + 1):
                for dc in range(-CLEAR_C, CLEAR_C + 1):
                    blocked.add((fy + r + dr, fx + c + dc))

    a = fw / (2 * ASPECT) + 3.5        # visual half-width
    b = fh / 2.0 + 2.0                 # visual half-height

    # even spacing by arc length around the ellipse
    N = 2000
    pts, cum, total = [], [], 0.0
    prev = None
    for i in range(N + 1):
        t = 2 * math.pi * i / N
        p = (a * math.cos(t), b * math.sin(t))
        if prev is not None:
            total += math.hypot(p[0] - prev[0], p[1] - prev[1])
        pts.append((t, p))
        cum.append(total)
        prev = p

    grid = [[" "] * W for _ in range(H)]
    j = 0
    for k in range(RAYS):
        target = total * k / RAYS
        while j < N and cum[j] < target:
            j += 1
        t, (ex, ey) = pts[j]
        nx, ny = math.cos(t) / a, math.sin(t) / b       # outward normal
        n = math.hypot(nx, ny)
        nx, ny = nx / n, ny / n
        g = glyph(nx, ny)
        length = LONG if k % 2 == 0 else SHORT
        d = GAP
        while d < GAP + length:
            x = int(round(cx + (ex + nx * d) * ASPECT))
            y = int(round(cy + ey + ny * d))
            if 0 <= y < H and 0 <= x < W and grid[y][x] == " ":
                grid[y][x] = g
            d += 0.4

    # mirror the right half onto the left so the halo is exactly symmetric
    flip = {"/": "\\", "\\": "/"}
    mid = int(round(cx))
    for y in range(H):
        for x in range(0, mid):          # clear first: a stroke with no
            grid[y][x] = " "             # counterpart across the axis
        for x in range(mid, W):          # would otherwise survive
            mx = 2 * mid - x
            if 0 <= mx < W:
                grid[y][mx] = flip.get(grid[y][x], grid[y][x])

    # the figure is not itself symmetric, so mirroring copies strokes that
    # were blocked on one side only - clear the keep-out zone again
    for (y, x) in blocked:
        if 0 <= y < H and 0 <= x < W:
            grid[y][x] = " "

    for r, line in enumerate(fig):
        for c, ch in enumerate(line):
            if ch != " ":
                grid[fy + r][fx + c] = ch

    text = "\n".join("".join(row).rstrip() for row in grid).strip("\n")
    OUT.write_text(text + "\n")
    lines = text.split("\n")
    print(f"{len(lines)} lines, {max(len(l) for l in lines)} wide\n")
    print(text)


if __name__ == "__main__":
    main()
