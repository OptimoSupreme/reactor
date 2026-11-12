"""Draw the Reactor Mk I's manufacturing drawings as one PDF, mechanical/export/reactor-mk-i-drawings.pdf.

  python3 mechanical/drawings.py

Run mk1.py first: the drawings are made from the saved sheet metal design, its flat pattern DXFs and
its bend tables. Views of the formed parts come from the running SolidCraft, so SOLIDCRAFT_MCP is
needed as for mk1.py. Needs matplotlib.
"""
import csv
import datetime
import math
import os
import shutil
import time

import matplotlib
matplotlib.use("pdf")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.collections import LineCollection
from matplotlib.patches import Arc, Circle

import mk1
from mk1 import (BULKHEAD_JOINS, DESIGN, EXPORT, FOOT_RECESS, FOOT_RECESS_DEPTH, FOOT_TAP, FOOT_TAP_DEPTH, LX, LY, LZ, SHEET, SHELF_FRONT, T,
                 TRAY_JOINS)

VIEWS = os.path.expanduser("~/.cache/reactor/drawings")
PDF = os.path.join(EXPORT, "reactor-mk-i-drawings.pdf")
W, H = 420.0, 297.0   # A3 landscape
REV = "A"
INK, THIN, BLUE, RED = "#111111", "#555555", "#1f4e9c", "#b3261e"

NUMBER = {"core": "RMK1-01", "tray": "RMK1-02", "bulkhead": "RMK1-03", "shelf": "RMK1-04", "shell": "RMK1-05"}
TITLE = {"core": "Core: bottom, rear and top", "tray": "Mainboard tray", "bulkhead": "Front bulkhead",
         "shelf": "Power supply shelf", "shell": "Shell: front and sides"}
