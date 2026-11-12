"""Build the Reactor Mk I in SolidCraft, as two designs.

  python3 mechanical/mk1.py            reactor-mk-i.sc: the five sheet metal parts alone, which is what a
                                       shop makes, with their flat patterns and bend tables; then the
                                       assembly: the same parts with the board, fans, power supply and
                                       every screw, nut and stud in place, a check for clashes and a
                                       report of how the board fits
  python3 mechanical/mk1.py --sheet    the sheet metal design and its exports only

The assembly holds Framework's model of the board and is too big for the repo, so it is saved beside
that model, outside it.

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
ASSEMBLY = os.path.expanduser("~/.cache/reactor/reactor-mk-i-with-board.sc")
WITH_BOARD = os.path.exists(MAINBOARD_STEP)    # without the model the board is drawn as a block
IMAGES = os.path.join(REPO, "docs", "images")

T = 1.2            # sheet
GAP = 0.3          # between nested sheet faces
SHELL_GAP = 0.5    # between the shell and the lips it slides over: two bent parts, each good to about 0.4
LX, LY, LZ = 251.3, 128.0, 210.0   # cavity: rear to front, between the side lips, bottom to top panel
FLANGE = 10.0
SIDE_LIP = 14.0    # side lips of the top, bottom and rear panels on the open side
JOIN_LIP = 17.0    # and on the tray's side: 14.6 of flat lip against the tray, room for a press tool or a spot weld
JOIN_IN = 9.5      # a joining fastener's centre from the panel its lip is folded from: 7 from the bend and from the lip's edge
EDGE = T + GAP     # a joined plate stops this far from the panel it meets, clear of the bend at that panel's edge
ROUND = 1.5        # radius on outside corners
OLIVE = "#5a6332"
BLACK = "#1b1b1b"
ZINC = "#c8c8c8"

# Every screw is the 6-32 hex washer head screw of PC cases and 3.5 in drives, apart from the M2 cap
# screws that hold the shell, ordinary self-tapping fan screws, and the mains inlet's countersunk M3s. Sizes of the pressed-in parts are PEM's, see docs/parts.md.
# The tray and the bulkhead are fixed to the core's lips with PEM SF-3-1.2 SpotFast fasteners, which end
# flush on both faces: the shell passes 0.3 to 0.5 outside the lips and the fans stand 2.8 inside the tray.
SF_HEAD, SF_TAIL = 3.0, 2.5   # holes in the lip and in the plate behind it
CLEAR_632 = 4.0    # clearance hole
LOOSE_632 = 4.5    # and where the two holes are on different bent parts
NUT_632 = 4.76     # hole for an S-632 nut, 5.6 or more from an edge
STUD_632 = 3.5     # hole for an FH-632 flush stud, 6.4 or more from an edge
STANDOFF_632 = 5.41   # hole for a BSO-632 standoff, 6.9 or more from an edge
SCREW_632 = 6.35   # the usual 1/4 in long
FAN_CLEAR = 5.0    # for a self-tapping fan screw, which cuts its own thread in the fan's frame
FAN_SCREW = 10.0
M3_CLEAR = 3.5

# Y stack: the tray stands against the far side wall and the board faces the other
TRAY_Y = LY - T                                # tray face the standoffs sit in; its other face is against the side lips
STANDOFF = 9.53    # BSO-632-12, 3/8 in: clears the M.2 holder, 8.4 under the board
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
# The bottom fans set the length of the case: 1.3 from the rear panel to clear the bend at its foot,
# 11 pitches apart so one mesh puts a cell on the screws of both, and 0.5 from the bulkhead.
BOTTOM_FANS = [(FAN / 2 + 1.3, LY / 2), (FAN / 2 + 1.3 + 11 * PITCH_X, LY / 2)]
TOP_FAN = (LX / 2 - 3.5 * PITCH_X, LY / 2)      # half pitches from the middle, so the mesh mirrors front to back

# SFX supply standing in front of the board: fan toward the board, exhaust and mains inlet up
PSU = (63.5, 125.0, 100.0)                     # along X, Y, Z as it stands here
# As far forward as it goes, 1.4 from the bulkhead: the heads of its front two screws still sit flat on
# the shelf, 0.7 short of the bend into the shelf's front flange. That leaves 13.1 to the board's edge.
PSU_X = LX - T - 1.39 - PSU[0]
PSU_Y = 0.7
PSU_TOP = LZ - 35.0                            # room above for a right-angle mains plug
# The three mounting holes of Intel's SFX12V guide, along X, Y from the PSU's corner: a pair at the tray's
# side and one at the open side, the end the guide draws the mains inlet at. With its fan toward the
# board, the SF450 and the Focus SGX-550 both have the inlet at the open side. The shelf has the same
# three mirrored as well, so that it takes a unit with all four corners threaded.
PSU_HOLES = [(6.0, 119.0), (57.5, 119.0), (31.7, 6.0)]
PSU_HOLES_SPARE = [(6.0, 6.0), (57.5, 6.0), (31.7, 119.0)]
# The PSU's weight goes to the floor through a bulkhead just inside the front, not into the top mesh.
BULKHEAD_X = (LX - T, LX)
LIP_TOP, LIP_BOTTOM = 18.5, 28.0               # front lips of the top and bottom panels, which the bulkhead is fixed to
BULKHEAD_JOINS = [(30.0, 20.0), (98.0, 20.0), (40.0, LZ - JOIN_IN), (98.0, LZ - JOIN_IN)]   # its fasteners to those lips, Y and Z
SHELF_X = (PSU_X - 1.0, BULKHEAD_X[0] - GAP)
# The tabs end at the corner of the cell diagonally in front of their screw's, so that cell's cut-out
# takes the tab's corner off at a slant and stops there, with no point left beyond it.
SHELF_FLANGE = round(TOP_FAN[0] + 10 * PITCH_X, 4) - SHELF_X[0]   # rounded as the cells' corners are
# The shelf comes out with the PSU on it, so it hangs on three flush studs in the bulkhead with nuts
# behind its front flange. A screw's head in front of the bulkhead would foul the shell, 1.5 away.
SHELF_STUDS = [(y, PSU_TOP + 7.5) for y in (22.0, 63.0, 104.0)]
STUD_LENGTH = 6.35   # FH-632-4
# two screws down through the top panel into nuts in the shelf's tabs: the fifth cell from the front
# in the outermost row on each side, the rows the fan screws are in
SHELF_SCREWS = [(TOP_FAN[0] + 9.5 * PITCH_X, LY / 2 + j * PITCH_Y) for j in (-HEX_NY, HEX_NY)]
# Hole in the shelf's rear wall for a cable grommet, behind the supply's inlet: Y, Z, diameter. Midway between the bend into the
# shelf below it and the relief slot beside the tab above it.
GROMMET = (33.0, (PSU_TOP + 2 * T + LZ - 0.1 - 2 * T - 3) / 2, 22.0)

FEET = [(17, 25), (LX - 17, 25), (17, LY - 25), (LX - 17, LY - 25)]   # clear of the fan screws' heads
FOOT_PAD = 12.0    # solid land around each foot: the nearest cell is 1.3 outside the foot's 20 mm flange
# A screw's head or a nut inside would sit under a fan's frame, so each foot turns onto a flush stud
# pressed into the bottom panel, pointing down.
FOOT_STUD = 9.53   # FH-632-6
FOOT_TAP, FOOT_TAP_DEPTH = 2.7, 12.0   # tap drill for 6-32, and deep enough for the whole stud
FOOT_RECESS, FOOT_RECESS_DEPTH = 9.0, 1.5   # recess underneath for a 3M SJ5076 bumper, 8.0 x 2.8

# shell
SHELL_Y0, SHELL_Y1 = -2 * T - SHELL_GAP, LY + 2 * T + SHELL_GAP
SHELL_Z0, SHELL_Z1 = -2 * T - SHELL_GAP, LZ + 2 * T + SHELL_GAP
SHELL_XF = LX + 2 * T + GAP
SHELL_RETURN = 9.5  # flanges over the top and under the bottom: narrow enough to pass the fan screws' heads
# A nub at each rear corner of the top and bottom panels, and a slot in each of the shell's flanges that
# runs onto it as the shell slides home, so the sides cannot be pulled outward: X and Y. Each nub is the
# head of an M2 socket cap screw (3.8 across, 2 tall) in a tapped hole, which any shop can make; pressed-in
# pins come too long and want more edge distance than the flange leaves.
PINS = [(6.0, 3.0), (6.0, LY - 3.0)]
PIN = 3.8
PIN_TAP = 1.6      # tap drill for M2
# The bottom corner on the open side has the same M2 screw the other way up instead of a nub: up through
# a hole in the flange into a thread in the bottom panel and tightened, which holds the shell on. It
# sits closer to the edge than the nubs so that its end clears the corner of the fan above it.
SCREW = (6.0, 2.5)
M2_CLEAR = 2.8
SLOT_CLEAR = 0.5   # each side of a nub in its slot
# 12 mm vandal switch, Y and Z: top left seen from the front. It is fixed in the bulkhead with its nut
# behind, and its head comes out through a larger hole in the shell, so the shell slides off over it.
SWITCH = (14.0, LZ - 14.0)
SWITCH_HOLE, SWITCH_SHELL, SWITCH_NUT = 12.0, 14.5, 16.0   # the head is 14
INLET = (28.0, FAN_T + 13.0)   # Schurter 6100-3 C14 inlet lying flat, low on the rear panel: Y and Z of its centre

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
    """Cut rectangles (x0, y0, x1, y1), circles (x, y, d), hexagons ("hex", x, y) and outlines
    ("poly", points) and rounded rectangles ("round", x0, y0, x1, y1, radius) through the targets."""
    steps = [("sketch.create", {"plane": pl, "name": name})]
    r = HEX_AF / math.sqrt(3)
    for s in shapes:
        if s[0] == "poly":
            steps.append(("sketch.line", {"points": s[1], "closed": True, "connect": False, "infer": False}))
        elif s[0] == "round":
            steps.append(("sketch.rectangle.rounded", {"p0": [s[1], s[2]], "p1": [s[3], s[4]], "radius": str(s[5]),
                                                       "connect": False}))
        elif s[0] == "hex":
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


def rounds(name, pl, corners, depth, targets, r=ROUND):
    """Round outside corners: each is (u, v, su, sv) in the sketch plane, su and sv pointing into the part."""
    steps = [("sketch.create", {"plane": pl, "name": name})]
    for u, v, su, sv in corners:
        steps += [("sketch.line", {"points": [[u, v + sv * r], [u - su, v + sv * r], [u - su, v - sv],
                                              [u + su * r, v - sv], [u + su * r, v]], "connect": False, "infer": False}),
                  ("sketch.arc.center_point", {"center": [u + su * r, v + sv * r], "start": [u + su * r, v],
                                               "sweep": -90 * su * sv, "connect": False})]
    steps += [("sketch.finish", {}),
              ("solid.extrude", {"sketch": name, "distance": str(depth), "operation": "cut", "targets": targets})]
    return steps


def mesh(fans, keep_out, other=()):
    """Hexagons over the whole panel, with a round hole in place of the cell at each fan screw and at
    each of the `other` screws (x, y, diameter)."""
    ax, ay = fans[0]
    h = FAN_HOLES / 2
    screws = [(fx + i * h, fy + j * h, FAN_CLEAR) for fx, fy in fans for i in (-1, 1) for j in (-1, 1)] + list(other)
    out = []
    for j in range(-int(LY / PITCH_Y), int(LY / PITCH_Y) + 1):
        for i in range(-int(LX / PITCH_X), int(LX / PITCH_X) + 1):
            x = ax + (i + (0.5 if j % 2 else 0)) * PITCH_X
            y = ay + j * PITCH_Y
            at = [d for sx, sy, d in screws if math.hypot(x - sx, y - sy) < 0.05]
            if at:
                out.append((round(x, 4), round(y, 4), at[0]))
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
    """Bottom, rear and top in one part; the fans, the tray and the bulkhead fasten to it."""
    w = LY + 2 * T
    zt, xf = LZ + T, LX + T
    lip = lambda p: {"point": p, "height": str(SIDE_LIP)}
    wide = lambda p: {"point": p, "height": str(JOIN_LIP)}
    s = [("sketch.create", {"plane": "XZ", "offset": str(-T), "name": "core-profile"}),
         ("sketch.line", {"points": [[xf, -zt], [-T, -zt], [-T, T], [xf, T]]}),
         ("sketch.finish", {}),
         ("sheet.flange", {"sketch": "core-profile", "curves": ["l1", "l2", "l3"], "distance": str(w),
                           "body_name": "core"}),
         ("sheet.flange", {"body": "core", "height": str(FLANGE), "flip": True, "edges": [
             {"point": [xf, LY / 2, zt], "height": str(LIP_TOP)}, {"point": [xf, LY / 2, -T], "height": str(LIP_BOTTOM)},
             lip([LX / 2, -T, zt]), wide([LX / 2, LY + T, zt]), lip([LX / 2, -T, -T]), wide([LX / 2, LY + T, -T]),
             lip([-T, -T, LZ / 2]), wide([-T, LY + T, LZ / 2])]})]
    # rear panel: the standard I/O aperture and the mains inlet with its two screws
    iy, iz = INLET
    rear = [(IO_Y[0], IO_Z[0], IO_Y[1], IO_Z[1]), ("round", iy - 14, iz - 10, iy + 14, iz + 10, 1.0),
            (iy - 20, iz, M3_CLEAR), (iy + 20, iz, M3_CLEAR)]
    s += cut("rear-cuts", REAR, rear, 5, ["core"])
    pad = near(FEET, FOOT_PAD + HEX_AF / 2)
    s += cut("bottom-mesh", XY, mesh(BOTTOM_FANS, pad)
             + [(x, y, STUD_632) for x, y in FEET] + [SCREW + (PIN_TAP,), PINS[1] + (PIN_TAP,)], 5, ["core"])
    s += cut("top-mesh", TOP, top_mesh() + [(x, y, PIN_TAP) for x, y in PINS], 6, ["core"])
    # The top front lip steps back round the switch's head, from the lip's end so that no sliver is left
    # beside the switch. Then the free corners of both front lips are rounded.
    sy, sz = SWITCH
    front = plane([LX - 0.2, 0, 0], [0, 1, 0], [0, 0, 1])
    s += cut("lip-joins", TRAY, [(x, z, SF_HEAD) for x, z in TRAY_JOINS], 5, ["core"])
    s += cut("front-lip-joins", front, [(y, z, SF_HEAD) for y, z in BULKHEAD_JOINS], 2.5, ["core"])
    s += cut("front-lips", front, [(-T - 1, sz - 4, sy + 10, sz + 9.5)], 2.5, ["core"])
    s += rounds("front-lip-corners", front, [(sy + 10, LZ + T - LIP_TOP, 1, 1), (T, LIP_BOTTOM - T, 1, -1),
                                             (LY - T, LIP_BOTTOM - T, -1, -1)], 2.5, ["core"])
    return s


def top_mesh():
    return mesh([TOP_FAN], lambda x, y: False, [(x, y, LOOSE_632) for x, y in SHELF_SCREWS])


def tray():
    """A flat plate the length of the case, fixed to the side lips of the bottom, rear and top
    panels. No flange at the rear: the I/O aperture's keepout reaches to within 5 mm of it."""
    x0, x1 = EDGE, LX - GAP
    s = [("sketch.create", {"plane": plane([x0, 0, 0], [0, 1, 0], [0, 0, 1]), "name": "tray-profile"}),
         ("sketch.line", {"points": [[TRAY_Y, EDGE], [TRAY_Y, LZ - EDGE]]}),
         ("sketch.finish", {}),
         ("sheet.flange", {"sketch": "tray-profile", "curves": ["l1"], "distance": str(x1 - x0),
                           "body_name": "tray"})]
    holes = [(BOARD_X + u, BOARD_Z + BOARD - v, STANDOFF_632) for u, v in BOARD_HOLES]
    # an opening to reach the back of the board: 10 inside the rear standoffs, 8 inside the upper and
    # lower ones, and out to 4 short of the board's front edge
    us, vs = [u for u, v in BOARD_HOLES], [v for u, v in BOARD_HOLES]
    holes.append(("round", BOARD_X + min(us) + 10, BOARD_Z + BOARD - max(vs) + 8,
                  BOARD_X + BOARD - 4, BOARD_Z + BOARD - min(vs) - 8, 8))
    holes += [(x, z, SF_TAIL) for x, z in TRAY_JOINS]
    s += cut("tray-cuts", TRAY, holes, 5, ["tray"])
    s += rounds("tray-corners", TRAY, [(x0, EDGE, 1, 1), (x1, EDGE, -1, 1), (x0, LZ - EDGE, 1, -1),
                                       (x1, LZ - EDGE, -1, -1)], 5, ["tray"])
    return s


