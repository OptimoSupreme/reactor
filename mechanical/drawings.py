"""Draw the Reactor's manufacturing drawings in SolidCraft's drawing workspace.

  python3 mechanical/drawings.py

Run reactor.py first. This opens reactor.sc, draws a drawing of seven sheets in it and saves it, so the
drawing lives in the design; then draws the foot's sheet in a design of its own, foot.sc. Each sheet is
exported as SVG and the lot bound into mechanical/export/reactor-drawings.pdf, with the foot's sheet
alone as foot-drawing.pdf for whoever prints the feet. SOLIDCRAFT_MCP as for reactor.py; needs
rsvg-convert (librsvg) for the PDFs.
"""
import datetime
import json
import os
import shutil
import subprocess
import time

import reactor
from reactor import (BULKHEAD_JOINS, DESIGN, EXPORT, FEET, FOOT_CROSS, FOOT_CROSS_DEPTH, FOOT_RECESS, FOOT_RECESS_DEPTH,
                     FOOT_TAP, LX, LY, LZ, PART_NUMBER, PART_TITLE, PSU_TOP, SHEET, T, TONGUES, TRAY_JOINS)

WORK = os.path.expanduser("~/.cache/reactor/drawings")
PDF = os.path.join(EXPORT, "reactor-drawings.pdf")
FOOT_DESIGN = os.path.join(os.path.dirname(DESIGN), "foot.sc")
FOOT_PDF = os.path.join(EXPORT, "foot-drawing.pdf")
FOOT_THREAD = 10.0   # full thread asked for: the stud stands 9.5 at most
OWNER = "Justin Ward, CERN-OHL-S v2"
SCALES = [(1, "1:1"), (1 / 1.5, "1:1.5"), (0.5, "1:2"), (0.4, "1:2.5"), (1 / 3, "1:3"), (0.25, "1:4"), (0.2, "1:5")]

# what each round hole is for, by part and diameter
HOLES = {
    ("core", 5.0): "fan screw, self-tapping, clearance",
    ("core", 4.5): "6-32, loose clearance: shelf screws (2) and handle screws (4), top panel",
    ("core", 3.5): "+0.08/0: PEM FH-632-6 stud, bottom panel (4); mains inlet M3, rear panel (2)",
    ("core", 2.5): "rivet, 3/32 in; countersunk by the customer",
    ("core", 4.76): "PEM S-632-1 nut for a shell screw, +0.08/0, one in each side lip of the rear panel",
    ("tray", 2.5): "rivet, 3/32 in",
    ("tray", 5.41): "PEM BSO-632-12 standoff, +0.08/0",
    ("bulkhead", 12.0): "power switch, +0.2/0",
    ("bulkhead", 8.0): "LED holder, +0.2/0",
    ("bulkhead", 2.5): "rivet, 3/32 in",
    ("shelf", 4.0): "6-32 clearance, supply: SFX pattern both ways round",
    ("shelf", 4.76): "PEM S-632-1 nut, +0.08/0",
    ("shell", 14.5): "power switch head, 14",
    ("shell", 11.3): "LED holder's bezel, 10.8",
    ("shell", 4.5): "shell screw 6-32, loose clearance, one in each side",
}
PART_NOTES = {
    "core": ["Hexagonal mesh: 9.6 across flats, webs 2.07; see DXF.",
             "Rear panel: I/O aperture 158.75 x 44.45 +/-0.2 to ATX 2.2 fig. 4; keep paint off both faces within 2.5 of it.",
             "Mains inlet cut-out 28 x 20 +0.2/0, R1, for Schurter 6100-3 mounted from outside.",
             "Two PEM S-632-1 nuts, one in each side lip of the rear panel, flush on the outside, bodies inside.",
             "Four 4.5 holes at the corners of the top panel take the screws of two handles, fitted by the customer.",
             "The top panel's front lip is cut back at both ends, round the switch and the two lamps in the bulkhead behind it: 7.0 of flange is left over the lamps.",
             "Four PEM FH-632-6 studs in the bottom panel for the feet, heads flush in its upper (inside) face, pointing down."],
    "tray": ["Flat. Four PEM BSO-632-12 standoffs pressed in from the face that goes against the core's lips, standing 9.53 off the other face.",
             "The standoffs go in before the customer rivets the tray on: two heads end up under the core's lips.",
             "Eight slots 2.0 x 5.0 in four pairs, for cable ties.",
             "The notch in the rear edge goes round the body of the nut in the core's lip."],
    "bulkhead": ["Flat, no hardware.", "Three slots 13.0 x 2.2, corners R0.5, for the shelf's tongues: keep their lower edges clean and square."],
    "shelf": ["Two PEM S-632-1 nuts in the tabs, bodies under the tabs, flush on top. The tabs fold toward the rear, away from the supply.",
              "Three tongues 12.0 wide on the front edge, standing 2.4 beyond it, go through the bulkhead's slots: no burr on them.",
              "Supplied loose: its tongues sit in the bulkhead's slots and two screws through the top panel hold it.",
              "The notch in the tray-side edge of the rear wall, 13.0 deep and 17.0 tall, corners R3, is for the mains lead and the switch and lamp wires: no burr, it is lined with edge trim."],
    "shell": ["Plain outside faces: no marks, grain or tooling witness on the front and sides.",
              "The four return flanges are plain. The shell slides onto the core from the front, 0.5 clear all round, and a screw through each side holds it."],
}
GENERAL = [
    "All dimensions in mm. The STEP model and the DXF flat patterns govern; do not scale this drawing.",
    "Material: cold rolled low carbon steel, 1008 or equivalent, 0.048 in (1.2) thick.",
    "Inside bend radius 1.0 and K = 0.516, Fabworks' figures for this sheet. The STEP models are the formed sizes to hold.",
    "Tolerances unless stated: cut features +/-0.15, bend positions +/-0.4, angles +/-1 deg.",
    "Deburr all edges and break sharp corners. Outside corners are R1.5 where drawn.",
    "Self-clinching hardware: PennEngineering (PEM), installed by the fabricator: twelve pieces, listed below.",
    "All five parts are supplied loose. The customer rivets the tray and bulkhead to the core (sheet 2).",
    "Finish: none ordered. If powder coated, mask threads, studs and standoff bores.",
]


