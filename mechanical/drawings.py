"""Draw the Reactor's manufacturing drawings as one PDF, mechanical/export/reactor-drawings.pdf.

  python3 mechanical/drawings.py
  python3 mechanical/drawings.py --foot    the foot's sheet alone, as foot-drawing.pdf, for whoever prints it

Run reactor.py first: the drawings are made from the saved sheet metal design, its flat pattern DXFs and
its bend tables. Views of the formed parts come from the running SolidCraft, so SOLIDCRAFT_MCP is
needed as for reactor.py. Needs matplotlib.
"""
import csv
import datetime
import math
import os
import shutil
import sys
import time

import matplotlib
matplotlib.use("pdf")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.collections import LineCollection
from matplotlib.patches import Arc, Circle, Polygon

import reactor
from reactor import (BULKHEAD_JOINS, DESIGN, EXPORT, FOOT_CROSS, FOOT_CROSS_DEPTH, FOOT_RECESS, FOOT_RECESS_DEPTH, FOOT_TAP, LX, LY, LZ, PANELS, SHEET, PSU_TOP, T, TONGUES,
                 TRAY_JOINS)

VIEWS = os.path.expanduser("~/.cache/reactor/drawings")
PDF = os.path.join(EXPORT, "reactor-drawings.pdf")
W, H = 420.0, 297.0   # A3 landscape
REV = "A"
INK, THIN, BLUE, RED = "#111111", "#555555", "#1f4e9c", "#b3261e"

NUMBER = {"core": "R-01", "top": "R-02", "tray": "R-03", "bulkhead": "R-04", "shelf": "R-05", "front": "R-06", "side": "R-07"}
TITLE = {"core": "Core: bottom and rear", "top": "Top panel", "tray": "Mainboard tray", "bulkhead": "Front bulkhead",
         "shelf": "Power supply shelf", "front": "Front panel", "side": "Side panel"}
QTY = {"side": 2}
# what each round hole is for, by part and diameter
HOLES = {
    ("core", 5.0): "fan screw, self-tapping, clearance",
    ("core", 4.5): "6-32, loose clearance: the rear handle's two screws, through the top lip's tabs",
    ("top", 5.0): "fan screw, self-tapping, clearance",
    ("top", 4.5): "6-32, loose clearance: shelf screws (2) and handle screws (4)",
    ("top", 2.5): "rivet, 3/32 in; countersunk by the customer",
    ("core", 3.5): "+0.08/0: PEM FH-632-6 stud, bottom panel (4); mains inlet M3, rear panel (2)",
    ("core", 2.5): "rivet, 3/32 in; countersunk by the customer",
    ("core", 4.76): "PEM S-632-1 nut for a side panel screw, +0.08/0, two in each side lip of the rear panel",
    ("front", 4.76): "PEM S-632-1 nut for a side panel screw, +0.08/0, two in each flange",
    ("tray", 2.5): "rivet, 3/32 in",
    ("tray", 5.41): "PEM BSO-632-12 standoff, +0.08/0",
    ("bulkhead", 12.0): "power switch, +0.2/0",
    ("bulkhead", 8.0): "LED holder, +0.2/0",
    ("bulkhead", 4.5): "6-32, loose clearance: the front handle's two screws, through the top lip's tabs",
    ("bulkhead", 2.5): "rivet, 3/32 in",
    ("shelf", 4.0): "6-32 clearance, supply: SFX pattern both ways round",
    ("shelf", 4.76): "PEM S-632-1 nut, +0.08/0",
    ("front", 14.5): "power switch head, 14",
    ("front", 11.3): "LED holder's bezel, 10.8",
    ("side", 4.5): "side panel screw 6-32, loose clearance",
}
PART_NOTES = {
    "core": ["Hexagonal mesh: 9.6 across flats, webs 2.07; see DXF.",
             "Rear panel: I/O aperture 158.75 x 44.45 +/-0.2 to ATX 2.2 fig. 4; keep paint off both faces within 2.5 of it.",
             "Mains inlet cut-out 28 x 20 +0.2/0, R1, for Schurter 6100-3 mounted from outside.",
             "Four PEM S-632-1 nuts, two in each side lip of the rear panel, flush on the outside, bodies inside.",
             "The rear panel's top lip lies under the top panel (R-02): 16.5 at the two corners, where the rear handle's screws go through both, and 9.5 between.",
             "The bottom panel's side lips stop 15.3 short of the front, behind the front panel's flanges (R-06).",
             "Four PEM FH-632-6 studs in the bottom panel for the feet, heads flush in its upper (inside) face, pointing down."],
    "top": ["Hexagonal mesh: 9.6 across flats, webs 2.07; see DXF.",
            "Four 4.5 holes at the corners take the screws of two handles, fitted by the customer. They also go through the core's top lip and the bulkhead's.",
            "The front lip is cut back at both ends, round the switch and the two lamps in the bulkhead behind it, and is riveted to the bulkhead; the lip on the tray's side, 17, is riveted to the tray.",
            "The side lips start 17.3 from the rear edge, in front of the rear panel's side lips, and stop 15.3 short of the front, behind the front panel's flanges. The front lip's ends stand 2.5 inside the panel's edges."],
    "tray": ["Flat. Four PEM BSO-632-12 standoffs pressed in from the face that goes against the core's lips, standing 9.53 off the other face.",
             "The standoffs go in before the customer rivets the tray on: two heads end up under the core's lips.",
             "Eight slots 2.0 x 5.0 in four pairs, for cable ties.",
             "The two notches in the rear edge and the two in the front edge go round the bodies of the nuts in the core's lip and the front panel's flange."],
    "bulkhead": ["No hardware.", "Three slots 13.0 x 2.2, corners R0.5, for the shelf's tongues: keep their lower edges clean and square.",
                 "The top lip lies under the top panel (R-02): 16.5 at the two corners, where the front handle's screws go through both, and 9.5 between."],
    "shelf": ["Two PEM S-632-1 nuts in the tabs, bodies under the tabs, flush on top. The tabs fold toward the rear, away from the supply.",
              "Three tongues 12.0 wide on the front edge, standing 2.4 beyond it, go through the bulkhead's slots: no burr on them.",
              "Supplied loose: its tongues sit in the bulkhead's slots and two screws through the top panel hold it.",
              "The notch in the tray-side edge of the rear wall, 13.0 deep and 17.0 tall, corners R3, is for the mains lead and the switch and lamp wires: no burr, it is lined with edge trim."],
    "front": ["Plain outside face: no marks, grain or tooling witness on the front.",
              "The two flanges, 15, go inside the side panels (R-07), which screw to them and are all that holds this panel.",
              "The switch's head and the lamps' bezels, fixed in the bulkhead behind, come through the three holes.",
              "Four PEM S-632-1 nuts, two in each flange, flush on the outside, bodies inside."],
    "side": ["Plain outside face: no marks, grain or tooling witness.",
             "The two return flanges are plain.",
             "Two off, the same part on both sides, turned end for end. Four screws hold each: two into the rear panel's lip (R-01) and two into the front panel's flange (R-06)."],
}
GENERAL = [
    "All dimensions in mm. The STEP model and the DXF flat patterns govern; do not scale this drawing.",
    "Material: cold rolled low carbon steel, 1008 or equivalent, 0.048 in (1.2) thick.",
    "Inside bend radius 1.32 (0.052 in) and K = 0.45, OSH Cut's figures for this sheet. The STEP models are the formed sizes to hold.",
    "Tolerances unless stated: cut features +/-0.15, bend positions +/-0.4, angles +/-1 deg.",
    "Deburr all edges and break sharp corners. Outside corners are R1.5 where drawn.",
    "Self-clinching hardware: PennEngineering (PEM), installed by the fabricator: eighteen pieces, listed below.",
    "All eight pieces, of seven parts, are supplied loose. The customer rivets the tray and bulkhead to the core and the top panel (sheet 2).",
    "Finish: as ordered. If powder coated, keep threads, studs and standoff bores free of powder.",
]