def bulkhead():
    """A flat plate across the front, floor to top panel, fixed to the front lips of both. It closes
    the open end of the core, holds the top panel's front edge up, and carries the PSU shelf."""
    ya, yb = 0.4, TRAY_Y - GAP
    x0, x1 = BULKHEAD_X
    s = [("sketch.create", {"plane": plane([0, yb, 0], [1, 0, 0], [0, 0, 1]), "name": "bulkhead-profile"}),
         ("sketch.line", {"points": [[x1, LZ - EDGE], [x1, EDGE]]}),
         ("sketch.finish", {}),
         ("sheet.flange", {"sketch": "bulkhead-profile", "curves": ["l1"], "distance": str(yb - ya),
                           "body_name": "bulkhead"})]
    s += cut("bulkhead-cuts", plane([x0 - 0.15, 0, 0], [0, 1, 0], [0, 0, 1]),
             [SWITCH + (SWITCH_HOLE,)] + [(y, z, STUD_632) for y, z in SHELF_STUDS]
             + [(y, z, SF_TAIL) for y, z in BULKHEAD_JOINS], T + 0.3, ["bulkhead"])
    s += rounds("bulkhead-corners", plane([x0 - 0.15, 0, 0], [0, 1, 0], [0, 0, 1]),
                [(ya, EDGE, 1, 1), (yb, EDGE, -1, 1), (ya, LZ - EDGE, 1, -1), (yb, LZ - EDGE, -1, -1)], T + 0.3, ["bulkhead"])
    return s