class Drawing:
    """The drawing open in SolidCraft. Text is put on a sheet a line at a time, as notes, which the app
    centres on the point given, so each character's width is measured once to set lines flush left."""

    def __init__(self, sc, name, template):
        self.sc = sc
        d = self.run("drawing.create", {"name": name, "template": template, "units": "mm"})
        self.first = d["sheets"][0]["id"]
        self.count = 0
        self.widths = self.measure()

    def run(self, command, params=None):
        return self.sc.call("execute", {"command": command, "params": params or {}})

    def measure(self):
        """Width of each character at 1 mm cap height, from a sheet of notes that is then deleted."""
        chars = [chr(c) for c in range(33, 127)] + ["±", "°", "Ø"]
        sheet = self.run("drawing.sheet.add", {"name": "measure"})["sheet"]
        made = self.sc.batch([("drawing.note.add", {"anchor": {"sheet": sheet}, "at": [200, 20 + 2.5 * i],
                                                    "content": c * 20, "cap_mm": 2.0}) for i, c in enumerate(chars)]
                             + [("drawing.note.add", {"anchor": {"sheet": sheet}, "at": [200, 10], "content": "H" + " " * 20 + "H",
                                                      "cap_mm": 2.0})], "measure")
        box = {o["object"]: o["bounds_mm"] for o in self.run("drawing.scene", {"sheet": sheet})["objects"]}
        wide = lambda r: box[r["note"]]["max"][0] - box[r["note"]]["min"][0]
        w = {c: wide(r) / 40.0 for c, r in zip(chars, made)}
        w[" "] = (wide(made[-1]) / 2.0 - 2 * w["H"]) / 20.0
        self.run("drawing.sheet.delete", {"sheet": sheet, "contents": "delete"})
        return w

    def width(self, s, cap):
        return sum(self.widths.get(c, self.widths["n"]) for c in s) * cap

    def sheet(self, title, number, material="", mass="", scale=""):
        """The next sheet, with its title block filled in."""
        over = {"title": title, "identification_number": number, "created_by": "Justin Ward",
                "date_of_issue": datetime.date.today().isoformat(), "material": material, "mass": mass,
                "finish": "none ordered", "legal_owner": OWNER,
                "general_tolerances": "Cut ±0.15, bends ±0.4, angles ±1°"}
        self.count += 1
        if self.count == 1:
            self.run("drawing.sheet.set", {"sheet": self.first, "name": number, "title_block_overrides": over})
            s = Sheet(self, self.first)
        else:
            s = Sheet(self, self.run("drawing.sheet.add", {"name": number, "title_block_overrides": over})["sheet"])
        s.text(231, 62, "SCALE (A3)  " + scale + "     third angle projection, mm", 2.2)   # the block has no cell for it
        return s