def entities(path):
    """LINE, ARC, CIRCLE, LWPOLYLINE and TEXT entities of a DXF, as dicts with their layer."""
    with open(path) as f:
        rows = [l.rstrip("\n") for l in f]
    pairs = [(int(rows[i].strip()), rows[i + 1].strip()) for i in range(0, len(rows) - 1, 2)]
    out, cur, on = [], None, False
    for code, val in pairs:
        if code == 2 and val == "ENTITIES":
            on = True
        elif code == 0:
            if cur:
                out.append(cur)
            cur = {"type": val, "pts": []} if on and val in ("LINE", "ARC", "CIRCLE", "LWPOLYLINE", "TEXT") else None
            if val == "ENDSEC":
                on = False
        elif cur is not None:
            if code == 8:
                cur["layer"] = val
            elif code == 1:
                cur["text"] = val
            elif code in (10, 20, 11, 21, 40, 50, 51, 70):
                if cur["type"] == "LWPOLYLINE" and code in (10, 20):
                    if code == 10:
                        cur["pts"].append([float(val), 0.0])
                    else:
                        cur["pts"][-1][1] = float(val)
                else:
                    cur[code] = float(val)
    return out


class Sheet:
    def __init__(self, pdf, number, title, material, scale, n, total):
        self.pdf = pdf
        self.fig = plt.figure(figsize=(W / 25.4, H / 25.4))
        self.ax = self.fig.add_axes([0, 0, 1, 1])
        self.ax.set_xlim(0, W)
        self.ax.set_ylim(0, H)
        self.ax.axis("off")
        self.box(8, 8, W - 8, H - 8, 0.7)
        x0, y0 = W - 8 - 190, 8
        self.box(x0, y0, W - 8, y0 + 30, 0.7)
        for x in (x0 + 95, x0 + 150):
            self.line([(x, y0), (x, y0 + 30)], 0.35)
        self.line([(x0, y0 + 15), (W - 8, y0 + 15)], 0.35)
        cells = [(x0 + 2, y0 + 26, "TITLE", "Reactor  -  " + title), (x0 + 2, y0 + 11, "MATERIAL", material),
                 (x0 + 97, y0 + 26, "DRAWING NO.", number), (x0 + 97, y0 + 11, "SCALE (A3)", scale),
                 (x0 + 152, y0 + 26, "SHEET / REV", "%d of %d   rev %s" % (n, total, REV)),
                 (x0 + 152, y0 + 11, "DATE", datetime.date.today().isoformat())]
        for x, y, k, v in cells:
            self.text(x, y, k, 4.5, THIN)
            self.text(x, y - 6.5, v, 8 if k == "TITLE" else 7.5, INK, weight="bold" if k in ("TITLE", "DRAWING NO.") else "normal")
        self.text(10, 10.5, "Justin Ward  -  github.com/OptimoSupreme/reactor  -  CERN-OHL-S v2  -  third angle projection, mm", 5, THIN)

    def line(self, pts, lw=0.35, color=INK, ls="-"):
        self.ax.plot([p[0] for p in pts], [p[1] for p in pts], color=color, lw=lw, ls=ls, solid_capstyle="round")

    def box(self, x0, y0, x1, y1, lw=0.35):
        self.line([(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)], lw)

    def text(self, x, y, s, size=6, color=INK, ha="left", va="baseline", weight="normal", rot=0):
        self.ax.text(x, y, s, fontsize=size, color=color, ha=ha, va=va, fontweight=weight, rotation=rot,
                     family="DejaVu Sans")

    def notes(self, x, y, title, lines, size=5.6, width=118):
        self.text(x, y, title, 6.5, INK, weight="bold")
        y -= 5
        for i, l in enumerate(lines):
            words, row = l.split(" "), "%d. " % (i + 1)
            for w in words:
                if len(row) + len(w) > width:
                    self.text(x, y, row, size)
                    y -= 3.6
                    row = "    "
                row += w + " "
            self.text(x, y, row, size)
            y -= 4.2
        return y

    def table(self, x, y, title, head, rows, widths, size=5.6):
        self.text(x, y, title, 6.5, INK, weight="bold")
        y -= 5.5
        for r, row in enumerate([head] + rows):
            cx = x
            for c, cell in enumerate(row):
                self.text(cx, y, str(cell), size, THIN if r == 0 else INK)
                cx += widths[c]
            if r == 0:
                self.line([(x, y - 1.3), (x + sum(widths), y - 1.3)], 0.25, THIN)
            y -= 4.3
        return y

    def geometry(self, ents, place, layers=None, lw=0.3, color=INK, ls="-"):
        """Draw DXF entities; place(x, y) maps drawing mm to page mm and place.k is its scale."""
        segs = []
        for e in ents:
            if layers and e.get("layer") not in layers:
                continue
            if e["type"] == "LINE":
                segs.append([place(e[10], e[20]), place(e[11], e[21])])
            elif e["type"] == "LWPOLYLINE":
                p = [place(*q) for q in e["pts"]]
                if int(e.get(70, 0)) & 1:
                    p.append(p[0])
                segs += [[p[i], p[i + 1]] for i in range(len(p) - 1)]
            elif e["type"] == "CIRCLE":
                self.ax.add_patch(Circle(place(e[10], e[20]), e[40] * place.k, fill=False, lw=lw, ec=color, ls=ls))
            elif e["type"] == "ARC":
                a0, a1 = (e[50], e[51]) if not place.flip else (180 - e[51], 180 - e[50])
                self.ax.add_patch(Arc(place(e[10], e[20]), 2 * e[40] * place.k, 2 * e[40] * place.k, theta1=a0,
                                      theta2=a1, lw=lw, ec=color, ls=ls))
        self.ax.add_collection(LineCollection(segs, colors=color, linewidths=lw, linestyles=ls, capstyle="round"))

    def dim(self, a, b, off, label, vertical=False):
        """A dimension between page points a and b, its line `off` away from them."""
        if vertical:
            x = a[0] + off
            self.line([(a[0], a[1]), (x + math.copysign(1.5, off), a[1])], 0.2, BLUE)
            self.line([(b[0], b[1]), (x + math.copysign(1.5, off), b[1])], 0.2, BLUE)
            self.ax.annotate("", (x, a[1]), (x, b[1]), arrowprops=dict(arrowstyle="<|-|>", lw=0.3, color=BLUE, shrinkA=0, shrinkB=0, mutation_scale=5))
            self.text(x - 1.2, (a[1] + b[1]) / 2, label, 6, BLUE, ha="center", va="center", rot=90)
        else:
            y = a[1] + off
            self.line([(a[0], a[1]), (a[0], y + math.copysign(1.5, off))], 0.2, BLUE)
            self.line([(b[0], b[1]), (b[0], y + math.copysign(1.5, off))], 0.2, BLUE)
            self.ax.annotate("", (a[0], y), (b[0], y), arrowprops=dict(arrowstyle="<|-|>", lw=0.3, color=BLUE, shrinkA=0, shrinkB=0, mutation_scale=5))
            self.text((a[0] + b[0]) / 2, y + 1.2, label, 6, BLUE, ha="center")

    def leader(self, tip, at, lines, color=BLUE):
        """A note at page point `at` with an arrow to `tip`."""
        self.ax.annotate("", tip, at, arrowprops=dict(arrowstyle="-|>", lw=0.3, color=color, shrinkA=0, shrinkB=0, mutation_scale=5))
        for i, l in enumerate(lines):
            self.text(at[0] + 1, at[1] - 1 - 3.6 * i, l, 5.6, color)

    def done(self):
        self.pdf.savefig(self.fig)
        plt.close(self.fig)