def shelf():
    """The PSU screws up against its underside, exhaust face up. Its front flange hangs on studs in the bulkhead,
    two tabs folded from its rear wall take screws down through the top panel, and that wall shuts the space above the PSU off from the rest of the case, so the exhaust can only
    leave through the top mesh. The bulkhead, the shell's side and the tray close the other sides."""
    zt = LZ - 0.1
    zb = zt - 2 * T    # where the tabs' bends start
    ya, yb = 0.4, TRAY_Y - GAP
    xr, xf = SHELF_X
    f = SHELF_FLANGE
    s = [("sketch.create", {"plane": plane([0, yb, 0], [1, 0, 0], [0, 0, 1]), "name": "shelf-profile"}),
         ("sketch.line", {"points": [[xf, PSU_TOP + 12], [xf, PSU_TOP], [xr, PSU_TOP], [xr, zb]]}),
         ("sketch.finish", {}),
         ("sheet.flange", {"sketch": "shelf-profile", "curves": ["l1", "l2", "l3"],
                           "distance": str(yb - ya), "body_name": "shelf"})]
    # The rear wall is straight, with a tab folded over at each side for the screws and a relief slot
    # beside each. SolidCraft folds only one flange feature on a side of a panel and levels the whole
    # side to where its bends start, so the straight part stops one bend (2.4) short of the tabs' tops
    # and of the top panel. It could not be made to model the straight part carried on up.
    # Each tab's inner edge is 5.6 from its nut. The tab on the open side starts clear of the bend of
    # the top panel's side lip.
    a, b = SHELF_SCREWS[0][1] + 5.6, SHELF_SCREWS[1][1] - 5.6
    y0 = EDGE
    s += cut("shelf-reliefs", plane([xr - 2, 0, 0], [0, 1, 0], [0, 0, 1]),
             [(a, zb - 3, a + 2, zb + 1), (b - 2, zb - 3, b, zb + 1), (ya - 1, zb - 3, y0, zb + 1)], 4, ["shelf"])
    s += [("sheet.flange", {"body": "shelf", "height": str(f), "flip": True, "position": "outside", "edges": [
        [xr, (y0 + a) / 2, zb], [xr, (b + yb) / 2, zb]]})]
    web = [("round", PSU_X + 8, PSU_Y + 12, PSU_X + 55.5, PSU_Y + 113, 3)]
    web += [(PSU_X + u, PSU_Y + v, CLEAR_632) for u, v in PSU_HOLES + PSU_HOLES_SPARE]
    s += cut("shelf-web", plane([0, 0, PSU_TOP - 2], [1, 0, 0], [0, 1, 0]), web, 5, ["shelf"])
    # Each tab loses the corners that would show in the cells beside its screw's. The cell behind the
    # screw's is over the tab's root and bend, which have to be there.
    h, clear = HEX_AF / 2, 2 * T + 0.2
    beside = [c for c in top_mesh() if c[0] == "hex" and xr + clear <= c[1] - h < xr + f
              and not a + 6 < c[2] < b - 6]
    # The cells of the next row inward that lie over the bend still catch the tab's edge with their
    # points. A cut may not reach the bend, so only the point comes off the tab, and only forward of
    # the bend; what is left in those cells is the bend itself.
    rows = [y for x, y in SHELF_SCREWS]
    v = HEX_K * HEX_AF / math.sqrt(3)
    for c in top_mesh():
        if (c[0] == "hex" and c[1] - h < xr + clear < c[1] + h and min(abs(c[2] - y) for y in rows) > 1
                and not a + 6 < c[2] < b - 6):
            side = 1 if c[2] < LY / 2 else -1                      # which way the cell lies from its tab
            edge = (a if side > 0 else b) + side * 0.3
            tip = c[2] - side * v
            dx = h * abs(edge - tip) / (v / 2)
            x0 = xr + clear
            pts = [[c[1] + dx, edge], [c[1], tip], [c[1] - dx, edge]]
            if c[1] - dx < x0:   # clip at the bend
                on = lambda p, q: [x0, p[1] + (q[1] - p[1]) * (x0 - p[0]) / (q[0] - p[0])]
                pts = [pts[0]] + ([pts[1], on(pts[1], pts[2])] if c[1] > x0 else [on(pts[0], pts[1])]) + [[x0, edge]]
            beside.append(("poly", [[round(x, 3), round(y, 3)] for x, y in pts]))
    s += cut("shelf-tabs", plane([0, 0, zb + 0.5], [1, 0, 0], [0, 1, 0]),
             beside + [(x, y, NUT_632) for x, y in SHELF_SCREWS], 2 * T, ["shelf"])
    s += rounds("shelf-tab-corners", plane([0, 0, zb + 0.5], [1, 0, 0], [0, 1, 0]),
                [(round(xr + f, 4), y0, -1, 1), (round(xr + f, 4), yb, -1, -1)], 2 * T, ["shelf"])
    s += cut("shelf-cables", plane([xr - 2, 0, 0], [0, 1, 0], [0, 0, 1]), [GROMMET], 4, ["shelf"])
    # the front flange is scalloped under the switch, so a socket fits over its nut, and has the holes
    # for the bulkhead's studs
    front = plane([xf - T - 0.5, 0, 0], [0, 1, 0], [0, 0, 1])
    s += cut("shelf-switch", front, [SWITCH + (SWITCH_NUT + 5,)] + [(y, z, LOOSE_632) for y, z in SHELF_STUDS],
             T + 1, ["shelf"])
    s += rounds("shelf-corners", front, [(ya, PSU_TOP + 12, 1, -1), (yb, PSU_TOP + 12, -1, -1)], T + 1, ["shelf"])
    return s