# what each round hole is for, by part and diameter
HOLES = {
    ("core", 5.0): "fan screw, self-tapping, clearance",
    ("core", 4.5): "shelf screws 6-32, loose clearance",
    ("core", 3.5): "+0.08/0: PEM FH-632-6 stud, bottom panel (4); mains inlet M3, rear panel (2)",
    ("core", 3.0): "PEM SF-3-1.2 SpotFast, head side, +0.08/0",
    ("core", 1.6): "tap M2 x 0.4 through",
    ("tray", 2.5): "PEM SF-3-1.2 SpotFast, second panel: see PEM bulletin SF",
    ("tray", 5.41): "PEM BSO-632-12 standoff, +0.08/0",
    ("bulkhead", 12.0): "power switch, +0.2/0",
    ("bulkhead", 2.5): "PEM SF-3-1.2 SpotFast, second panel: see PEM bulletin SF",
    ("bulkhead", 4.5): "shelf screws 6-32, loose clearance",
    ("shelf", 4.0): "6-32 clearance, supply: SFX pattern both ways round",
    ("shelf", 4.76): "PEM S-632-1 nut, +0.08/0",
    ("shelf", 22.0): "cable grommet",
    ("shell", 14.5): "power switch head, 14",
    ("shell", 2.8): "M2 clearance",
}
PART_NOTES = {
    "core": ["Hexagonal mesh: 9.6 across flats, webs 2.07; see DXF.",
             "Rear panel: I/O aperture 158.75 x 44.45 +/-0.2 to ATX 2.2 fig. 4; keep paint off both faces within 2.5 of it.",
             "Mains inlet cut-out 28 x 20 +0.2/0, R1, for Schurter 6100-3 mounted from outside.",
             "M2 threads (4) at the rear corners of the top and bottom panels: tap after bending.",
             "Four PEM FH-632-6 studs in the bottom panel for the feet, heads flush in its upper (inside) face, pointing down."],
    "tray": ["Flat. Four PEM BSO-632-12 standoffs pressed in from the face that goes against the core's lips, standing 9.53 off the other face.",
             "Install the standoffs before joining: two heads end up under the core's lips.",
             "Eight slots 2.0 x 5.0 in four pairs, for cable ties."],
    "bulkhead": ["Flat, no hardware."],
    "shelf": ["Two PEM S-632-1 nuts in the tabs, bodies under the tabs, flush on top. The tabs fold toward the rear, away from the front flange.",
              "Three PEM S-632-1 nuts in the front flange, flush on its front face, bodies behind it.",
              "Supplied loose: three screws through the bulkhead and two through the top panel hold it."],
    "shell": ["Plain outside faces: no marks, grain or tooling witness on the front and sides.",
              "Slots in three return flanges run onto M2 screw heads on the core; check the slide fit before finishing."],
}
GENERAL = [
    "All dimensions in mm. The STEP model and the DXF flat patterns govern; do not scale this drawing.",
    "Material: cold rolled low carbon steel, DC01 / SPCC / CR4 or equivalent, 1.2 thick.",
    "Inside bend radius 1.2 nominal. Flat patterns are drawn for K = 0.44: adjust to your tooling so the formed sizes hold.",
    "Tolerances unless stated: cut features +/-0.15, bend positions +/-0.4, angles +/-1 deg.",
    "Deburr all edges and break sharp corners. Outside corners are R1.5 where drawn.",
    "Self-clinching hardware: PennEngineering (PEM) or equivalent, installed before finishing.",
    "Core, tray and bulkhead are joined with PEM SF-3-1.2 SpotFast fasteners, flush or under flush on both faces (sheet 2).",
    "Finish: powder coat all over after joining, if offered; colour and texture to be agreed. Mask threads, studs and standoff bores.",
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
        cells = [(x0 + 2, y0 + 26, "TITLE", "Reactor Mk I  -  " + title), (x0 + 2, y0 + 11, "MATERIAL", material),
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
        sc.call("execute", {"command": "browser.visibility", "params": {"visible": False, "items": [b for b in SHEET if b not in show]}})
    sc.call("execute", {"command": "file.export_view_dxf", "params": {
        "camera": {"target": target, "yaw": yaw, "pitch": pitch, "distance": 200000, "fov": 0.005},
        "path": path, "curves": "arcs", "tolerance": 0.05}})
    if show is not None:
        sc.call("execute", {"command": "browser.visibility", "params": {"visible": True, "items": SHEET}})
    return entities(path)


def part_sheet(pdf, sc, body, sizes, n, total):
    flat = entities(os.path.join(EXPORT, body + ".dxf"))
    with open(os.path.join(EXPORT, body + "-bends.csv")) as f:
        bends = list(csv.DictReader(f))
    box = bbox(flat, ("OUTLINE",))
    place = placer(box, (22, 62, 268, 276))
    s = Sheet(pdf, NUMBER[body], TITLE[body], "CRS DC01, 1.2 mm", "flat " + ratio(place.k), n, total)
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
        ["Bends", "%d, all 90 deg, inside R1.2" % len(bends) if bends else "none"],
        ["Mass", "%.0f g" % sizes[body + "-g"]]], [26, 90])
    count = lambda d: sum(1 for e in flat if e["type"] == "CIRCLE" and e.get("layer") == "CUT" and round(2 * e[40], 2) == d)
    y = s.table(x0, y - 3, "ROUND HOLES", ["", "dia", "qty", "for"], [
        [letter[d], "%g" % d, count(d), HOLES.get((body, d), "")] for d in dias], [7, 12, 9, 90], size=5.2)
    if bends:
        rows = [["B" + r["bend"], "%g" % float(r["angle_deg"]), r["direction"], "%.1f" % float(r["length_mm"])] for r in bends]
        s.table(x0, y - 3, "BENDS", ["", "angle", "dir.", "length"], rows[:12], [10, 14, 14, 20], size=5.2)
    s.notes(14, 52, "NOTES", PART_NOTES[body] + ["General notes on sheet 1 apply."], width=150)
    s.done()