def bbox(ents, layers=None):
    xs, ys = [], []
    for e in ents:
        if layers and e.get("layer") not in layers:
            continue
        if e["type"] == "LINE":
            xs += [e[10], e[11]]
            ys += [e[20], e[21]]
        elif e["type"] == "LWPOLYLINE":
            xs += [p[0] for p in e["pts"]]
            ys += [p[1] for p in e["pts"]]
        elif e["type"] == "CIRCLE":
            xs += [e[10] - e[40], e[10] + e[40]]
            ys += [e[20] - e[40], e[20] + e[40]]
        elif e["type"] == "ARC":
            sweep = (e[51] - e[50]) % 360
            for i in range(13):
                t = math.radians(e[50] + sweep * i / 12)
                xs.append(e[10] + e[40] * math.cos(t))
                ys.append(e[20] + e[40] * math.sin(t))
    return min(xs), min(ys), max(xs), max(ys)


def placer(box, area, scale=None, flip=False):
    """Map drawing coordinates in `box` to the middle of the page rectangle `area`, at a neat scale."""
    x0, y0, x1, y1 = box
    ax0, ay0, ax1, ay1 = area
    if scale is None:
        fit = min((ax1 - ax0) / (x1 - x0), (ay1 - ay0) / (y1 - y0))
        scale = max(s for s in (1, 1 / 1.5, 0.5, 0.4, 1 / 3, 0.25, 0.2, 1 / 6, 0.125, 0.1) if s <= fit)
    cx, cy = (ax0 + ax1) / 2, (ay0 + ay1) / 2
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    sx = -scale if flip else scale
    f = lambda x, y: (cx + (x - mx) * sx, cy + (y - my) * scale)
    f.k, f.flip = scale, flip
    return f


