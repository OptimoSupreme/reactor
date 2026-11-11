"""Build the Reactor Mk I in SolidCraft: four folded sheet metal parts and the bought-in parts as blocks.

  python3 mechanical/mk1.py            build, save, check and export flat patterns
  python3 mechanical/mk1.py --board    the same case with Framework's model of the board in it, saved
                                       outside the repo, and a report of how the board fits

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
# Framework's own model of the board (CC BY 4.0), from github.com/FrameworkComputer/Framework-Desktop,
# Mainboard/FRAMEWORK_DESKTOP_MAIN_PCB_V01.stp. It is 73 MB and makes the design 26 MB and slow to
# rebuild, so both stay outside the repo and the committed design draws the board as a block.
MAINBOARD_STEP = os.path.expanduser("~/.cache/reactor/framework-desktop/FRAMEWORK_DESKTOP_MAIN_PCB_V01.stp")
DESIGN_WITH_BOARD = os.path.expanduser("~/.cache/reactor/reactor-mk-i-with-board.sc")
WITH_BOARD = "--board" in sys.argv
IMAGES = os.path.join(REPO, "docs", "images")

T = 1.2            # sheet
GAP = 0.3          # between sliding or nested sheet faces
LX, LY, LZ = 252.0, 128.0, 210.0   # cavity: rear to front, between the side lips, bottom to top panel
FLANGE = 10.0
SIDE_LIP = 14.0    # top and bottom panels' side lips, tall enough to fasten the tray to
OLIVE = "#5a6332"

# Y stack: the tray stands against the far side wall and the board faces the other
TRAY_Y = LY - GAP - 0.2 - T                    # tray face the standoffs sit in
STANDOFF = 10.0    # clears the M.2 holder, 8.4 under the board
PCB = 1.6
BOARD_Y = TRAY_Y - STANDOFF - PCB              # component face of the board
HEATSINK = 49.0    # placeholder, see docs/parts.md
CPU_FAN = 16.0     # NF-A12x15 with its pads

# slim 120 mm fans, two in the bottom and one in the top
FAN, FAN_T, FAN_HOLES = 120.0, 15.0, 105.0
BOARD_Z = FAN_T + 7.0                          # bottom edge of the board
BOARD_X = 12.27 - 10.16   # rear edge of the board: the rear holes sit 0.483 in from the panel (ATX figure 4)
BOARD = 170.0

# mesh: hexagons 9.6 across flats. The pitches put a cell on every fan screw, which stretches the
# rows 4 % from a true honeycomb. SolidCraft's flat pattern gives up on a much finer mesh.
HEX_NX, HEX_NY = 4.5, 5
HEX_AF = 9.6
PITCH_X = FAN_HOLES / 2 / HEX_NX
PITCH_Y = FAN_HOLES / 2 / HEX_NY
HEX_K = PITCH_Y / (PITCH_X * math.sqrt(3) / 2)
MESH_EDGE = 10.5   # cell centres stay this far inside the cavity
BOTTOM_FANS = [(LX / 2 - 5.5 * PITCH_X, LY / 2), (LX / 2 + 5.5 * PITCH_X, LY / 2)]
TOP_FAN = (89.0, LY / 2)

# SFX supply standing in front of the board: fan toward the board, exhaust and mains inlet up
PSU_X = BOARD_X + BOARD + 8.0                  # no room for plugs on a board's front edge, by choice
PSU = (63.5, 125.0, 100.0)                     # along X, Y, Z as it stands here
PSU_Y = 0.7
PSU_TOP = LZ - 35.0                            # room above for a right-angle mains plug
PSU_HOLES = [(6.0, 6.0), (6.0, 119.0), (57.5, 6.0), (57.5, 119.0)]   # along X, Y from the PSU's corner
BRACKET_X = (PSU_X - 1.0, PSU_X + PSU[0] + 2.5)
BRACKET_FLANGE = 11.6
STUDS = [(x, y) for x in (BRACKET_X[0] + 6, BRACKET_X[1] - 6) for y in (30.0, 98.0)]   # flush studs in the top panel
GROMMET = (20.0, LZ - 17.0, 22.0)              # hole in the rear baffle for a cable grommet: Y, Z, diameter

FEET = [(16, 24), (LX - 16, 24), (16, LY - 24), (LX - 16, LY - 24)]
FOOT_PAD = 13.0    # solid land around each foot

# shell
SHELL_Y0, SHELL_Y1 = -2 * T - GAP, LY + 2 * T + GAP
SHELL_Z0, SHELL_Z1 = -2 * T - GAP, LZ + 2 * T + GAP
SHELL_XF = LX + 2 * T + GAP
SHELL_FOOT = 14.0  # bottom flanges, wide enough for the thumbscrew
SCREW = (LX / 2, 6.0)   # thumbscrew, X and Y, up through the shell's flange into a nut between the bottom fans
SWITCH = (14.0, LZ - 14.0)   # 12 mm vandal switch, Y and Z on the front panel: top left seen from the front
INLET = (26.0, FAN_T + 13.0)   # IEC C14 inlet lying flat, low on the rear panel: Y and Z of its centre

# Rear I/O aperture, ATX specification 2.03 figure 4: 6.25 x 1.75 in, its long side running from 2.44
# past the board's edge on the port side, its lower side 0.088 in below the underside of the board.
IO_Z = (BOARD_Z + BOARD - 156.31, BOARD_Z + BOARD + 2.44)
IO_Y = (TRAY_Y - STANDOFF + 2.24 - 44.45, TRAY_Y - STANDOFF + 2.24)

# Mini-ITX holes (C, F, H, J), measured from the port edge and from the edge the aperture overhangs
BOARD_HOLES = [(33.02, 6.17), (165.10, 6.17), (10.16, 163.65), (165.10, 163.65)]


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


def mesh(fans, keep_out):
    """Hexagons over the whole panel, with a round hole in place of the cell at each fan screw."""
    ax, ay = fans[0]
    h = FAN_HOLES / 2
    screws = [(fx + i * h, fy + j * h) for fx, fy in fans for i in (-1, 1) for j in (-1, 1)]
    out = []
    for j in range(-int(LY / PITCH_Y), int(LY / PITCH_Y) + 1):
        for i in range(-int(LX / PITCH_X), int(LX / PITCH_X) + 1):
            x = ax + (i + (0.5 if j % 2 else 0)) * PITCH_X
            y = ay + j * PITCH_Y
            if any(math.hypot(x - sx, y - sy) < 0.05 for sx, sy in screws):
                out.append((round(x, 4), round(y, 4), 4.5))
            elif (MESH_EDGE <= x <= LX - MESH_EDGE and MESH_EDGE <= y <= LY - MESH_EDGE
                  and not keep_out(x, y)):
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
TRAY = plane([0, TRAY_Y + T + 3, 0], [1, 0, 0], [0, 0, 1])   # sketch (X, Z), cuts toward the board
SIDE = plane([0, LY + T + 1, 0], [1, 0, 0], [0, 0, 1])       # the same from outside the side lips


def near(points, r):
    return lambda x, y: any(math.hypot(x - px, y - py) < r for px, py in points)


def core():
    """Bottom, rear and top in one part; the fans, the tray and the PSU bracket hang off it."""
    w = LY + 2 * T
    zt, xf = LZ + T, LX + T
    lip = lambda p: {"point": p, "height": str(SIDE_LIP)}
    s = [("sketch.create", {"plane": "XZ", "offset": str(-T), "name": "core-profile"}),
         ("sketch.line", {"points": [[xf, -zt], [-T, -zt], [-T, T], [xf, T]]}),
         ("sketch.finish", {}),
         ("sheet.flange", {"sketch": "core-profile", "curves": ["l1", "l2", "l3"], "distance": str(w),
                           "body_name": "core"}),
         ("sheet.flange", {"body": "core", "height": str(FLANGE), "flip": True, "edges": [
             [xf, LY / 2, zt], [xf, LY / 2, -T],
             lip([LX / 2, -T, zt]), lip([LX / 2, LY + T, zt]), lip([LX / 2, -T, -T]), lip([LX / 2, LY + T, -T]),
             [-T, -T, LZ / 2], [-T, LY + T, LZ / 2]]})]
    # rear panel: the standard I/O aperture and the mains inlet with its two screws
    iy, iz = INLET
    rear = [(IO_Y[0], IO_Z[0], IO_Y[1], IO_Z[1]), (iy - 14, iz - 10, iy + 14, iz + 10),
            (iy - 20, iz, 3.4), (iy + 20, iz, 3.4)]
    s += cut("rear-cuts", REAR, rear, 5, ["core"])
    pad = near(FEET, FOOT_PAD + HEX_AF / 2)
    nut = near([SCREW], 9)
    s += cut("bottom-mesh", XY, mesh(BOTTOM_FANS, lambda x, y: pad(x, y) or nut(x, y))
             + [(x, y, 4.0) for x, y in FEET] + [SCREW + (5.41,)], 5, ["core"])
    s += cut("top-mesh", TOP, top_mesh() + [(x, y, 3.0) for x, y in STUDS], 6, ["core"])
    # the top front lip steps back behind the switch so its nut has room
    sy, sz = SWITCH
    s += cut("switch-notch", plane([LX - 1.5, 0, 0], [0, 1, 0], [0, 0, 1]), [(sy - 10, sz - 2, sy + 10, sz + 9.5)], 3.5,
             ["core"])
    return s


def top_mesh():
    return mesh([TOP_FAN], near(STUDS, 9))


def tray():
    """A flat plate the length of the case against the side wall. No flange at the rear: the I/O
    aperture's keepout reaches to within 5 mm of it."""
    x0, x1 = GAP, LX - GAP
    s = [("sketch.create", {"plane": plane([x0, 0, 0], [0, 1, 0], [0, 0, 1]), "name": "tray-profile"}),
         ("sketch.line", {"points": [[TRAY_Y, GAP], [TRAY_Y, LZ - GAP]]}),
         ("sketch.finish", {}),
         ("sheet.flange", {"sketch": "tray-profile", "curves": ["l1"], "distance": str(x1 - x0),
                           "body_name": "tray"})]
    holes = [(BOARD_X + u, BOARD_Z + BOARD - v, 4.22) for u, v in BOARD_HOLES]
    s += cut("tray-cuts", TRAY, holes, 5, ["tray"])
    return s