class Sheet:
    def __init__(self, drawing, sheet):
        self.d, self.id, self.steps = drawing, sheet, []

    def text(self, x, y, s, cap=2.2):
        """One line, its left end at x and its middle at y."""
        if s:
            self.steps.append(("drawing.note.add", {"anchor": {"sheet": self.id}, "at": [round(x + self.d.width(s, cap) / 2, 2), round(y, 2)],
                                                    "content": s, "cap_mm": cap}))

    def notes(self, x, y, title, lines, width, cap=2.2):
        """A numbered list, wrapped to `width`; returns the y under it."""
        self.text(x, y, title, 3.0)
        y -= 6
        for i, line in enumerate(lines):
            row = "%d. " % (i + 1)
            for word in line.split(" "):
                if self.d.width(row + word, cap) > width:
                    self.text(x, y, row, cap)
                    y -= 1.8 * cap
                    row = "    "
                row += word + " "
            self.text(x, y, row.rstrip(), cap)
            y -= 2.1 * cap
        return y

    def table(self, x, y, title, head, rows, widths, cap=2.2):
        self.text(x, y, title, 3.0)
        y -= 6
        for row in ([head] if any(head) else []) + rows:
            cx = x
            for cell, w in zip(row, widths):
                self.text(cx, y, str(cell), cap)
                cx += w
            y -= 1.9 * cap
        return y - 2

    def view(self, command, params):
        """Place a view, and return it with a function from a point of the model to the paper."""
        r = self.d.run(command, dict(params, **({"sheet": self.id} if "parent" not in params else {})))
        i = self.d.run("drawing.view.inspect", {"view": r["view"]})
        k = r["scale"]["factor"]
        lo, hi, e0, e1 = i["boundary_mm"]["min"], i["boundary_mm"]["max"], i["extents"]["min"], i["extents"]["max"]
        ax = i["direction"]
        dot = lambda a, b: sum(a[j] * b[j] for j in range(3))
        if i["kind"] == "flat":   # a point of the flat pattern
            at = lambda p: [lo[0] + (p[0] - e0[0]) * k, lo[1] + (p[1] - e0[1]) * k]
        else:
            at = lambda p: [(lo[0] + hi[0]) / 2 + (dot(p, ax["x"]) - (e0[0] + e1[0]) / 2) * k,
                            (lo[1] + hi[1]) / 2 + (dot(p, ax["y"]) - (e0[1] + e1[1]) / 2) * k]
        return r["view"], at, (lo, hi)

    def dim(self, view, kind, **more):
        """A dimension, or a line saying why not: a drawing with one dimension missing is still wanted."""
        try:
            self.d.run("drawing.dimension.add", dict({"view": view, "kind": kind, "decimals": 1}, **more))
        except SystemExit as e:
            print("  no dimension %s: %s" % (json.dumps(kind)[:80], str(e)[:160]))

    def done(self):
        if self.steps:
            self.d.sc.batch(self.steps, "text")


def fit(size, area):
    """The largest of SCALES at which `size` goes in `area`."""
    return next(s for s in SCALES if size[0] * s[0] <= area[0] and size[1] * s[0] <= area[1])