def foot_sheet(pdf, n, total):
    """The foot in half section, as it stands under the case."""
    k = 5.0
    s = Sheet(pdf, "RMK1-06", "Foot", "316L stainless steel, printed", "5 : 1", n, total)
    cx, top = 110.0, 230.0
    at = lambda r, z: (cx + r * k, top - z * k)
    out = [(0, 0), (10, 0), (10, 2), (8.5, 2), (6, 18), (0, 18)]
    s.line([at(-r, z) for r, z in out[::-1]] + [at(r, z) for r, z in out], 0.5)
    s.line([at(-8.5, 2), at(8.5, 2)], 0.25)
    d, r = FOOT_TAP_DEPTH, FOOT_TAP / 2
    s.line([at(r, 0), at(r, d), at(0, d + r * 0.6), at(-r, d), at(-r, 0)], 0.35, INK, "--")
    rr, rd = FOOT_RECESS / 2, FOOT_RECESS_DEPTH
    s.line([at(-rr, 18), at(-rr, 18 - rd), at(rr, 18 - rd), at(rr, 18)], 0.35, INK, "--")
    s.dim(at(-rr, 18), at(rr, 18), -17, "recess dia %.1f x %.1f deep" % (FOOT_RECESS, rd))
    s.line([at(0, -3), at(0, 21)], 0.2, THIN, "-.")
    s.text(cx - 50, top + 22, "SIDE  (flange up, against the bottom panel; hole and recess shown hidden)", 6.5, weight="bold")
    s.dim(at(-10, 0), at(10, 0), 8, "dia 20.0")
    s.dim(at(-6, 18), at(6, 18), -8, "dia 12.0")
    s.dim(at(10, 0), at(10, 2), 16, "2.0", vertical=True)
    s.dim(at(10, 0), at(10, 18), 30, "18.0", vertical=True)
    s.dim(at(-10, 0), at(-10, d), -22, "%.1f min" % d, vertical=True)
    s.text(at(8.5, 2)[0] + 3, at(8.5, 2)[1] - 4, "dia 17.0 under the flange,", 5.6, BLUE)
    s.text(at(8.5, 2)[0] + 3, at(8.5, 2)[1] - 8, "tapering to 12.0", 5.6, BLUE)
    s.text(at(0, 6)[0] + 9, at(0, 6)[1], "6-32 UNC-2B", 5.6, BLUE)
    s.table(262, 284, "PART", ["", ""], [["Quantity", "4"], ["Model", "foot.step"], ["Mass", "about 25 g"],
                                         ["Thread", "6-32 UNC-2B, %.1f drill, %.0f deep" % (FOOT_TAP, d)]], [26, 90])
    s.notes(262, 250, "NOTES", [
        "Printed in 316L stainless steel by laser powder bed fusion or binder jetting.",
        "Tap 6-32 UNC-2B after printing, 10 of full thread or more. foot.step has the %.1f tap drill hole, not the thread; drill it to size first if it prints small." % FOOT_TAP,
        "The flange's top face sits against the case: flat within 0.1, no support marks.",
        "Recess underneath for a stick-on bumper, 3M Bumpon SJ5076 (8.0 dia x 2.8), which stands 1.3 below the rim.",
        "Each foot turns onto a PEM FH-632-6 stud standing 9.5 out of the bottom panel, hand tight with thread lock.",
        "Finish to match the case."], width=92)
    s.done()