def bracket():
    """A channel hung from the top panel. The PSU screws up against its underside, exhaust face up, and its
    two walls shut the space above the PSU off from the rest of the case, so the exhaust can only leave
    through the top mesh. The shell's side and the tray close the ends."""
    zt = LZ - 0.1
    ya, yb = 0.4, TRAY_Y - GAP
    xr, xf = BRACKET_X
    f = BRACKET_FLANGE
    s = [("sketch.create", {"plane": plane([0, yb, 0], [1, 0, 0], [0, 0, 1]), "name": "bracket-profile"}),
         ("sketch.line", {"points": [[xf - f, zt], [xf, zt], [xf, PSU_TOP], [xr, PSU_TOP], [xr, zt], [xr + f, zt]]}),
         ("sketch.finish", {}),
         ("sheet.flange", {"sketch": "bracket-profile", "curves": ["l1", "l2", "l3", "l4", "l5"],
                           "distance": str(yb - ya), "body_name": "bracket"})]
    web = [(PSU_X + 8, PSU_Y + 12, PSU_X + 55.5, PSU_Y + 113)]
    web += [(PSU_X + a, PSU_Y + b, 4.0) for a, b in PSU_HOLES]
    s += cut("bracket-web", plane([0, 0, PSU_TOP - 2], [1, 0, 0], [0, 1, 0]), web, 5, ["bracket"])
    # the flanges under the top panel get the panel's own hexagons, so they cover none of the mesh
    # (a cell that reaches over a wall's bend is left alone: the wall is under it either way)
    h, clear = HEX_AF / 2, 2 * T + 0.2
    under = [c for c in top_mesh() if c[0] == "hex" and (xr + clear <= c[1] - h < xr + f or xf - f < c[1] + h <= xf - clear)]
    s += cut("bracket-top", TOP, under + [(x, y, 3.4) for x, y in STUDS], 2.95, ["bracket"])
    s += cut("bracket-cables", plane([xr - 2, 0, 0], [0, 1, 0], [0, 0, 1]), [GROMMET], 4, ["bracket"])
    s += cut("bracket-switch", plane([xf - 3, 0, 0], [0, 1, 0], [0, 0, 1]), [SWITCH + (15.0,)], 4, ["bracket"])
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
    """Holes shared by the tray and what it is fastened to: the rear panel's side flange and the side lips
    of the top and bottom panels, all of them under the shell."""
    pts = [(x, z, 3.3) for x in (40, LX / 2, LX - 40) for z in (7, LZ - 8)] + [(5.0, z, 3.3) for z in (40, 105, 170)]
    return cut("tray-rivets", SIDE, pts, 4.6, ["core", "tray"])