def general(d, occ, sizes):
    lo = [min(sizes[b][0][i] for b in SHEET) for i in range(3)]
    hi = [max(sizes[b][1][i] for b in SHEET) for i in range(3)]
    s = d.sheet("Reactor - general arrangement", "R-00", "see parts", scale="1:4")
    side, at, box = s.view("drawing.view.base", {"view": "front", "scale": "1:4", "position_mm": [70, 105]})
    top = d.run("drawing.view.projected", {"parent": side, "side": "above"})["view"]
    front = d.run("drawing.view.projected", {"parent": side, "side": "right"})["view"]
    s.view("drawing.view.base", {"view": "iso", "scale": "1:4", "position_mm": [170, 215]})
    s.text(20, 280, "SIDE (open side; rear at left), TOP above it, FRONT beside it", 2.6)
    shell, core, mid = [occ["shell"]], [occ["core"]], [(lo[i] + hi[i]) / 2 for i in range(3)]
    face = lambda p, path: {"point": p, "path": path}
    s.dim(side, {"faces": {"a": face([lo[0], mid[1], mid[2]], core), "b": face([hi[0], mid[1], mid[2]], shell), "direction": "horizontal"}},
          offset_mm=12)
    s.dim(side, {"faces": {"a": face([mid[0], lo[1] + 5, lo[2]], shell), "b": face([mid[0], lo[1] + 5, hi[2]], shell), "direction": "vertical"}},
          offset_mm=12)
    s.dim(front, {"faces": {"a": face([mid[0], lo[1], mid[2]], shell), "b": face([mid[0], hi[1], mid[2]], shell), "direction": "horizontal"}},
          offset_mm=12)
    y = s.notes(235, 280, "GENERAL NOTES", GENERAL, 168)
    rows = [[PART_NUMBER[b], PART_TITLE[b], 1, "%.0f g" % sizes[b + "-g"], b + ".step, " + b + ".dxf"] for b in SHEET]
    y = s.table(235, y - 3, "PARTS  (all 0.048 in / 1.2 mm cold rolled steel)", ["no.", "part", "qty", "mass", "files"], rows,
                [14, 58, 9, 16, 60])
    hw = [["PEM BSO-632-12", "blind standoff, 6-32, 9.53 long", 4, "tray"],
          ["PEM FH-632-6", "flush-head stud, 6-32, 9.53 long", 4, "core, bottom panel"],
          ["PEM S-632-1", "self-clinching nut, 6-32", 4, "shelf 2, core 2"]]
    s.table(235, y, "HARDWARE BY THE FABRICATOR  (Fabworks' ZI parts)", ["item", "", "qty", "where"], hw, [34, 62, 9, 40])
    s.text(20, 64, "OVERALL  %.1f x %.1f x %.1f" % tuple(hi[i] - lo[i] for i in range(3)), 3.0)
    s.notes(20, 54, "SCOPE", [
        "Five sheet metal parts, cut, bent and with their PEM hardware pressed in, all supplied loose.",
        "The customer rivets the core, tray and bulkhead together (sheet 2: %d rivets MS20426AD3-4)." % (len(TRAY_JOINS) + len(BULKHEAD_JOINS)),
        "Fans, mainboard, power supply, mains inlet, switch, handles, screws and feet are fitted by the customer. "
        "The feet (sheet 8) are made separately."], 200)
    s.done()