def ratio(k):
    return "1 : %g" % round(1 / k, 2)


def view(sc, name, yaw, pitch, target, show=None):
    """A line drawing of the design from a far camera, which is as good as parallel projection."""
    path = os.path.join(VIEWS, name + ".dxf")
    if show is not None:
        sc.call("execute", {"command": "browser.visibility", "params": {"visible": False, "items": [b for b in PANELS if b not in show]}})
    sc.call("execute", {"command": "file.export_view_dxf", "params": {
        "camera": {"target": target, "yaw": yaw, "pitch": pitch, "distance": 200000, "fov": 0.005},
        "path": path, "curves": "arcs", "tolerance": 0.05}})
    if show is not None:
        sc.call("execute", {"command": "browser.visibility", "params": {"visible": True, "items": PANELS}})
    return entities(path)


def part_sheet(pdf, sc, body, sizes, n, total):
    flat = entities(os.path.join(EXPORT, body + ".dxf"))
    with open(os.path.join(EXPORT, body + "-bends.csv")) as f:
        bends = list(csv.DictReader(f))
    box = bbox(flat, ("OUTLINE",))
    place = placer(box, (22, 62, 268, 276))
    s = Sheet(pdf, NUMBER[body], TITLE[body], "steel 1008, 0.048 in", "flat " + ratio(place.k), n, total)
    s.text(14, 284, "FLAT PATTERN  (bend lines dash-dot, numbered as in %s-bends.csv)" % body, 6.5, weight="bold")
    s.geometry(flat, place, ("OUTLINE",), 0.45)
    s.geometry(flat, place, ("CUT",), 0.25)
    s.geometry(flat, place, ("BEND_UP", "BEND_DOWN"), 0.3, RED, "-.")
    a, b = place(box[0], box[1]), place(box[2], box[3])
    s.dim((a[0], a[1]), (b[0], a[1]), -9, "%.1f" % (box[2] - box[0]))
    s.dim((a[0], a[1]), (a[0], b[1]), -9, "%.1f" % (box[3] - box[1]), vertical=True)
    for r in bends:
        mx = (float(r["start_x_mm"]) + float(r["end_x_mm"])) / 2 + box[0] * 0
        my = (float(r["start_y_mm"]) + float(r["end_y_mm"])) / 2
        p = place(mx + box[0], my + box[1])
        s.text(p[0] + 1, p[1] + 1, "B" + r["bend"], 5.5, RED, weight="bold")
    # letter every round hole
    dias = sorted({round(2 * e[40], 2) for e in flat if e["type"] == "CIRCLE" and e.get("layer") == "CUT"}, reverse=True)
    letter = {d: chr(65 + i) for i, d in enumerate(dias)}
    for e in flat:
        if e["type"] == "CIRCLE" and e.get("layer") == "CUT":
            p = place(e[10], e[20])
            s.text(p[0] + e[40] * place.k + 0.6, p[1] + 0.6, letter[round(2 * e[40], 2)], 4.6, BLUE, weight="bold")
    # formed view
    x0 = 282
    s.text(x0, 284, "FORMED  (not to scale)", 6.5, weight="bold")
    formed = view(sc, "formed-" + body, -0.65, 0.5, [LX / 2, LY / 2, LZ / 2], show=[body])
    s.geometry(formed, placer(bbox(formed), (x0, 196, 408, 280)), None, 0.2)
    lo, hi = sizes[body]
    y = s.table(x0, 188, "PART", ["", ""], [
        ["Formed size", "%.1f x %.1f x %.1f" % tuple(hi[i] - lo[i] for i in range(3))],
        ["Flat size", "%.1f x %.1f" % (box[2] - box[0], box[3] - box[1])],
        ["Bends", "%d, all 90 deg, inside R%.2f" % (len(bends), reactor.BEND_R) if bends else "none"],
        ["Mass", "%.0f g" % sizes[body + "-g"]]], [26, 90])
    count = lambda d: sum(1 for e in flat if e["type"] == "CIRCLE" and e.get("layer") == "CUT" and round(2 * e[40], 2) == d)
    y = s.table(x0, y - 3, "ROUND HOLES", ["", "dia", "qty", "for"], [
        [letter[d], "%g" % d, count(d), HOLES.get((body, d), "")] for d in dias], [7, 12, 9, 90], size=5.2)
    if bends:
        rows = [["B" + r["bend"], "%g" % float(r["angle_deg"]), r["direction"], "%.1f" % float(r["length_mm"])] for r in bends]
        s.table(x0, y - 3, "BENDS", ["", "angle", "dir.", "length"], rows[:12], [10, 14, 14, 20], size=5.2)
    s.notes(14, 52, "NOTES", PART_NOTES[body] + ["General notes on sheet 1 apply."], width=150)
    s.done()