def shell():
    """Front and both sides, plain. Slides on from the front, three of its flanges running onto screw heads
    at the rear corners; a screw at the fourth corner, underneath, keeps it there."""
    y0, y1, z0, z1 = SHELL_Y0, SHELL_Y1, SHELL_Z0, SHELL_Z1
    s = [("sketch.create", {"plane": plane([0, 0, z0], [1, 0, 0], [0, 1, 0]), "name": "shell-profile"}),
         ("sketch.line", {"points": [[-T, y1], [SHELL_XF, y1], [SHELL_XF, y0], [-T, y0]]}),
         ("sketch.finish", {}),
         ("sheet.flange", {"sketch": "shell-profile", "curves": ["l1", "l2", "l3"],
                           "distance": str(z1 - z0), "body_name": "shell"}),
         ("sheet.flange", {"body": "shell", "height": str(SHELL_RETURN), "flip": True, "edges": [
             [LX / 2, y0, z1], [LX / 2, y1, z1]]}),
         ("sheet.flange", {"body": "shell", "height": str(SHELL_RETURN), "flip": True, "edges": [
             [LX / 2, y0, z0], [LX / 2, y1, z0]]})]
    # slots open at the rear for the core's nubs, and a hole for the screw that holds it
    s += cut("shell-slots-top", plane([0, 0, z1 - T - 0.5], [1, 0, 0], [0, 1, 0]), [slot(*p) for p in PINS], T + 1, ["shell"])
    s += cut("shell-slots-bottom", plane([0, 0, z0 - 0.5], [1, 0, 0], [0, 1, 0]), [slot(*PINS[1]), SCREW + (M2_CLEAR,)], T + 1,
             ["shell"])
    s += cut("shell-switch", plane([LX, 0, 0], [0, 1, 0], [0, 0, 1]), [SWITCH + (SWITCH_SHELL,)], 5, ["shell"])
    # free corners of the flanges: their front ends, and the rear end of the one with no slot
    xe, ta, tb = SHELL_XF - 2 * T, y0 + SHELL_RETURN, y1 - SHELL_RETURN
    s += rounds("shell-corners-top", plane([0, 0, z1 - T - 0.5], [1, 0, 0], [0, 1, 0]),
                [(xe, ta, -1, -1), (xe, tb, -1, 1)], T + 1, ["shell"])
    s += rounds("shell-corners-bottom", plane([0, 0, z0 - 0.5], [1, 0, 0], [0, 1, 0]),
                [(xe, ta, -1, -1), (xe, tb, -1, 1), (-T, ta, 1, -1)], T + 1, ["shell"])
    return s