def bought_in():
    bx, bz = BOARD_X, BOARD_Z
    hx, hz = bx + 18.54, bz + BOARD - 136.06     # fan duct square from Framework's drawing
    cx, cz = hx + 63.1, hz + 63.1
    hy = BOARD_Y - HEATSINK
    if WITH_BOARD:
        # The file has the board in its XZ plane, parts toward +Y, ports along its low-Z edge, with
        # the board's top face at y 10.9 and its corners at x -178.6..-8.6, z 1.7..171.7.
        s = [("file.insert_step", {"path": MAINBOARD_STEP, "name": "framework-mainboard", "matrix": [
            0, 0, 1, bx - 1.7, 0, -1, 0, BOARD_Y + 10.9, 1, 0, 0, bz + 178.6]})]
    else:
        s = box("ref-mainboard", "#2f7d4f", bx, bx + BOARD, BOARD_Y, BOARD_Y + PCB, bz, bz + BOARD)
        s += box("ref-rear-ports", "#7d8791", 0.2, 20, BOARD_Y - 31.1, BOARD_Y, bz + 11.5, bz + 143.9)
    s += box("ref-heatsink", "#b8bcc2", hx, hx + 126.2, hy, BOARD_Y - 4, hz, hz + 126.2)
    s += box("ref-cpu-fan", "#c9a27a", cx - 60, cx + 60, hy - CPU_FAN, hy, cz - 60, cz + 60)
    s += box("ref-psu-sfx", "#2b2e33", PSU_X, PSU_X + PSU[0], PSU_Y, PSU_Y + PSU[1], PSU_TOP - PSU[2], PSU_TOP)
    s += box("ref-mains-inlet", "#2b2e33", 0, 30, INLET[0] - 14, INLET[0] + 14, INLET[1] - 10, INLET[1] + 10)
    for i, (fx, fy) in enumerate(BOTTOM_FANS):
        s += box("ref-fan-bottom-%d" % (i + 1), "#c9a27a", fx - 60, fx + 60, fy - 60, fy + 60, 0, FAN_T)
    fx, fy = TOP_FAN
    s += box("ref-fan-top", "#c9a27a", fx - 60, fx + 60, fy - 60, fy + 60, LZ - FAN_T, LZ)
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
        s += [("solid.cylinder", {"diameter": 20, "height": 2, "base": [x, y, -T - 2], "body_name": n,
                                  "operation": "new"}),
              ("solid.cone", {"diameter": 17, "top_diameter": 12, "height": -16, "base": [x, y, -T - 2],
                              "operation": "join", "targets": [n]}),
              ("appearance.assign", {"bodies": [n], "color": OLIVE})]
    return s