FOOT_PDF = os.path.join(EXPORT, "foot-drawing.pdf")
FOOT_THREAD = 10.0   # full thread asked for: the stud stands 9.5 at most


def foot_sheet(pdf, n, total):
    """The foot in section as it stands under the case, with a view on each end."""
    k = 5.0
    s = Sheet(pdf, "R-08", "Foot", "316L stainless steel, SLM / DMLS", "5 : 1, views 3 : 1", n, total)
    cx, top = 92.0, 222.0
    at = lambda r, z: (cx + r * k, top - z * k)
    r = FOOT_TAP / 2
    rr, rd = FOOT_RECESS / 2, FOOT_RECESS_DEPTH
    (sw, sl), sd = FOOT_CROSS, FOOT_CROSS_DEPTH
    floor = 18 - rd - sd
    half = [(r, 0), (10, 0), (10, 2), (8.5, 2), (6, 18), (rr, 18), (rr, 18 - rd), (sl / 2, 18 - rd), (sl / 2, floor),
            (r, floor)]
    for sign in (-1, 1):
        cut = [at(sign * x, z) for x, z in half]
        s.ax.add_patch(Polygon(cut, closed=True, fill=False, hatch="////", ec=THIN, lw=0))
        s.line(cut + [cut[0]], 0.5)
        s.line([at(sign * 1.753, 0), at(sign * 1.753, FOOT_THREAD)], 0.2)   # the thread's major diameter
    s.line([at(-r, 0), at(r, 0)], 0.2)
    s.line([at(-1.753, FOOT_THREAD), at(1.753, FOOT_THREAD)], 0.2)
    for sign in (-1, 1):    # the other slot's walls, seen beyond
        s.line([at(sign * sw / 2, floor), at(sign * sw / 2, 18 - rd)], 0.25)
    s.line([at(0, -3), at(0, 21)], 0.2, THIN, "-.")
    s.text(cx - 50, top + 20, "SECTION A-A   5 : 1", 6.5, weight="bold")
    s.text(cx - 50, top + 15.5, "as it stands under the case: flange up, against the bottom panel", 5.6, THIN)
    s.dim(at(-10, 0), at(10, 0), 8, "dia 20.0")
    s.dim(at(-6, 18), at(6, 18), -8, "dia 12.0")
    s.dim(at(-rr, 18), at(rr, 18), -17, "recess dia %.1f x %.1f deep" % (FOOT_RECESS, rd))
    s.dim(at(10, 0), at(10, 2), 10, "2.0", vertical=True)
    s.dim(at(10, 0), at(6, 18), 20, "18.0", vertical=True)
    s.dim(at(-10, 0), at(-1.753, FOOT_THREAD), -10, "%.1f min full thread" % FOOT_THREAD, vertical=True)
    s.dim(at(-sl / 2, 18 - rd), at(-sl / 2, floor), -34, "%.1f" % sd, vertical=True)
    note = cx + 10 * k + 26
    s.leader(at(8.2, 4), (note, top - 14), ["dia 17.0 under the flange,", "tapering to 12.0"])
    s.leader(at(1.753, 6), (note, top - 40), ["6-32 UNC-2B, tapped", "after printing: full thread",
                                              "%.0f deep or more. Hole dia" % FOOT_THREAD,
                                              "%.1f, right through, in the" % FOOT_TAP, "model"], RED)
    s.leader(at(sl / 2 - 0.6, floor + 1.2), (note, top - 78), ["cross slot, as printed,", "for a PH2 screwdriver"])

    k2 = 3.0
    for cy, name, below in ((222.0, "VIEW ON THE FLANGE   3 : 1", False), (118.0, "VIEW FROM BELOW   3 : 1", True)):
        px = 244.0
        s.ax.add_patch(Circle((px, cy), 10 * k2, fill=False, lw=0.5, ec=INK))
        s.line([(px - 11.5 * k2, cy), (px + 11.5 * k2, cy)], 0.2, THIN, "-.")
        s.line([(px, cy - 11.5 * k2), (px, cy + 11.5 * k2)], 0.2, THIN, "-.")
        s.text(px - 10 * k2, cy + 12.5 * k2, name, 6.5, weight="bold")
        s.ax.add_patch(Circle((px, cy), r * k2, fill=False, lw=0.5, ec=INK))
        if not below:
            s.ax.add_patch(Arc((px, cy), 3.505 * k2, 3.505 * k2, theta1=100, theta2=10, lw=0.2, ec=INK))
            for sign in (-1, 1):
                s.line([(px + sign * 11.5 * k2, cy), (px + sign * 11.5 * k2, cy + 4)], 0.5)
                s.text(px + sign * 11.5 * k2, cy + 5, "A", 7, ha="center", weight="bold")
            s.leader((px + 1.24 * k2, cy - 1.24 * k2), (px + 8, cy - 14), ["6-32 UNC-2B"], RED)
        else:
            for rad in (8.5, 6.0, rr):
                s.ax.add_patch(Circle((px, cy), rad * k2, fill=False, lw=0.35, ec=INK))
            a, b = sl / 2, sw / 2
            cross = [(a, b), (b, b), (b, a), (-b, a), (-b, b), (-a, b), (-a, -b), (-b, -b), (-b, -a), (b, -a), (b, -b),
                     (a, -b), (a, b)]
            s.line([(px + x * k2, cy + y * k2) for x, y in cross], 0.5)
            s.leader((px - a * k2 + 1, cy - b * k2), (px - 34, cy - 36), ["cross slot: two slots", "%.1f wide x %.1f long," % (sw, sl), "%.1f deep" % sd])
            s.leader((px + rr * k2 * 0.7, cy - rr * k2 * 0.7), (px + 6, cy - 36), ["recess dia %.1f for" % FOOT_RECESS, "a stick-on pad"])

    s.table(288, 284, "PART", ["", ""], [["Quantity", "4"], ["Model", "foot.step  (one body, mm)"],
                                         ["Material", "316L stainless steel, laser powder bed fusion"],
                                         ["Finish", "blasted matte all over, as ordered"],
                                         ["Mass", "about 25 g each"]], [22, 100])
    s.notes(288, 248, "THREAD  (the one operation after printing)", [
        "Tap one 6-32 UNC-2B thread in each foot, on its axis, from the flange's flat face.",
        "Full thread to %.0f deep or more. The hole goes right through into the cross slot, so the tap can run through: no bottoming tap is needed." % FOOT_THREAD,
        "foot.step has the hole at %.1f, the tap drill size, with no thread modelled. Drill it out before tapping if it prints small; any drill from 2.7 to 2.9 will do." % FOOT_TAP,
        "Thread square to the flange's face within 0.5 deg: the foot is screwed down onto a stud until that face seats.",
        "Check: a 6-32 screw turns in by hand to %.0f deep." % FOOT_THREAD], width=84)
    s.notes(288, 186, "NOTES", [
        "All dimensions in mm. The STEP model governs; this drawing adds the thread and the notes.",
        "Tolerance +/-0.3 unless stated.",
        "The flange's flat face sits against the case: flat within 0.2, with no support marks left standing on it.",
        "The cross slot in the recess's floor is as printed: the foot is turned tight with a PH2 (No. 2 Phillips) screwdriver, whose point goes into the hole and whose wings sit in the slots. Slots %.1f wide or more." % (sw - 0.3),
        "The recess underneath takes a stick-on pad 8.0 across, which the customer fits.",
        "Each foot turns onto a 6-32 stud that stands 9.5 out of the case's bottom panel.",
        "Remove loose powder from the hole, the slots and the recess. Break sharp edges."], width=84)
    s.done()