def slot(px, py):
    """Outline to cut from a shell flange for the pin at (px, py): a slot open at the rear with a round
    end on the pin, and the narrow finger left between the slot and the flange's tip cut back to just
    past the pin and rounded."""
    side = 1 if py < LY / 2 else -1                 # which way the flange's tip lies from the pin
    r = PIN / 2 + SLOT_CLEAR
    tip = (SHELL_Y0 + SHELL_RETURN) if side > 0 else (SHELL_Y1 - SHELL_RETURN)
    a, b = py - side * r, py + side * r             # the slot's edges: toward the bend, toward the tip
    fr = abs(tip - b) / 2                           # half the finger's width
    fx = px - PIN / 2 - 1.0 + fr                    # centre of the finger's round end
    arc = lambda cx, cy, rad, a0, a1: [[round(cx + rad * math.cos(math.radians(a0 + (a1 - a0) * k / 8)), 3),
                                        round(cy + side * rad * math.sin(math.radians(a0 + (a1 - a0) * k / 8)), 3)]
                                       for k in range(9)]
    pts = [[-T - 1, a]] + arc(px, py, r, -90, 90) + arc(fx, b + side * fr, fr, -90, -270)
    pts += [[fx, tip + side * 0.3], [-T - 1, tip + side * 0.3]]
    return ("poly", pts)


# SpotFast fasteners, tray to the side lips of the bottom and top panels and of the rear panel: X and Z
TRAY_JOINS = ([(x, z) for x in (40, LX / 2, LX - 40) for z in (JOIN_IN, LZ - JOIN_IN)]
              + [(JOIN_IN, z) for z in (40, 105, 170)])


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
    s += fan("ref-cpu-fan", [cx, hy - FAN_T, cz], [0, 1, 0])
    s += psu()
    # mains inlet: a body through the panel with a flange outside, held by two countersunk M3 screws
    iy, iz = INLET
    s += box("ref-mains-inlet", "#2b2e33", -T - 2.5, 23.5, iy - 13.6, iy + 13.6, iz - 9.6, iz + 9.6)
    s += [("solid.box", {"length": 2.5, "width": 48, "height": 23, "corner": [-T - 2.5, iy - 24, iz - 11.5],
                         "operation": "join", "targets": ["ref-mains-inlet"]}),
          ("solid.box", {"length": 14, "width": 23, "height": 15, "corner": [-T - 2.5, iy - 11.5, iz - 7.5],
                         "operation": "cut", "targets": ["ref-mains-inlet"]})]
    for i, (fx, fy) in enumerate(BOTTOM_FANS):
        s += fan("ref-fan-bottom-%d" % (i + 1), [fx, fy, 0], [0, 0, 1])
    s += fan("ref-fan-top", [TOP_FAN[0], TOP_FAN[1], LZ], [0, 0, -1])
    return s


def rotor(name, at, n, hub, tip, h, color):
    """Hub and nine swept blades, as a body of its own."""
    xd, yd = frame(n)
    s = cyl(name, along(at, n, -1), n, 2 * hub, h + 2, "new")
    s += [("sketch.create", {"plane": plane(at, xd, yd), "name": "sk-" + name})]
    for k in range(9):
        edge = lambda w: [(r, k * 2 * math.pi / 9 + 0.9 * (r - hub) / (tip - hub) + w * (0.56 - 0.1 * (r - hub) / (tip - hub)))
                          for r in [hub - 2 + (tip - hub + 2) * j / 6 for j in range(7)]]
        pts = edge(0) + edge(1)[::-1]
        s.append(("sketch.line", {"points": [[round(r * math.cos(a), 3), round(r * math.sin(a), 3)] for r, a in pts],
                                  "closed": True, "connect": False, "infer": False}))
    s += [("sketch.finish", {}),
          ("solid.extrude", {"sketch": "sk-" + name, "distance": str(h), "operation": "join", "targets": [name]})]
    return s + paint([name], color)