def riveted(d, occ):
    s = d.sheet("Riveted assembly", "R-10", "R-01, R-02, R-03", scale="1:2")
    three = {"occurrences": [[occ[b]] for b in ("core", "tray", "bulkhead")]}
    tray, at_tray, box = s.view("drawing.view.base", {"view": "back", "scale": "1:2", "position_mm": [82, 175], "source": three})
    front, at_front, fbox = s.view("drawing.view.base", {"view": "right", "scale": "1:2", "position_mm": [200, 175], "source": three})
    s.text(box[0][0], box[1][1] + 8, "TRAY SIDE (front at left): %d rivets, tray to the side lips of the core" % len(TRAY_JOINS), 2.4)
    s.text(fbox[0][0], fbox[0][1] - 8, "FRONT: %d rivets, bulkhead to front lips" % len(BULKHEAD_JOINS), 2.4)
    rows = []
    for i, (x, z) in enumerate(TRAY_JOINS):
        p = at_tray([x, LY + T, z])
        s.text(p[0] + 1.6, p[1] + 2.2, "T%d" % (i + 1), 2.0)
        rows.append(["T%d" % (i + 1), "%.1f" % x, "tray side", "%.1f" % z])
    for i, (y, z) in enumerate(BULKHEAD_JOINS):
        p = at_front([LX + T, y, z])
        s.text(p[0] + 1.6, p[1] + 2.2, "F%d" % (i + 1), 2.0)
        rows.append(["F%d" % (i + 1), "front", "%.1f" % y, "%.1f" % z])
    for y in TONGUES:
        p = at_front([LX, y, PSU_TOP])
        s.text(p[0] - 3, p[1] - 3, "slot", 1.8)
    y = s.table(250, 280, "RIVETS MS20426AD3-4  (centres; datum in note 1)", ["", "X", "Y", "Z"], rows, [12, 20, 22, 20])
    s.notes(250, y - 2, "RIVETING  (by the customer)", [
        "Datum: X from the inside face of the rear panel, Y from the inside face of the open-side lips, Z from the top face of the bottom panel.",
        "Tray: its outer face against the inside of the 17 mm lips of the bottom, top and rear panels, 1.5 clear of each panel.",
        "Bulkhead: its front face against the inside of the front lips of the top and bottom panels, 1.5 clear of each panel, its edge 0.3 from the tray.",
        "Every rivet is 9.5 from the panel its lip is folded from, except F1 and F2 at Z 20. Lip flats are 14.8 or more.",
        "Rivet: MS20426AD3-4, 3/32 in flush head, 2117 aluminium, 1/4 in long, in the 2.5 (No. 40) holes cut in both parts.",
        "Countersink each hole in the core's lip from outside, 100 deg to 4.6 across, until the head sits flush or 0.1 under. Do not countersink the tray or bulkhead.",
        "Head in the lip, outside. Drive the head with a flat punch while a steel bar is held against the tail inside, until the tail is 3.0 to 4.1 across and 0.8 to 1.5 tall.",
        "Both sides matter: the shell passes 0.3 to 0.5 outside the lips, and the fans stand 2.8 inside the tray.",
        "Rivet the tray first, then the bulkhead, starting each from its middle.",
        "After riveting the open side must stay square: 128.0 +/-0.4 between the side lips, 210.0 +/-0.4 between top and bottom panels."],
        152, 2.0)
    s.notes(20, 52, "NOTES", ["Outside faces of the lips are under the shell, which slides over them 0.5 clear: nothing may stand proud of them.",
                              "Slots marked in the front view take the shelf's three tongues, which stand 0.9 in front of the bulkhead, under the shell."], 200)
    s.done()


def part(d, occ, body, sizes):
    flat = d.run("sheet.flat_pattern", {"body": body})
    fx, fy = flat["flat_size_mm"][:2]
    k, scale = fit((fx, fy), (265, 150))
    s = d.sheet(PART_TITLE[body], PART_NUMBER[body], "steel 1008, 0.048 in", "%.0f g" % sizes[body + "-g"], "flat " + scale)
    view, at, box = s.view("drawing.view.flat", {"body": body, "scale": scale, "position_mm": [150, 195]})
    s.text(20, 282, "FLAT PATTERN  %.1f x %.1f  (bend lines chain-dotted, numbered as in %s-bends.csv)" % (fx, fy, body), 2.6)
    for b in flat["bends"]:
        p = at([(b["start"][0] + b["end"][0]) / 2, (b["start"][1] + b["end"][1]) / 2])
        s.text(p[0] + 1, p[1] + 2, "B%d" % b["bend"], 2.0)
    holes = [c["circle"] for c in flat["cutout_shapes"] if "circle" in c]
    dias = sorted({round(2 * c["radius"], 2) for c in holes}, reverse=True)
    letter = {dia: chr(65 + i) for i, dia in enumerate(dias)}
    for c in holes:
        p = at(c["center"])
        s.text(p[0] + c["radius"] * k + 0.4, p[1] + 1.2, letter[round(2 * c["radius"], 2)], 1.6)
    s.text(300, 282, "FORMED  (not to scale)", 2.6)
    lo, hi = sizes[body]
    formed = fit((0.8 * (hi[0] - lo[0] + hi[1] - lo[1]), 0.5 * (hi[0] - lo[0] + hi[1] - lo[1]) + 0.82 * (hi[2] - lo[2])), (105, 80))[1]
    s.view("drawing.view.base", {"view": "iso", "scale": formed, "position_mm": [352, 235], "source": {"occurrences": [[occ[body]]]}})
    bends = flat["bends"]
    y = s.table(300, 188, "PART", ["", ""], [
        ["Formed size", "%.1f x %.1f x %.1f" % tuple(hi[i] - lo[i] for i in range(3))],
        ["Flat size", "%.1f x %.1f" % (fx, fy)],
        ["Bends", "%d, all 90 deg, inside R1.0" % len(bends) if bends else "none"],
        ["Mass", "%.0f g" % sizes[body + "-g"]]], [24, 80])
    count = lambda dia: sum(1 for c in holes if round(2 * c["radius"], 2) == dia)
    hole_rows = []
    for dia in dias:   # what a hole is for can run to two lines
        words, row = HOLES.get((body, dia), "").split(" "), ""
        first = [letter[dia], "%g" % dia, count(dia)]
        for word in words:
            if d.width(row + word, 1.9) > 78:
                hole_rows.append(first + [row])
                first, row = ["", "", ""], ""
            row += word + " "
        hole_rows.append(first + [row.rstrip()])
    y = s.table(300, y, "ROUND HOLES", ["", "dia", "qty", "for"], hole_rows, [6, 10, 8, 80], 1.9)
    if bends:
        rows = [["B%d" % b["bend"], "%g" % b["angle_deg"], b["direction"], "%.1f" % b["length"]] for b in bends]
        s.table(300, y, "BENDS", ["", "angle", "dir.", "length"], rows[:12], [10, 14, 14, 20], 1.9)
    s.notes(20, 100, "NOTES", PART_NOTES[body] + ["General notes on sheet 1 apply."], 255)
    s.done()