def main():
    sc = mk1.Bridge()
    os.makedirs(VIEWS, exist_ok=True)
    # a copy under a new name: opening DESIGN itself can land on a tab still showing an earlier build
    fresh = os.path.join(VIEWS, "sheet-%d.sc" % time.time())
    shutil.copy(DESIGN, fresh)
    sc.call("open", {"path": fresh})
    m = sc.call("measure", {"summary": True})
    sizes = {}
    for b in m["bodies"]:
        if b["name"] in SHEET:
            sizes[b["name"]] = (b["bbox"]["min"], b["bbox"]["max"])
            sizes[b["name"] + "-g"] = b["volume_mm3"] * 7.85e-3
    lo = [min(sizes[b][0][i] for b in SHEET) for i in range(3)]
    hi = [max(sizes[b][1][i] for b in SHEET) for i in range(3)]
    mid = [(lo[i] + hi[i]) / 2 for i in range(3)]
    total = 3 + len(SHEET)
    with PdfPages(PDF) as pdf:
        # sheet 1: general arrangement
        k = 0.4
        s = Sheet(pdf, "RMK1-00", "General arrangement", "see parts", ratio(k), 1, total)
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
        rows = [[NUMBER[b], TITLE[b], 1, "%.0f g" % sizes[b + "-g"], b + ".step, " + b + ".dxf"] for b in SHEET]
        y = s.table(232, 196, "PARTS  (all 1.2 mm cold rolled steel)", ["no.", "part", "qty", "mass", "files"], rows, [18, 62, 9, 16, 60])
        hw = [["PEM BSO-632-12", "blind standoff, 6-32, 9.53 long", 4, "tray"],
              ["PEM FH-632-6", "flush-head stud, 6-32, 9.53 long", 4, "core, bottom panel"],
              ["PEM S-632-1", "self-clinching nut, 6-32", 5, "shelf"],
              ["PEM SF-3-1.2", "SpotFast: tray to core 9, bulkhead to core 4", 13, "sheet 2"],
              ["M2 x 0.4 tap", "through, 1.6 drill", 4, "core"]]
        s.table(232, y - 4, "HARDWARE AND JOINING BY THE FABRICATOR", ["item", "", "qty", "where"], hw, [30, 62, 9, 40])
        s.notes(30, 52, "SCOPE", ["Five sheet metal parts. Core, tray and bulkhead are supplied joined as one assembly (sheet 2); "
                                  "shelf and shell are supplied loose.",
                                  "Fans, mainboard, power supply, mains inlet, switch, screws and feet are fitted by the customer. "
                                  "The feet (sheet %d) are made separately." % total], width=135)
        s.done()

        # sheet 2: joined assembly
        k = 0.45
        s = Sheet(pdf, "RMK1-10", "Joined assembly: core, tray, bulkhead", "RMK1-01, -02, -03", ratio(k), 2, total)
        show = ["core", "tray", "bulkhead"]
        tray_side = view(sc, "weld-tray", math.pi, 0, mid, show=show)
        fr = view(sc, "weld-front", -math.pi / 2, 0, mid, show=show)
        pt_ = placer((-dx / 2, -dz / 2, dx / 2, dz / 2), (28, 150, 28 + dx * k, 150 + dz * k), k)
        pf = placer((-dy / 2, -dz / 2, dy / 2, dz / 2), (172, 150, 172 + dy * k, 150 + dz * k), k)
        s.geometry(tray_side, pt_, None, 0.2)
        s.geometry(fr, pf, None, 0.2)
        s.text(28, 254, "TRAY SIDE (front at left): 9 SpotFast, tray to the side lips of the core", 6, weight="bold")
        s.text(172, 254, "FRONT: 4 SpotFast, bulkhead to front lips", 6, weight="bold")
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
        for i, (y_, z) in enumerate(SHELF_FRONT):
            p = pf(y_ - mid[1], z - mid[2])
            s.text(p[0] + 1.5, p[1] - 3.5, "screw", 4.6, BLUE)
        s.table(262, 284, "SPOTFAST SF-3-1.2  (centres; origin below)", ["", "X", "Y", "Z"], rows, [12, 20, 20, 20], size=5.4)
        s.notes(262, 215, "JOINING", [
            "Datum: X from the inside face of the rear panel, Y from the inside face of the open-side lips, Z from the top face of the bottom panel.",
            "Tray: its outer face against the inside of the 17 mm lips of the bottom, top and rear panels, 1.5 clear of each panel.",
            "Bulkhead: its front face against the inside of the front lips of the top and bottom panels, 1.5 clear of each panel, its edge 0.3 from the tray.",
            "Every fastener is 9.5 from the panel its lip is folded from, except F1 and F2 at Z 20. Lip flats are 14.6 or more.",
            "Install the studs and standoffs first. Join the tray first, then the bulkhead.",
            "SpotFast: 3.0 +0.08/0 holes in the core's lips, 2.5 in the tray and bulkhead, heads in the lips. Both faces must end flush: there is 0.3 to 0.5 outside the lips and 2.8 inside the tray.",
            "Spot welding at the same centres is an accepted alternative: nugget 5 min, upset dressed flush outside. Leave the 13 holes out.",
            "After joining the open side must stay square: 128.0 +/-0.4 between the side lips, 210.0 +/-0.4 between top and bottom panels."],
            width=92)
        s.notes(28, 52, "NOTES", ["Outside faces of the lips are under the shell, which slides over them 0.5 clear: nothing may stand proud of them.",
                                  "Holes marked in the front view take the shelf's three screws: NBK SETS-#6-32, head 0.86 tall, or any 6-32 with a head under 1.2."], width=150)
        s.done()

        for i, b in enumerate(SHEET):
            part_sheet(pdf, sc, b, sizes, 3 + i, total)
        foot_sheet(pdf, 3 + len(SHEET), total)
    os.remove(fresh)
    print("wrote", PDF)


if __name__ == "__main__":
    main()