def fan(name, at, n):
    """A 120 x 15 fan with its mounting face centred on `at` and its depth along n."""
    xd, yd = frame(n)
    h = FAN_HOLES / 2
    s = [("sketch.create", {"plane": plane(at, xd, yd), "name": "sk-" + name}),
         ("sketch.rectangle.rounded", {"p0": [-FAN / 2, -FAN / 2], "p1": [FAN / 2, FAN / 2], "radius": "6",
                                       "connect": False}),
         ("sketch.circle.center", {"center": [0, 0], "diameter": 116, "connect": False})]
    s += [("sketch.circle.center", {"center": [a * h, b * h], "diameter": 4.3, "connect": False})
          for a in (-1, 1) for b in (-1, 1)]
    s += [("sketch.finish", {}),
          ("solid.extrude", {"sketch": "sk-" + name, "distance": str(FAN_T), "operation": "new", "body_name": name})]
    return s + paint([name], "#d9c7a8") + rotor(name + "-rotor", along(at, n, 2), n, 21, 56.5, FAN_T - 4, "#6f4631")


def psu():
    """SFX supply: fan and guard on the face toward the board; vents, inlet and switch on top, the inlet at
    the open side and turned as on the SF450 and the Focus SGX-550 (2021)."""
    n = "ref-psu-sfx"
    yc, zc = PSU_Y + PSU[1] / 2, PSU_TOP - PSU[2] / 2
    s = box(n, "#2b2e33", PSU_X, PSU_X + PSU[0], PSU_Y, PSU_Y + PSU[1], PSU_TOP - PSU[2], PSU_TOP)
    cutbox = lambda x0, x1, y0, y1, z0, z1: ("solid.box", {
        "length": round(x1 - x0, 3), "width": round(y1 - y0, 3), "height": round(z1 - z0, 3),
        "corner": [round(x0, 3), round(y0, 3), round(z0, 3)], "operation": "cut", "targets": [n]})
    s += [("solid.cylinder", {"diameter": 90, "height": 16, "base": [PSU_X, yc, zc], "axis": [1, 0, 0],
                              "operation": "cut", "targets": [n]})]
    s += [cutbox(PSU_X + 12 + 5 * i, PSU_X + 15 + 5 * i, PSU_Y + 50, PSU_Y + 112, PSU_TOP - 2, PSU_TOP) for i in range(9)]
    # C14 inlet: its pins in a row along the supply's width, the earth pin nearest the fan, switch beside it
    ix, iy = PSU_X + 25, PSU_Y + 29
    s += [cutbox(ix - 10, ix + 10, iy - 14, iy + 14, PSU_TOP - 16, PSU_TOP)]
    s += box("ref-psu-pins", ZINC, ix - 4, ix, iy - 1, iy + 1, PSU_TOP - 16, PSU_TOP - 3)
    s += [("solid.box", {"length": 4, "width": 2, "height": 13, "corner": [round(ix, 3), round(iy + d - 1, 3), PSU_TOP - 16],
                         "operation": "join", "targets": ["ref-psu-pins"]}) for d in (-7, 7)]
    s += box("ref-psu-switch", "#111111", PSU_X + 40, PSU_X + 53, PSU_Y + 20, PSU_Y + 39, PSU_TOP, PSU_TOP + 1.5)
    s += rotor("ref-psu-rotor", [PSU_X + 3, yc, zc], [1, 0, 0], 16, 43, 11, "#111111")
    g = "ref-psu-guard"
    s += [("sketch.create", {"plane": plane([PSU_X, yc, zc], [0, 1, 0], [0, 0, 1]), "name": "sk-" + g})]
    s += [("sketch.circle.center", {"center": [0, 0], "radius": r, "connect": False})
          for r in (45, 43.6, 34, 32.6, 23, 21.6, 12)]
    s += [("sketch.finish", {}),
          ("solid.extrude", {"sketch": "sk-" + g, "distance": "1.4", "operation": "new", "body_name": g}),
          ("solid.box", {"length": 1.4, "width": 89, "height": 1.6, "corner": [PSU_X, yc - 44.5, zc - 0.8],
                         "operation": "join", "targets": [g]}),
          ("solid.box", {"length": 1.4, "width": 1.6, "height": 89, "corner": [PSU_X, yc - 0.8, zc - 44.5],
                         "operation": "join", "targets": [g]})]
    return s + paint([g], ZINC)


def frame(n):
    """Sketch axes for a plane whose normal is the axis direction n."""
    k = [abs(c) for c in n].index(1)
    e = lambda i: [1 if j == i else 0 for j in range(3)]
    a, b = e((k + 1) % 3), e((k + 2) % 3)
    return (a, b) if n[k] > 0 else (b, a)


def along(p, n, d):
    return [round(p[i] + n[i] * d, 3) for i in range(3)]


def neg(n):
    return [-c for c in n]


def hexagon(name, at, n, af, h):
    """A new body: a hexagon af across flats standing h tall on the point `at`, along n."""
    xd, yd = frame(n)
    return [("sketch.create", {"plane": plane(at, xd, yd), "name": "sk-" + name}),
            ("sketch.polygon.circumscribed", {"center": [0, 0], "radius": af / 2, "sides": 6, "connect": False}),
            ("sketch.finish", {}),
            ("solid.extrude", {"sketch": "sk-" + name, "distance": str(h), "operation": "new", "body_name": name})]


def cyl(name, at, n, d, h, op="join"):
    c = {"diameter": d, "height": round(h, 3), "base": [round(v, 3) for v in at], "axis": n, "operation": op}
    c.update({"body_name": name} if op == "new" else {"targets": [name]})
    return [("solid.cylinder", c)]


def paint(names, color):
    return [("appearance.assign", {"bodies": names, "color": color})]