def foot(sc, pages):
    """The foot in a design of its own, drawn where the first of the four stands under the case."""
    x, y = FEET[0]
    sc.call("execute", {"command": "file.new", "params": {}})
    sc.batch(reactor.foot("foot", x, y), "foot")
    sc.call("execute", {"command": "file.save", "params": {"path": FOOT_DESIGN, "overwrite": True}})
    d = Drawing(sc, "Foot", "iso-a3-part")
    s = d.sheet("Foot", "R-06", "316L stainless steel, SLM / DMLS", "about 25 g", "5:1, views 3:1")
    below, at, box = s.view("drawing.view.base", {"view": "bottom", "scale": "3:1", "position_mm": [60, 215]})
    s.text(box[0][0], box[1][1] + 6, "FROM BELOW  3:1", 2.6)
    above, at2, box2 = s.view("drawing.view.base", {"view": "top", "scale": "3:1", "position_mm": [60, 120]})
    s.text(box2[0][0], box2[1][1] + 6, "ON THE FLANGE  3:1", 2.6)
    try:
        cut = d.run("drawing.view.section", {"parent": above, "line": {"kind": "full", "points": [[x - 13, y], [x + 13, y]], "arrows": "left"},
                                             "place": {"at": [165, 150]}})
        d.run("drawing.view.edit", {"view": cut["view"], "set": {"scale": "5:1"}})
        s.text(112, 262, "SECTION, as it stands under the case: flange up", 2.6)
        z0 = -T
        face = lambda p: {"point": p}
        s.dim(cut["view"], {"faces": {"a": face([x + 9, y, z0]), "b": face([x + 5, y, z0 - 18]), "direction": "vertical"}}, offset_mm=14)
        s.dim(cut["view"], {"faces": {"a": face([x + 9, y, z0]), "b": face([x + 9.5, y, z0 - 2]), "direction": "vertical"}}, offset_mm=8)
        s.dim(cut["view"], {"cylinder": {"face": [x + 10, y, z0 - 1]}}, offset_mm=26)
        s.dim(cut["view"], {"cylinder": {"face": [x + FOOT_RECESS / 2, y, z0 - 18 + FOOT_RECESS_DEPTH / 2]}}, offset_mm=10)
    except SystemExit as e:
        print("  no section:", str(e)[:300])
    (sw, sl), sd, rd = FOOT_CROSS, FOOT_CROSS_DEPTH, FOOT_RECESS_DEPTH
    yb = s.table(250, 280, "PART", ["", ""], [["Quantity", "4"], ["Model", "foot.step  (one body, mm)"],
                                             ["Material", "316L stainless steel, laser powder bed fusion"],
                                             ["Finish", "blasted matte all over, as ordered"], ["Mass", "about 25 g each"]], [22, 100])
    yb = s.table(250, yb, "SIZES", ["", ""], [
        ["Flange", "dia 20.0, 2.0 thick"], ["Body", "dia 17.0 under the flange, tapering to 12.0; 18.0 tall overall"],
        ["Hole", "dia %.1f right through: tap drill for 6-32" % FOOT_TAP],
        ["Recess", "dia %.1f x %.1f deep, underneath, for a stick-on pad" % (FOOT_RECESS, rd)],
        ["Cross slot", "two slots %.1f wide x %.1f long, %.1f deep, in the recess's floor" % (sw, sl, sd)]], [22, 100])
    yb = s.notes(250, yb, "THREAD  (the one operation after printing)", [
        "Tap one 6-32 UNC-2B thread in each foot, on its axis, from the flange's flat face.",
        "Full thread to %.0f deep or more. The hole goes right through into the cross slot, so the tap can run through: no bottoming tap is needed." % FOOT_THREAD,
        "foot.step has the hole at %.1f, the tap drill size, with no thread modelled. Drill it out before tapping if it prints small; any drill from 2.7 to 2.9 will do." % FOOT_TAP,
        "Thread square to the flange's face within 0.5 deg: the foot is screwed down onto a stud until that face seats.",
        "Check: a 6-32 screw turns in by hand to %.0f deep." % FOOT_THREAD], 152, 2.0)
    s.notes(250, yb - 2, "NOTES", [
        "All dimensions in mm. The STEP model governs; this drawing adds the thread and the notes.",
        "Tolerance +/-0.3 unless stated.",
        "The flange's flat face sits against the case: flat within 0.2, with no support marks left standing on it.",
        "The cross slot in the recess's floor is as printed: the foot is turned tight with a PH2 (No. 2 Phillips) screwdriver, whose point goes into the hole and whose wings sit in the slots. Slots %.1f wide or more." % (sw - 0.3),
        "The recess underneath takes a stick-on pad 8.0 across, which the customer fits.",
        "Each foot turns onto a 6-32 stud that stands 9.5 out of the case's bottom panel.",
        "Remove loose powder from the hole, the slots and the recess. Break sharp edges."], 152, 2.0)
    s.done()
    pages.append(export(d, s.id, "foot"))
    sc.call("execute", {"command": "drawing.close", "params": {}})
    sc.call("execute", {"command": "file.save", "params": {"path": FOOT_DESIGN, "overwrite": True}})