def foot_only():
    with PdfPages(FOOT_PDF) as pdf:
        foot_sheet(pdf, 1, 1)
    print("wrote", FOOT_PDF)


def main():
    if "--foot" in sys.argv:
        return foot_only()
    sc = reactor.Bridge()
    os.makedirs(VIEWS, exist_ok=True)
    # a copy under a new name: opening DESIGN itself can land on a tab still showing an earlier build
    fresh = os.path.join(VIEWS, "sheet-%d.sc" % time.time())
    shutil.copy(DESIGN, fresh)
    sc.call("open", {"path": fresh})
    m = sc.call("measure", {"summary": True})
    sizes = {}
    for b in m["bodies"]:
        if b["name"] in PANELS:
            sizes[b["name"]] = (b["bbox"]["min"], b["bbox"]["max"])
            sizes[b["name"] + "-g"] = b["volume_mm3"] * 7.85e-3
    lo = [min(sizes[b][0][i] for b in PANELS) for i in range(3)]
    hi = [max(sizes[b][1][i] for b in PANELS) for i in range(3)]
    mid = [(lo[i] + hi[i]) / 2 for i in range(3)]
    total = 3 + len(SHEET)
    with PdfPages(PDF) as pdf:
        # sheet 1: general arrangement
        k = 0.4
        s = Sheet(pdf, "R-00", "General arrangement", "see parts", ratio(k), 1, total)
        side = view(sc, "ga-side", 0, 0, mid)
        front = view(sc, "ga-front", -math.pi / 2, 0, mid)
        top = view(sc, "ga-top", 0, math.pi / 2 - 1e-4, mid)
        dx, dy, dz = [(hi[i] - lo[i]) for i in range(3)]
        ps = placer((-dx / 2, -dz / 2, dx / 2, dz / 2), (30, 150, 30 + dx * k, 150 + dz * k), k)
        pf = placer((-dy / 2, -dz / 2, dy / 2, dz / 2), (160, 150, 160 + dy * k, 150 + dz * k), k)
        pt = placer((-dx / 2, -dy / 2, dx / 2, dy / 2), (30, 70, 30 + dx * k, 70 + dy * k), k)
        for ents, p in ((side, ps), (front, pf), (top, pt)):
            s.geometry(ents, p, None, 0.22)
        s.text(30, 242, "SIDE (open side; rear at left)", 6, weight="bold")
        s.text(160, 242, "FRONT", 6, weight="bold")
        s.text(30, 128, "TOP (from above; rear at left)", 6, weight="bold")
        s.dim(ps(-dx / 2, -dz / 2), ps(dx / 2, -dz / 2), -8, "%.1f" % dx)
        s.dim(ps(-dx / 2, -dz / 2), ps(-dx / 2, dz / 2), -8, "%.1f" % dz, vertical=True)
        s.dim(pf(-dy / 2, -dz / 2), pf(dy / 2, -dz / 2), -8, "%.1f" % dy)
        s.notes(232, 284, "GENERAL NOTES", GENERAL, width=120)
        rows = [[NUMBER[b], TITLE[b], QTY.get(b, 1), "%.0f g" % sizes[b + "-g"], b + ".step, " + b + ".dxf"] for b in SHEET]
        y = s.table(232, 196, "PARTS  (all 0.048 in / 1.2 mm cold rolled steel)", ["no.", "part", "qty", "mass", "files"], rows, [18, 62, 9, 16, 60])
        hw = [["PEM BSO-632-12", "blind standoff, 6-32, 9.53 long", 4, "tray"],
              ["PEM FH-632-6", "flush-head stud, 6-32, 9.53 long", 4, "core, bottom panel"],
              ["PEM S-632-1", "self-clinching nut, 6-32", 10, "shelf 2, core 4, front panel 4"]]
        s.table(232, y - 4, "HARDWARE BY THE FABRICATOR  (PEM, zinc plated steel)", ["item", "", "qty", "where"], hw, [30, 62, 9, 40])
        s.notes(30, 52, "SCOPE", ["Seven sheet metal parts, cut, bent and with their PEM hardware pressed in, all supplied loose.",
                                  "The customer rivets the core, top panel, tray and bulkhead together (sheet 2: %d rivets MS20426AD3-4)." % (len(TRAY_JOINS) + len(BULKHEAD_JOINS)),
                                  "Fans, mainboard, power supply, mains inlet, switch, handles, screws and feet are fitted by the customer. "
                                  "The feet (sheet %d) are made separately." % total], width=135)
        s.done()

        # sheet 2: joined assembly
        k = 0.45
        s = Sheet(pdf, "R-10", "Riveted assembly: core, top, tray, bulkhead", "R-01 to R-04", ratio(k), 2, total)
        show = ["core", "top", "tray", "bulkhead"]
        tray_side = view(sc, "weld-tray", math.pi, 0, mid, show=show)
        fr = view(sc, "weld-front", -math.pi / 2, 0, mid, show=show)
        pt_ = placer((-dx / 2, -dz / 2, dx / 2, dz / 2), (28, 150, 28 + dx * k, 150 + dz * k), k)
        pf = placer((-dy / 2, -dz / 2, dy / 2, dz / 2), (172, 150, 172 + dy * k, 150 + dz * k), k)
        s.geometry(tray_side, pt_, None, 0.2)
        s.geometry(fr, pf, None, 0.2)
        s.text(28, 254, "TRAY SIDE (front at left): %d rivets, tray to the side lips of the core and top panel" % len(TRAY_JOINS), 6, weight="bold")
        s.text(172, 254, "FRONT: %d rivets, bulkhead to the front lips" % len(BULKHEAD_JOINS), 6, weight="bold")
        rows = []
        for i, (x, z) in enumerate(TRAY_JOINS):
            p = pt_(-(x - mid[0]), z - mid[2])
            s.ax.add_patch(Circle(p, 2.5 * k * 1.6, fill=False, ec=RED, lw=0.6))
            s.line([(p[0] - 2.4, p[1]), (p[0] + 2.4, p[1])], 0.3, RED)
            s.line([(p[0], p[1] - 2.4), (p[0], p[1] + 2.4)], 0.3, RED)
            s.text(p[0] + 2.2, p[1] + 2.2, "T%d" % (i + 1), 5.2, RED, weight="bold")
            rows.append(["T%d" % (i + 1), "%.1f" % x, "tray side", "%.1f" % z])
        for i, (y_, z) in enumerate(BULKHEAD_JOINS):
            p = pf(y_ - mid[1], z - mid[2])
            s.ax.add_patch(Circle(p, 2.5 * k * 1.6, fill=False, ec=RED, lw=0.6))
            s.line([(p[0] - 2.4, p[1]), (p[0] + 2.4, p[1])], 0.3, RED)
            s.line([(p[0], p[1] - 2.4), (p[0], p[1] + 2.4)], 0.3, RED)
            s.text(p[0] + 2.2, p[1] + 2.2, "F%d" % (i + 1), 5.2, RED, weight="bold")
            rows.append(["F%d" % (i + 1), "front", "%.1f" % y_, "%.1f" % z])
        for y_ in TONGUES:
            p = pf(y_ - mid[1], PSU_TOP - mid[2])
            s.text(p[0] - 2.5, p[1] - 4, "slot", 4.6, BLUE)
        s.table(262, 284, "RIVETS MS20426AD3-4  (centres; origin below)", ["", "X", "Y", "Z"], rows, [12, 20, 20, 20], size=5.4)
        s.notes(262, 209, "RIVETING  (by the customer)", [
            "Datum: X from the inside face of the rear panel, Y from the inside face of the open-side lips, Z from the top face of the bottom panel.",
            "Top panel: on the rear panel's top lip and the bulkhead's, its rear edge flush with the rear panel's outside face, held there by the handles' four screws.",
            "Tray: its outer face against the inside of the 17 mm lips of the bottom, top and rear panels, 1.5 clear of each panel.",
            "Bulkhead: its front face against the inside of the front lips of the bottom and top panels, 1.5 clear of the bottom panel, its edge 0.3 from the tray.",
            "Every tray rivet is 9.5 from the panel its lip is folded from; F1 to F3 are at Z 20 and F4 to F6 at Z 200. Lip flats are 14.8 or more.",
            "Rivet: MS20426AD3-4, 3/32 in flush head, 2117 aluminium, 1/4 in long, in the 2.5 (No. 40) holes cut in both parts.",
            "Countersink each hole in the core's and the top panel's lips from outside, 100 deg to 4.6 across, until the head sits flush or 0.1 under. Do not countersink the tray or bulkhead.",
            "Head in the lip, outside. Drive the head with a flat punch while a steel bar is held against the tail inside, until the tail is 3.0 to 4.1 across and 0.8 to 1.5 tall.",
            "Both sides matter: the side and front panels pass 0.3 to 0.5 outside the lips, and the fans stand 2.8 inside the tray.",
            "Rivet the bulkhead to the bottom panel's lip first. Fit the top panel and both handles, then rivet the tray, then the bulkhead to the top panel's lip, starting each row from its middle.",
            "After riveting the open side must stay square: 128.0 +/-0.4 between the side lips, 210.0 +/-0.4 between top and bottom panels."],
            width=92)
        s.notes(28, 52, "NOTES", ["Outside faces of the lips are under the side and front panels, 0.3 to 0.5 clear: nothing may stand proud of them.",
                                  "The front panel's flanges (R-06) stand in line with the side lips, in front of them, and the side panels screw to both.",
                                  "Slots marked in the front view take the shelf's three tongues, which stand 0.9 in front of the bulkhead, under the front panel."], width=150)
        s.done()

        for i, b in enumerate(SHEET):
            part_sheet(pdf, sc, b, sizes, 3 + i, total)
        foot_sheet(pdf, 3 + len(SHEET), total)
    os.remove(fresh)
    print("wrote", PDF)


if __name__ == "__main__":
    main()