def pc_screw(name, at, n, length=SCREW_632):
    """6-32 hex washer head screw with its head on the point `at`, which faces along n."""
    return (hexagon(name, along(at, n, 0.8), n, 6.35, 2.0) + cyl(name, at, n, 8.0, 0.8)
            + cyl(name, at, neg(n), 3.5, length) + paint([name], BLACK))


def cap_screw(name, at, n, length):
    """M2 socket head cap screw. The thread is drawn at its root, so it does not read as a clash with
    the tapped hole it is in."""
    top = along(at, n, 2.0)
    xd, yd = frame(neg(n))
    return (cyl(name, at, n, PIN, 2.0, "new") + cyl(name, at, neg(n), 1.55, length)
            + [("sketch.create", {"plane": plane(top, xd, yd), "name": "sk-" + name}),
               ("sketch.polygon.circumscribed", {"center": [0, 0], "radius": 0.75, "sides": 6, "connect": False}),
               ("sketch.finish", {}),
               ("solid.extrude", {"sketch": "sk-" + name, "distance": "1.2", "operation": "cut", "targets": [name]}),
               ("solid.chamfer", {"body": name, "edges": [along(top, xd, PIN / 2)], "distance": "0.2"})]
            + paint([name], BLACK))


def fan_screw(name, at, n):
    """Self-tapping fan screw with a cross-recessed pan head, for a panel that faces along Z."""
    s = cyl(name, at, n, 8.5, 1.8, "new") + cyl(name, at, neg(n), 5.0, FAN_SCREW)
    z = at[2] + (0.9 if n[2] > 0 else -1.8)
    for l, w in ((5.0, 1.0), (1.0, 5.0)):
        s.append(("solid.box", {"length": l, "width": w, "height": 0.9, "corner": [at[0] - l / 2, at[1] - w / 2, z],
                                "operation": "cut", "targets": [name]}))
    return s + paint([name], BLACK)


def nut(name, at, n):
    return hexagon(name, at, n, 7.94, 2.78) + paint([name], ZINC)


def hardware():
    """Screws, nuts, standoffs, studs and joining fasteners, for the assembly only."""
    up, down, back, fore, left = [0, 0, 1], [0, 0, -1], [-1, 0, 0], [1, 0, 0], [0, -1, 0]
    h = FAN_HOLES / 2
    s = []
    for f, fans in (("bottom", BOTTOM_FANS), ("top", [TOP_FAN])):
        out = down if f == "bottom" else up
        for i, (x, y) in enumerate((fx + a * h, fy + b * h) for fx, fy in fans for a in (-1, 1) for b in (-1, 1)):
            s += fan_screw("screw-fan-%s-%d" % (f, i + 1), [x, y, -T if f == "bottom" else LZ + T], out)
    for i, (x, y) in enumerate(SHELF_SCREWS):
        s += pc_screw("screw-shelf-%d" % (i + 1), [x, y, LZ + T], up)
        s += cyl("nut-shelf-%d" % (i + 1), [x, y, LZ - 0.1 - T], down, 7.11, 1.78, "new")
        s += paint(["nut-shelf-%d" % (i + 1)], ZINC)
    for i, (a, b) in enumerate(PSU_HOLES):
        s += pc_screw("screw-psu-%d" % (i + 1), [PSU_X + a, PSU_Y + b, PSU_TOP + T], up)
    for i, (u, v) in enumerate(BOARD_HOLES):
        x, z = BOARD_X + u, BOARD_Z + BOARD - v
        s += hexagon("standoff-%d" % (i + 1), [x, TRAY_Y, z], left, 6.35, STANDOFF)
        s += paint(["standoff-%d" % (i + 1)], ZINC)
        s += pc_screw("screw-board-%d" % (i + 1), [x, BOARD_Y, z], left)
    # shelf: flush studs in the bulkhead, nuts behind the shelf's front flange
    for i, (y, z) in enumerate(SHELF_STUDS):
        s += cyl("stud-%d" % (i + 1), [LX, y, z], back, 3.5, T + STUD_LENGTH, "new") + paint(["stud-%d" % (i + 1)], ZINC)
        s += nut("nut-stud-%d" % (i + 1), [SHELF_X[1] - T, y, z], back)
    for i, d in enumerate((-20, 20)):
        n = "screw-inlet-%d" % (i + 1)   # countersunk M3, flush in the inlet's flange
        s += cyl(n, [-T - 2.6, INLET[0] + d, INLET[1]], fore, 5.6, 0.4, "new")
        s += cyl(n, [-T - 2.2, INLET[0] + d, INLET[1]], fore, 3.0, 8.0) + paint([n], BLACK)
        s += hexagon("nut-inlet-%d" % (i + 1), [0, INLET[0] + d, INLET[1]], fore, 5.5, 2.4)
        s += paint(["nut-inlet-%d" % (i + 1)], ZINC)
    # shell: a nub at three corners and the screw that holds it at the fourth
    for i, (x, y) in enumerate(PINS):
        s += cap_screw("nub-top-%d" % (i + 1), [x, y, LZ + T], up, 3.0)
    s += cap_screw("nub-bottom", [PINS[1][0], PINS[1][1], -T], down, 3.0)
    s += cap_screw("screw-shell", [SCREW[0], SCREW[1], SHELL_Z0], down, 4.0)
    # SpotFast: flush in the lip and in the plate behind it
    joins = [("join-tray-%d" % (i + 1), [x, LY + T, z], left) for i, (x, z) in enumerate(TRAY_JOINS)]
    joins += [("join-bulkhead-%d" % (i + 1), [LX + T, y, z], back) for i, (y, z) in enumerate(BULKHEAD_JOINS)]
    for n, at, d in joins:
        s += cyl(n, at, d, SF_HEAD, T, "new") + cyl(n, along(at, d, T), d, SF_TAIL, T) + paint([n], ZINC)
    # switch: plain 12 mm body, nut behind the bulkhead, head out through the shell
    y, z = SWITCH
    s += cyl("switch", [BULKHEAD_X[1] - 22, y, z], fore, 11.9, 22, "new")
    s += cyl("switch", [BULKHEAD_X[1], y, z], fore, SWITCH_SHELL - 0.5, SHELL_XF + 0.6 - BULKHEAD_X[1])
    s += hexagon("switch-nut", [BULKHEAD_X[0], y, z], back, 13.5, 3.0)
    s += [("solid.cylinder", {"diameter": 12.0, "height": 3.0, "base": [BULKHEAD_X[0], y, z], "axis": back,
                              "operation": "cut", "targets": ["switch-nut"]})]
    s += paint(["switch", "switch-nut"], BLACK)
    for i, (x, y) in enumerate(FEET):
        n = "foot-%d" % (i + 1)
        s += cyl("stud-foot-%d" % (i + 1), [x, y, 0], down, 3.5, T + FOOT_STUD, "new")
        s += paint(["stud-foot-%d" % (i + 1)], ZINC)
        s += [("solid.cylinder", {"diameter": 20, "height": 2, "base": [x, y, -T - 2], "body_name": n,
                                  "operation": "new"}),
              ("solid.cone", {"diameter": 17, "top_diameter": 12, "height": -16, "base": [x, y, -T - 2],
                              "operation": "join", "targets": [n]}),
              ("solid.cylinder", {"diameter": FOOT_TAP, "height": FOOT_TAP_DEPTH, "base": [x, y, -T],
                                  "axis": down, "operation": "cut", "targets": [n]}),
              ("solid.cylinder", {"diameter": FOOT_RECESS, "height": FOOT_RECESS_DEPTH, "base": [x, y, -T - 18],
                                  "axis": up, "operation": "cut", "targets": [n]})] + paint([n], BLACK)
    return s