SHEET = ["core", "tray", "bracket", "shell"]


def main():
    sc = Bridge()
    os.makedirs(EXPORT, exist_ok=True)
    os.makedirs(IMAGES, exist_ok=True)
    sc.call("new_design")
    sc.batch([("sheet.manage_rules", {"name": "CRS 1.2", "thickness": "%g mm" % T, "k_factor": "0.44",
                                      "bend_radius": "Thickness", "active": True})], "rule")
    for name, steps in (("core", core()), ("tray", tray()), ("bracket", bracket()), ("shell", shell()),
                        ("rivets", rivets()), ("bought-in", bought_in())):
        sc.batch(steps, name)
        print("built", name)
    sc.batch([("appearance.assign", {"bodies": SHEET, "color": OLIVE})], "paint")
    sc.call("save", {"path": DESIGN_WITH_BOARD if WITH_BOARD else DESIGN})

    m = sc.call("measure", {"summary": True})
    if WITH_BOARD:
        return board_fit(sc, m)
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
    made = lambda i: any(str(i.get(k, "")).split(" ")[0] in SHEET for k in ("a", "b"))
    for i in filter(made, r.get("interferences", [])):
        print("  overlap %s / %s: %.1f mm3, box %s" % (i.get("a"), i.get("b"), i.get("volume_mm3", 0),
                                                         json.dumps(i.get("bbox"))[:160]))
    for i in filter(made, r.get("unchecked", [])):
        print("  not checked: %s / %s" % (i.get("a"), i.get("b")))
    print("  (pairs between two bought-in parts are not listed)")

    for b in SHEET:
        f = sc.call("execute", {"command": "sheet.flat_pattern", "params": {"body": b}})
        sc.call("execute", {"command": "sheet.export_dxf", "params": {
            "body": b, "path": os.path.join(EXPORT, b + ".dxf"), "bend_notes": True}})
        sc.call("execute", {"command": "sheet.export_bend_table", "params": {
            "body": b, "path": os.path.join(EXPORT, b + "-bends.csv")}})
        print("%-8s flat %.1f x %.1f mm, %d bends, %d cut-outs" % (
            b, f["flat_size_mm"][0], f["flat_size_mm"][1], len(f.get("bends", [])), len(f.get("cutouts", []))))


