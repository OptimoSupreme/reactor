"""Build the Reactor Mk I in SolidCraft: three folded sheet metal parts and the bought-in parts as blocks.

  python3 mechanical/mk1.py            build, save, check, export flat patterns and renders

Talks to the running desktop app over its MCP bridge. SOLIDCRAFT_MCP holds the
command line that starts the bridge, for example "solidcraft-cli mcp --connect
127.0.0.1:27901 --allow-path .".

Axes: X from the rear panel's inside face to the front, Y from the CPU-side
edge of the core to the PSU side, Z up from the top of the bottom panel.
All mm. Sources for the bought-in dimensions are in docs/parts.md.
"""
import json
import math
import os
import shlex
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DESIGN = os.path.join(REPO, "mechanical", "reactor-mk-i.sc")
EXPORT = os.path.join(REPO, "mechanical", "export")
IMAGES = os.path.join(REPO, "docs", "images")

T = 1.2            # sheet
GAP = 0.3          # between sliding or nested sheet faces
LX, LY, LZ = 174.0, 204.0, 240.0   # cavity: rear to front, between the side lips, bottom to top panel
FLANGE = 10.0
OLIVE = "#5a6332"

# Y stack from the CPU side
PLENUM = 20.0
CPU_FAN = 16.0     # NF-A12x15 with its pads
HEATSINK = 49.0    # placeholder, see docs/parts.md
BOARD_Y = PLENUM + CPU_FAN + HEATSINK          # component face of the board
PCB = 1.6
STANDOFF = 10.0    # clears the M.2 holder, 8.4 under the board
TRAY_Y = BOARD_Y + PCB + STANDOFF              # tray face the standoffs sit in
PSU_Y = TRAY_Y + T
PSU = (140.0, 86.0, 150.0)                     # along X, Y, Z as it stands here

# Z stack
FAN, FAN_T, FAN_HOLES = 140.0, 25.0, 124.5
BASE = 37.0        # bottom fan plus room for its air to spread under the shelf
SHELF_Z = BASE + T
BOARD_Z = 40.0     # bottom edge of the board
BOARD_X = 2.0      # rear edge of the board; its ports overhang 1.8
BOARD = 170.0
TRAY_TOP = LZ - FAN_T - 3                      # between its ears, under the top fan
CENTRE = (LX / 2, LY / 2)

# mesh: hexagons 10.4 across flats. The pitches put a cell on each fan screw, which squeezes the
# rows 4 % from a true honeycomb. SolidCraft's flat pattern gave up on a finer mesh (7 across flats).
HEX_NX, HEX_NY = 5, 6
HEX_AF = 10.4
PITCH_X = FAN_HOLES / 2 / HEX_NX
PITCH_Y = FAN_HOLES / 2 / HEX_NY
HEX_K = PITCH_Y / (PITCH_X * math.sqrt(3) / 2)
MESH_EDGE = 10.5   # cell centres stay this far inside the cavity

FEET = [(14, 26), (LX - 14, 26), (14, LY - 26), (LX - 14, LY - 26)]
FOOT_PAD = 15.0    # solid land around each foot
SWITCH = (14.0, 14.0)   # 12 mm vandal switch, Y and Z on the front panel: bottom left seen from the front
FRONT_LIP = 6.0    # bottom panel's front lip, kept low so the switch's nut clears it
SLOTS = [(3.8, 12.2), (161.8, 170.2)]          # tray tabs through the top panel, X ranges

# shell
SHELL_Y0, SHELL_Y1 = -2 * T - GAP, LY + 2 * T + GAP
SHELL_Z0, SHELL_Z1 = -2 * T - GAP, LZ + 2 * T + GAP
SHELL_XF = LX + 2 * T + GAP
SHELL_FOOT = 14.0  # bottom flanges, wide enough for the thumbscrew
SCREW = (10.0, 6.0)   # thumbscrew, X and Y, up through the shell's flange into a nut in the bottom panel

# board holes from Framework's drawing, measured from the port edge and the top edge
BOARD_HOLES = [(33.02, 6.17), (165.10, 6.17), (10.16, 163.65), (165.10, 163.65)]
# ATX rear face, both ways up: along the 150 side, along the 86 side
PSU_HOLES = [(6, 80), (144, 80), (120, 6), (6, 16)]
PSU_HOLES += [(150 - a, 86 - b) for a, b in PSU_HOLES]