def export(d, sheet, name):
    path = os.path.join(WORK, name + ".svg")
    r = d.run("drawing.export", {"sheet": sheet, "format": "svg", "path": path})
    bad = [v for v in r.get("views", []) if v.get("status") != "drawn"]
    if bad:
        print("  %s: views not drawn: %s" % (name, json.dumps(bad)[:300]))
    return path


def main():
    sc = reactor.Bridge()
    os.makedirs(WORK, exist_ok=True)
    # a copy under a new name: opening DESIGN itself can land on a tab still showing an earlier build
    fresh = os.path.join(WORK, "sheet-%d.sc" % time.time())
    shutil.copy(DESIGN, fresh)
    sc.call("open", {"path": fresh})
    run = lambda c, p=None: sc.call("execute", {"command": c, "params": p or {}})
    for old in run("drawing.list")["drawings"]:
        run("drawing.delete", {"drawing": old["id"]})
    sizes = {}
    for b in sc.call("measure", {"summary": True})["bodies"]:
        if b["name"] in SHEET:
            sizes[b["name"]] = (b["bbox"]["min"], b["bbox"]["max"])
            sizes[b["name"] + "-g"] = b["volume_mm3"] * 7.85e-3
    occ = {c["name"]: c["occurrences"][0]["id"] for c in run("component.list", {"compact": True})["components"] if c["occurrences"]}
    d = Drawing(sc, "Reactor", "iso-a3-assembly")
    general(d, occ, sizes)
    riveted(d, occ)
    for b in SHEET:
        part(d, occ, b, sizes)
    sheets = d.run("drawing.inspect")["sheets"]
    pages = [export(d, s["id"], s["name"]) for s in sheets]
    findings = d.run("drawing.check")["counts"]
    print("drawing check:", json.dumps(findings))
    run("drawing.close")
    run("file.save", {"path": DESIGN, "overwrite": True})
    os.remove(fresh)
    foot(sc, pages)
    subprocess.run(["rsvg-convert", "-f", "pdf", "-o", PDF] + pages, check=True)
    subprocess.run(["rsvg-convert", "-f", "pdf", "-o", FOOT_PDF, pages[-1]], check=True)
    print("wrote", PDF, "and", FOOT_PDF)


if __name__ == "__main__":
    main()