def board_fit(sc, m):
    """How Framework's model of the board sits in the case, from its bodies' extents and its holes."""
    ours = lambda n: n.split(" ")[0] in SHEET or n.startswith(("ref-", "foot-"))
    parts = [b for b in m["bodies"] if not ours(b["name"])]
    lo = [min(b["bbox"]["min"][i] for b in parts) for i in range(3)]
    hi = [max(b["bbox"]["max"][i] for b in parts) for i in range(3)]
    print("board and its parts: x %.2f..%.2f  y %.2f..%.2f  z %.2f..%.2f" % (lo[0], hi[0], lo[1], hi[1], lo[2], hi[2]))
    holes = sc.call("body_topology", {"body": "LFSP0_MB_PCB", "faces": "cylinders"})
    holes = [f for v in holes.values() if isinstance(v, list) for f in v if abs(f["radius"] - 1.98) < 0.01]
    for u, v in BOARD_HOLES:
        x, z = BOARD_X + u, BOARD_Z + BOARD - v
        off = min(math.hypot(f["origin"][0] - x, f["origin"][2] - z) for f in holes)
        print("standoff at x %.2f z %.2f: nearest board hole %.2f away" % (x, z, off))
    print("rear panel: nearest part %.2f inside it" % lo[0])
    for b in parts:
        a, c = b["bbox"]["min"], b["bbox"]["max"]
        if a[0] < 3 and "PCB" not in b["name"] and "EMN" not in b["name"]:
            # a connector's legs go through the board, so only its body above the board is compared
            print("  %-32s to aperture edges: %.1f above, %.1f at the board side, %.1f below, %.1f on top" % (
                b["name"][:32], a[1] - IO_Y[0], IO_Y[1] - min(c[1], BOARD_Y), a[2] - IO_Z[0], IO_Z[1] - c[2]))
    print("tray: nearest part %.2f from it" % (TRAY_Y - hi[1]))
    print("open side: tallest part %.1f above the board, %.1f from the shell" % (BOARD_Y - lo[1], lo[1] + T + GAP))
    print("bottom fans: lowest part %.1f above them" % (lo[2] - FAN_T))
    print("top fan: highest part %.1f below it" % (LZ - FAN_T - hi[2]))
    print("PSU fan face: %.1f from the nearest part" % (PSU_X - hi[0]))


if __name__ == "__main__":
    main()
