"""Check the flat patterns in mechanical/export against Fabworks' rules for 0.048 in 1008 steel.

  python3 mechanical/dfm.py

Reads the DXFs that mk1.py exports; needs matplotlib only because drawings.py does. The figures are
from fabworks.com's material, laser cutting and bending pages, read 2026-11-17.
"""
import math
import os

import drawings
from mk1 import EXPORT, SHEET, T

MIN_FEATURE = 0.51     # smallest hole or slot
MIN_WEB = 1.22         # between cut-outs: one thickness
DISTORTION = 5.11      # a 90 degree bend can distort a feature this close to the bend line: half the die's opening
MIN_FLANGE = 6.81      # 8.4 advised
FLAT_TO_OUTSIDE = 0.93  # from a bend line in the flat to the flange's outside length: T + R less half the bend, 1.27


def points(e, step=0.4):
    if e["type"] == "LINE":
        n = max(1, int(math.hypot(e[11] - e[10], e[21] - e[20]) / step))
        return [(e[10] + (e[11] - e[10]) * i / n, e[20] + (e[21] - e[20]) * i / n) for i in range(n + 1)]
    a0, a1 = (0, 360) if e["type"] == "CIRCLE" else (e[50], e[51] if e[51] > e[50] else e[51] + 360)
    n = max(6, int(math.radians(a1 - a0) * e[40] / step))
    return [(e[10] + e[40] * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             e[20] + e[40] * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


def loops(ents):
    """Group cut entities into closed outlines by their shared end points."""
    parent = list(range(len(ents)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    ends = {}
    for i, e in enumerate(ents):
        if e["type"] == "CIRCLE":
            continue
        p = points(e)
        for q in (p[0], p[-1]):
            k = (round(q[0], 2), round(q[1], 2))
            if k in ends:
                parent[find(i)] = find(ends[k])
            ends[k] = i
    out = {}
    for i, e in enumerate(ents):
        out.setdefault(find(i), []).append(e)
    return [{"pts": [q for e in g for q in points(e)],
             "dia": 2 * g[0][40] if len(g) == 1 and g[0]["type"] == "CIRCLE" else None} for g in out.values()]


def seg_dist(p, a, b):
    d = (b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2
    t = max(0, min(1, ((p[0] - a[0]) * (b[0] - a[0]) + (p[1] - a[1]) * (b[1] - a[1])) / d)) if d else 0
    return math.hypot(p[0] - a[0] - t * (b[0] - a[0]), p[1] - a[1] - t * (b[1] - a[1]))


def describe(l):
    xs, ys = [p[0] for p in l["pts"]], [p[1] for p in l["pts"]]
    at = "at %.1f, %.1f" % ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2)
    if l["dia"]:
        return "hole dia %.2f %s" % (l["dia"], at)
    return "cut-out %.1f x %.1f %s" % (max(xs) - min(xs), max(ys) - min(ys), at)


def main():
    for body in SHEET:
        ents = drawings.entities(os.path.join(EXPORT, body + ".dxf"))
        cuts = loops([e for e in ents if e.get("layer") == "CUT" and e["type"] in ("LINE", "ARC", "CIRCLE")])
        edge = [q for e in ents if e.get("layer") == "OUTLINE" and e["type"] in ("LINE", "ARC", "CIRCLE") for q in points(e)]
        bends = [((e[10], e[20]), (e[11], e[21])) for e in ents if e.get("layer", "").startswith("BEND") and e["type"] == "LINE"]
        for l in cuts:
            xs, ys = [p[0] for p in l["pts"]], [p[1] for p in l["pts"]]
            l["box"] = (min(xs), min(ys), max(xs), max(ys))
        small = min((min(l["box"][2] - l["box"][0], l["box"][3] - l["box"][1]), describe(l)) for l in cuts)
        web = (1e9, "")
        for i, a in enumerate(cuts):
            for b in cuts[i + 1:]:
                if (a["box"][0] - b["box"][2] > 4 or b["box"][0] - a["box"][2] > 4 or a["box"][1] - b["box"][3] > 4
                        or b["box"][1] - a["box"][3] > 4):
                    continue
                d = min(math.hypot(p[0] - q[0], p[1] - q[1]) for p in a["pts"] for q in b["pts"])
                web = min(web, (d, describe(a) + " / " + describe(b)))
        rim = (1e9, "")
        for l in cuts:
            b = l["box"]
            near = [q for q in edge if b[0] - 6 < q[0] < b[2] + 6 and b[1] - 6 < q[1] < b[3] + 6]
            if near:
                rim = min(rim, (min(math.hypot(p[0] - q[0], p[1] - q[1]) for p in l["pts"] for q in near), describe(l)))
        print("%s: %d cut-outs, %d bends" % (body, len(cuts), len(bends)))
        print("  smallest feature %.2f (%s): %s" % (small[0], small[1], "ok" if small[0] >= MIN_FEATURE else "TOO SMALL"))
        for what, (d, where) in (("thinnest web between cut-outs", web), ("nearest cut-out to the outline", rim)):
            if d > 1e8:
                print("  %s: none within 4 to 6" % what)
            else:
                print("  %s %.2f (%s): %s" % (what, d, where, "ok" if d >= MIN_WEB else "TOO THIN"))
        close = []
        for l in cuts:
            d = min((seg_dist(p, a, b) for p in l["pts"] for a, b in bends), default=1e9)
            if d < DISTORTION:
                close.append((d, describe(l)))
        if not bends:
            continue
        print("  cut-outs within %.2f of a bend line: %d" % (DISTORTION, len(close)))
        for d, what in sorted(close):
            print("    %.2f  %s" % (d, what))
        # Each flange, measured all along its bend: from the bend line square out to the first edge on each
        # side, the shorter side being the flange. A lip that steps back part of the way along shows up here.
        # The last 7 at each end are left out: lips are mitred where they meet at a corner and taper there.
        rim_segs = [(q[i], q[i + 1]) for e in ents if e.get("layer") == "OUTLINE" and e["type"] in ("LINE", "ARC", "CIRCLE")
                    for q in [points(e)] for i in range(len(q) - 1)]
        for k, (a, b) in enumerate(bends):
            n = math.hypot(b[0] - a[0], b[1] - a[1])
            ux, uy = (b[0] - a[0]) / n, (b[1] - a[1]) / n
            worst = (1e9, 0)
            for i in range(7, int(n) - 6):
                o = (a[0] + ux * i, a[1] + uy * i)
                reach = []
                for sign in (1, -1):
                    dx, dy = -uy * sign, ux * sign
                    best = 1e9
                    for p, q in rim_segs:
                        ex, ey = q[0] - p[0], q[1] - p[1]
                        den = dx * ey - dy * ex
                        if abs(den) < 1e-12:
                            continue
                        t = ((p[0] - o[0]) * ey - (p[1] - o[1]) * ex) / den
                        v = ((p[0] - o[0]) * dy - (p[1] - o[1]) * dx) / den
                        if t > 1e-6 and -1e-9 <= v <= 1 + 1e-9:
                            best = min(best, t)
                    reach.append(best)
                worst = min(worst, (min(reach) + FLAT_TO_OUTSIDE, i))
            verdict = "ok" if worst[0] >= MIN_FLANGE + 1.6 else "ok, under the advised 8.4" if worst[0] >= MIN_FLANGE else "TOO SHORT"
            print("    bend %d, %.0f long: shortest flange %.2f, %d along: %s" % (k + 1, n, worst[0], worst[1], verdict))


if __name__ == "__main__":
    main()