class Bridge:
    ENV = "SOLIDCRAFT_MCP"

    def __init__(self):
        cmd = os.environ.get(self.ENV)
        if not cmd:
            raise SystemExit("set %s to the command that starts the MCP bridge" % self.ENV)
        self.p = subprocess.Popen(shlex.split(cmd), stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        self.n = 0
        self.rpc("initialize", {"protocolVersion": "2024-11-05", "capabilities": {},
                                "clientInfo": {"name": "mk1", "version": "0"}})
        self.send({"jsonrpc": "2.0", "method": "notifications/initialized"})

    def send(self, m):
        self.p.stdin.write(json.dumps(m) + "\n")
        self.p.stdin.flush()

    def rpc(self, method, params):
        self.n += 1
        self.send({"jsonrpc": "2.0", "id": self.n, "method": method, "params": params})
        while True:
            line = self.p.stdout.readline()
            if not line:
                raise SystemExit("bridge closed")
            if line.startswith("{"):
                r = json.loads(line)
                if r.get("id") == self.n:
                    return r

    def call(self, tool, args=None):
        r = self.rpc("tools/call", {"name": tool, "arguments": args or {}})
        if "error" in r:
            raise SystemExit("%s: %s" % (tool, r["error"]["message"]))
        text = "".join(c.get("text", "") for c in r["result"].get("content", []))
        if r["result"].get("isError"):
            raise SystemExit("%s: %s" % (tool, text[:1500]))
        try:
            return json.loads(text)
        except ValueError:
            return text

    def batch(self, steps, what):
        r = self.call("batch", {"commands": [{"command": c, "params": p} for c, p in steps]})
        if not isinstance(r, dict) or not r.get("ok"):
            raise SystemExit("%s failed: %s" % (what, json.dumps(r)[:1500]))
        for s in r["results"]:
            if isinstance(s, dict) and s.get("warning"):
                print("  warning in %s: %s" % (what, s["warning"]))
        return r["results"]


def plane(origin, x_dir, y_dir):
    return {"origin": origin, "x_dir": x_dir, "y_dir": y_dir}


def cut(name, pl, shapes, depth, targets):
    """Cut rectangles (x0, y0, x1, y1), circles (x, y, d) and hexagons ("hex", x, y) through the targets."""
    steps = [("sketch.create", {"plane": pl, "name": name})]
    r = HEX_AF / math.sqrt(3)
    for s in shapes:
        if s[0] == "hex":
            pts = [[round(s[1] + r * math.sin(math.radians(60 * k)), 4),
                    round(s[2] + HEX_K * r * math.cos(math.radians(60 * k)), 4)] for k in range(6)]
            steps.append(("sketch.line", {"points": pts, "closed": True, "connect": False, "infer": False}))
        elif len(s) == 4:
            steps.append(("sketch.rectangle.two_point", {"p0": [s[0], s[1]], "p1": [s[2], s[3]], "connect": False}))
        else:
            steps.append(("sketch.circle.center", {"center": [s[0], s[1]], "diameter": s[2], "connect": False}))
    steps += [("sketch.finish", {}),
              ("solid.extrude", {"sketch": name, "distance": str(depth), "operation": "cut", "targets": targets})]
    return steps


def mesh(keep_out):
    """Hexagons over the whole panel, with a round hole in place of the cell at each fan screw."""
    cx, cy = CENTRE
    out = []
    nj = int((LY / 2 - MESH_EDGE) / PITCH_Y)
    ni = int((LX / 2 - MESH_EDGE) / PITCH_X) + 1
    for j in range(-nj, nj + 1):
        for i in range(-ni, ni + 1):
            x = cx + (i + (0.5 if j % 2 else 0)) * PITCH_X
            y = cy + j * PITCH_Y
            if abs(i) == HEX_NX and abs(j) == HEX_NY:
                out.append((round(x, 4), round(y, 4), 4.5))
            elif not (MESH_EDGE <= x <= LX - MESH_EDGE) or keep_out(x, y):
                continue
            else:
                out.append(("hex", x, y))
    return out


def box(name, color, x0, x1, y0, y1, z0, z1, opacity=1):
    return [("solid.box", {"length": round(x1 - x0, 3), "width": round(y1 - y0, 3), "height": round(z1 - z0, 3),
                           "corner": [round(x0, 3), round(y0, 3), round(z0, 3)], "body_name": name,
                           "operation": "new"}),
            ("appearance.assign", {"bodies": [name], "color": color, "opacity": opacity})]


XY = plane([0, 0, -3], [1, 0, 0], [0, 1, 0])           # looks up through the bottom
TOP = plane([0, 0, LZ - 3], [1, 0, 0], [0, 1, 0])
REAR = plane([-4, 0, 0], [0, 1, 0], [0, 0, 1])         # sketch (Y, Z), cuts toward the front
TRAY = plane([0, TRAY_Y + 3, 0], [1, 0, 0], [0, 0, 1])  # sketch (X, Z), cuts toward the CPU side


def core():
    """Bottom, rear and top in one part; both fans, the tray and the PSU hang off it."""
    w = LY + 2 * T
    zt, xf = LZ + T, LX + T
    s = [("sketch.create", {"plane": "XZ", "offset": str(-T), "name": "core-profile"}),
         ("sketch.line", {"points": [[xf, -zt], [-T, -zt], [-T, T], [xf, T]]}),
         ("sketch.finish", {}),
         ("sheet.flange", {"sketch": "core-profile", "curves": ["l1", "l2", "l3"], "distance": str(w),
                           "body_name": "core"}),
         ("sheet.flange", {"body": "core", "height": str(FLANGE), "flip": True, "edges": [
             [xf, LY / 2, zt], {"point": [xf, LY / 2, -T], "height": str(FRONT_LIP)},
             [LX / 2, -T, zt], [LX / 2, LY + T, zt], [LX / 2, -T, -T], [LX / 2, LY + T, -T],
             [-T, -T, LZ / 2], [-T, LY + T, LZ / 2]]})]
    # rear panel: port opening (placeholder), PSU opening and screws, thumbscrew
    pz, py = SHELF_Z, PSU_Y
    rear = [(51, 46, 85.5, 195), (py + 11, pz + 11, py + 75, pz + 139)]
    rear += [(py + b, pz + a, 4.0) for a, b in PSU_HOLES]
    s += cut("rear-cuts", REAR, rear, 5, ["core"])
    pad = lambda x, y: any(math.hypot(x - fx, y - fy) < FOOT_PAD + HEX_AF / 2 for fx, fy in FEET)
    s += cut("bottom-mesh", XY, mesh(pad) + [(x, y, 4.3) for x, y in FEET] + [SCREW + (5.41,)], 5, ["core"])
    slot = lambda x, y: abs(y - TRAY_Y - T / 2) < 7.5 and any(a - 6 < x < b + 6 for a, b in SLOTS)
    s += cut("top-mesh", TOP, mesh(slot) + [(a, TRAY_Y - 0.2, b, PSU_Y + 0.2) for a, b in SLOTS], 6, ["core"])
    return s


def tray():
    x0, x1 = GAP, LX - GAP
    s = [("sketch.create", {"plane": plane([x0, 0, 0], [0, 1, 0], [0, 0, 1]), "name": "tray-profile"}),
         ("sketch.line", {"points": [[PSU_Y, LZ + T], [PSU_Y, SHELF_Z], [PSU_Y + PSU[1] - 0.5, SHELF_Z]]}),
         ("sketch.finish", {}),
         ("sheet.flange", {"sketch": "tray-profile", "curves": ["l1", "l2"], "distance": str(x1 - x0),
                           "body_name": "tray"})]
    # cut down under the top fan; the ears left at each end reach the top panel and end in a tab through it
    (a0, a1), (b0, b1) = SLOTS
    s += cut("tray-top", TRAY, [(14, TRAY_TOP, 160, LZ + 3)], 5, ["tray"])
    trims = [(-1, LZ - 2.5, a0 + 0.2, LZ + 3), (a1 - 0.2, LZ, 15, LZ + 3),
             (159, LZ, b0 + 0.2, LZ + 3), (b1 - 0.2, LZ, LX + 1, LZ + 3)]
    s += cut("tray-ears", TRAY, trims, 5, ["tray"])
    s += [("sheet.flange", {"body": "tray", "height": str(FLANGE + 2), "edges": [[x0, TRAY_Y, 125]]})]
    holes = [(BOARD_X + u, BOARD_Z + BOARD - v, 4.22) for u, v in BOARD_HOLES]
    s += cut("tray-cuts", TRAY, holes + [(142, 60, 160, 130)], 5, ["tray"])
    return s


def shell():
    """Front and both sides, plain. Slides on from the front; one thumbscrew up through its bottom flange."""
    y0, y1, z0, z1 = SHELL_Y0, SHELL_Y1, SHELL_Z0, SHELL_Z1
    s = [("sketch.create", {"plane": plane([0, 0, z0], [1, 0, 0], [0, 1, 0]), "name": "shell-profile"}),
         ("sketch.line", {"points": [[-T, y1], [SHELL_XF, y1], [SHELL_XF, y0], [-T, y0]]}),
         ("sketch.finish", {}),
         ("sheet.flange", {"sketch": "shell-profile", "curves": ["l1", "l2", "l3"],
                           "distance": str(z1 - z0), "body_name": "shell"}),
         ("sheet.flange", {"body": "shell", "height": str(FLANGE), "flip": True, "edges": [
             [LX / 2, y0, z1], [LX / 2, y1, z1]]}),
         ("sheet.flange", {"body": "shell", "height": str(SHELL_FOOT), "flip": True, "edges": [
             [LX / 2, y0, z0], [LX / 2, y1, z0]]})]
    s += cut("shell-switch", plane([LX, 0, 0], [0, 1, 0], [0, 0, 1]), [SWITCH + (12.2,)], 5, ["shell"])
    s += cut("shell-screw", plane([0, 0, z0 - 0.5], [1, 0, 0], [0, 1, 0]), [SCREW + (4.5,)], T + 0.7, ["shell"])
    return s


def rivets():
    """Holes shared by the tray's rear flange and the rear panel."""
    return cut("rear-rivets", REAR, [(TRAY_Y - 6.5, z, 3.3) for z in (60, 125, 190)], 6.5, ["core", "tray"])


def bought_in():
    bx, bz = BOARD_X, BOARD_Z
    hx, hz = bx + 18.54, bz + BOARD - 136.06     # fan duct square from Framework's drawing
    cx, cz = hx + 63.1, hz + 63.1
    fx, fy = CENTRE
    s = box("ref-mainboard", "#2f7d4f", bx, bx + BOARD, BOARD_Y, BOARD_Y + PCB, bz, bz + BOARD)
    s += box("ref-heatsink", "#b8bcc2", hx, hx + 126.2, BOARD_Y - HEATSINK, BOARD_Y, hz, hz + 126.2)
    s += box("ref-cpu-fan", "#c9a27a", cx - 60, cx + 60, PLENUM, PLENUM + CPU_FAN, cz - 60, cz + 60)
    s += box("ref-rear-ports", "#7d8791", 0.2, 20, BOARD_Y - 31.1, BOARD_Y, bz + 8, bz + 152)
    s += box("ref-psu-atx", "#2b2e33", 0, PSU[0], PSU_Y, PSU_Y + PSU[1], SHELF_Z, SHELF_Z + PSU[2])
    s += box("ref-fan-bottom", "#c9a27a", fx - 70, fx + 70, fy - 70, fy + 70, 0, FAN_T)
    s += box("ref-fan-top", "#c9a27a", fx - 70, fx + 70, fy - 70, fy + 70, LZ - FAN_T, LZ)
    for i, (u, v) in enumerate(BOARD_HOLES):
        x, z = bx + u, bz + BOARD - v
        s += box("ref-standoff-%d" % (i + 1), "#d0d0d0", x - 2.7, x + 2.7, BOARD_Y + PCB, TRAY_Y, z - 2.7, z + 2.7)
    s += [("solid.cylinder", {"diameter": 12, "height": 24, "base": [SHELL_XF - 24, SWITCH[0], SWITCH[1]], "axis": "X",
                              "body_name": "ref-switch", "operation": "new"}),
          ("solid.cylinder", {"diameter": 15, "height": 2, "base": [SHELL_XF, SWITCH[0], SWITCH[1]], "axis": "X",
                              "operation": "join", "targets": ["ref-switch"]}),
          ("solid.cylinder", {"diameter": 16, "height": 3, "base": [LX + T + GAP - 3, SWITCH[0], SWITCH[1]], "axis": "X",
                              "operation": "join", "targets": ["ref-switch"]}),
          ("appearance.assign", {"bodies": ["ref-switch"], "color": "#c8c8c8"})]
    for i, (x, y) in enumerate(FEET):
        n = "foot-%d" % (i + 1)
        s += [("solid.cylinder", {"diameter": 24, "height": 2, "base": [x, y, -T - 2], "body_name": n,
                                  "operation": "new"}),
              ("solid.cone", {"diameter": 21, "top_diameter": 15, "height": -16, "base": [x, y, -T - 2],
                              "operation": "join", "targets": [n]}),
              ("appearance.assign", {"bodies": [n], "color": OLIVE})]
    return s


SHEET = ["core", "tray", "shell"]


def main():
    sc = Bridge()
    os.makedirs(EXPORT, exist_ok=True)
    os.makedirs(IMAGES, exist_ok=True)
    sc.call("new_design")
    sc.batch([("sheet.manage_rules", {"name": "CRS 1.2", "thickness": "%g mm" % T, "k_factor": "0.44",
                                      "bend_radius": "Thickness", "active": True})], "rule")
    for name, steps in (("core", core()), ("tray", tray()), ("shell", shell()), ("rivets", rivets()),
                        ("bought-in", bought_in())):
        sc.batch(steps, name)
        print("built", name)
    sc.batch([("appearance.assign", {"bodies": SHEET, "color": OLIVE})], "paint")
    sc.call("save", {"path": DESIGN})

    m = sc.call("measure", {"summary": True})
    lo = [min(b["bbox"]["min"][i] for b in m["bodies"] if b["name"] in SHEET) for i in range(3)]
    hi = [max(b["bbox"]["max"][i] for b in m["bodies"] if b["name"] in SHEET) for i in range(3)]
    size = [hi[i] - lo[i] for i in range(3)]
    for b in m["bodies"]:
        if b["name"] in SHEET:
            print("%-8s x %.1f..%.1f  y %.1f..%.1f  z %.1f..%.1f  %.0f g in steel" % (
                b["name"], b["bbox"]["min"][0], b["bbox"]["max"][0], b["bbox"]["min"][1], b["bbox"]["max"][1],
                b["bbox"]["min"][2], b["bbox"]["max"][2], b["volume_mm3"] * 7.85e-3))
    print("case without feet: %.1f x %.1f x %.1f mm, %.2f L" % (size[0], size[1], size[2],
                                                                 size[0] * size[1] * size[2] / 1e6))

    r = sc.call("execute", {"command": "inspect.interference", "params": {}})
    print("interference: %d overlapping pairs, %d not checked" % (len(r.get("interferences", [])),
                                                                  len(r.get("unchecked", []))))
    for i in r.get("interferences", []):
        print("  overlap %s" % json.dumps(i)[:300])
    for i in r.get("unchecked", []):
        print("  not checked: %s / %s" % (i.get("a"), i.get("b")))

    for b in SHEET:
        f = sc.call("execute", {"command": "sheet.flat_pattern", "params": {"body": b}})
        sc.call("execute", {"command": "sheet.export_dxf", "params": {
            "body": b, "path": os.path.join(EXPORT, b + ".dxf"), "bend_notes": True}})
        sc.call("execute", {"command": "sheet.export_bend_table", "params": {
            "body": b, "path": os.path.join(EXPORT, b + "-bends.csv")}})
        print("%-8s flat %.1f x %.1f mm, %d bends, %d cut-outs" % (
            b, f["flat_size_mm"][0], f["flat_size_mm"][1], len(f.get("bends", [])), len(f.get("cutouts", []))))


if __name__ == "__main__":
    main()