SHEET = ["core", "tray", "bulkhead", "shelf", "shell"]


def main():
    sc = Bridge()
    os.makedirs(EXPORT, exist_ok=True)
    os.makedirs(IMAGES, exist_ok=True)
    sc.call("new_design")
    sc.batch([("sheet.manage_rules", {"name": "CRS 1.2", "thickness": "%g mm" % T, "k_factor": "0.44",
                                      "bend_radius": "Thickness", "active": True})], "rule")
    for name, steps in (("core", core()), ("tray", tray()), ("bulkhead", bulkhead()), ("shelf", shelf()),
                        ("shell", shell())):
        sc.batch(steps, name)
        print("built", name)
    # a body hidden for a render stays hidden by name through a rebuild
    sc.batch([("appearance.assign", {"bodies": SHEET, "color": OLIVE}),
              ("browser.visibility", {"visible": True, "items": SHEET})], "paint")
    sc.call("save", {"path": DESIGN})
    report(sc)
    if "--sheet" in sys.argv:
        return
    for name, steps in (("bought-in", bought_in()), ("hardware", hardware())):
        sc.batch(steps, name)
        print("built", name)
    sc.call("execute", {"command": "file.export_step", "params": {
        "bodies": ["foot-1"], "path": os.path.join(EXPORT, "foot.step")}})
    sc.call("save", {"path": ASSEMBLY})
    m = sc.call("measure", {"summary": True})
    clashes(sc, [b["name"] for b in m["bodies"] if ours(b["name"])])
    if WITH_BOARD:
        board_fit(sc, m)


def ours(n):
    """A body this script made, as against one of the board model's."""
    return n.split(" ")[0] in SHEET or n.startswith(("ref-", "foot-", "screw-", "nut-", "standoff-", "stud-", "nub-",
                                                     "join-", "switch"))


# a fastener shares volume with what it threads into, and the mains inlet's body with its own screws
THREADED = [("screw-fan-", "ref-fan-"), ("screw-psu-", "ref-psu-sfx"), ("screw-shelf-", "nut-shelf-"),
            ("screw-board-", "standoff-"), ("stud-", "nut-stud-"), ("stud-foot-", "foot-"), ("screw-inlet-", "nut-inlet-"),
            ("screw-inlet-", "ref-mains-inlet"), ("switch", "switch-nut"),
            ("ref-psu-guard", "ref-psu-guard")]   # the guard's rings and spokes are drawn as overlapping pieces


def clashes(sc, bodies):
    """Every pair of our own bodies that shares volume, apart from threads."""
    r = sc.call("execute", {"command": "inspect.interference", "params": {"bodies": bodies}})
    thread = lambda a, b: any((a.startswith(p) and b.startswith(q)) or (b.startswith(p) and a.startswith(q))
                              for p, q in THREADED)
    found = [i for i in r.get("interferences", []) if not thread(str(i.get("a")), str(i.get("b")))]
    print("clash check over %d bodies: %d overlaps besides %d threads, %d pairs not checked" % (
        len(bodies), len(found), len(r.get("interferences", [])) - len(found), len(r.get("unchecked", []))))
    for i in found:
        print("  overlap %s / %s: %.2f mm3, box %s" % (i.get("a"), i.get("b"), i.get("volume_mm3", 0),
                                                         json.dumps(i.get("bbox"))[:160]))
    for i in r.get("unchecked", []):
        print("  not checked: %s / %s" % (i.get("a"), i.get("b")))


def report(sc):
    """Sizes of the sheet parts, and their flat patterns, bend tables and STEP models."""
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
    for b in SHEET:
        f = sc.call("execute", {"command": "sheet.flat_pattern", "params": {"body": b}})
        sc.call("execute", {"command": "sheet.export_dxf", "params": {
            "body": b, "path": os.path.join(EXPORT, b + ".dxf"), "bend_notes": True}})
        sc.call("execute", {"command": "sheet.export_bend_table", "params": {
            "body": b, "path": os.path.join(EXPORT, b + "-bends.csv")}})
        sc.call("execute", {"command": "file.export_step", "params": {
            "bodies": [b], "path": os.path.join(EXPORT, b + ".step")}})
        print("%-8s flat %.1f x %.1f mm, %d bends, %d cut-outs" % (
            b, f["flat_size_mm"][0], f["flat_size_mm"][1], len(f.get("bends", [])), len(f.get("cutouts", []))))


def board_fit(sc, m):
    """How Framework's model of the board sits in the case, from its bodies' extents and its holes."""
    parts = [b for b in m["bodies"] if not ours(b["name"]) and "bbox" in b]   # the outline body has no volume to measure
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
