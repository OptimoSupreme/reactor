"""Build the Reactor in SolidCraft, as two designs.

  python3 mechanical/reactor.py            reactor.sc: the sheet metal parts alone, five kinds and six pieces, which is what a shop
                                           makes, with their flat patterns and bend tables.
                                           reactor-low-detail.sc: the same parts with the fans, power supply,
                                           handles, lamps and every screw, nut and stud in place, the board
                                           drawn as a block, and a check for clashes.
  python3 mechanical/reactor.py --sheet    the sheet metal design and its exports only

The assembly is too big to commit, so .gitignore leaves it out.

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
DESIGN = os.path.join(REPO, "mechanical", "reactor.sc")
EXPORT = os.path.join(REPO, "mechanical", "export")
LOW_DETAIL = os.path.join(REPO, "mechanical", "reactor-low-detail.sc")    # the board as a block
BLOCK_BOARD = ["ref-mainboard", "ref-rear-ports"]
IMAGES = os.path.join(REPO, "docs", "images")

T = 1.2            # sheet
GAP = 0.3          # between nested sheet faces
SHELL_GAP = 0.5    # between a side panel and the lips it goes over: two bent parts, each good to about 0.4
LX, LY, LZ = 251.3, 128.0, 210.0   # cavity: rear to front, between the side lips, bottom to top panel
FLANGE = 10.0
SIDE_LIP = 14.0    # side lips of the top, bottom and rear panels on the open side
JOIN_LIP = 17.0    # and on the tray's side: 14.6 of flat lip against the tray, room for a press tool or a spot weld
JOIN_IN = 9.5      # a joining fastener's centre from the panel its lip is folded from: 7 from the bend and from the lip's edge
EDGE = T + GAP     # a joined plate stops this far from the panel it meets, clear of the bend at that panel's edge
ROUND = 1.5        # radius on outside corners
GREEN = "#4a5445"   # the outside: near FS 34094, the colour of Prismatic's PSS-11240; not matched to a swatch
INSIDE = ["tray", "shelf"]   # painted black
BLACK = "#1b1b1b"
ZINC = "#c8c8c8"

# Every screw is the 6-32 hex washer head screw of PC cases and 3.5 in drives, with its Phillips recess,
# apart from ordinary self-tapping fan screws and the mains inlet's countersunk M3s: one PH2 driver does
# them all. Sizes of the pressed-in parts are PEM's, see docs/parts.md.
# The tray is riveted to the lips of the core and the hood by hand with 3/32 in flush solid rivets,
# MS20426AD3-4: the 100 degree head sits in a countersink in the lip, flush outside where the side panel passes
# 0.3 to 0.5 away, and the tail is bucked to a head about 3.6 across and 1.2 tall inside, where the fans
# stand 2.8 from the tray. A blind rivet's tail is too long for that.
RIVET, RIVET_HOLE = 2.4, 2.5          # shank, and a No. 40 drill's hole
RIVET_CSK = (4.6, 100)                # countersink for the head, 4.55 across and 0.91 tall
RIVET_TAIL = (3.6, 1.2)
BEND_R, K_FACTOR = 1.32, 0.45         # OSH Cut's figures for 0.048 in A1008: its 0.052 in tooling radius
RELIEF = 3.0      # round relief where two bends meet at a corner, which OSH Cut asks for
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
# 11 pitches apart so one mesh puts a cell on the screws of both, and 1.7 from the bottom panel's front lip.
BOTTOM_FANS = [(FAN / 2 + 1.3, LY / 2), (FAN / 2 + 1.3 + 11 * PITCH_X, LY / 2)]
TOP_FAN = (LX / 2 - 3.5 * PITCH_X, LY / 2)      # half pitches from the middle, so the mesh mirrors front to back

# SFX supply standing in front of the board: fan toward the board, exhaust and mains inlet up
PSU = (63.5, 125.0, 100.0)                     # along X, Y, Z as it stands here
# 2.6 behind the bottom panel's front lip and 1.1 behind the shelf's front wall. That leaves 13.1 to the
# board's edge.
PSU_X = LX - T - 1.39 - PSU[0]
PSU_Y = 0.7
PSU_TOP = LZ - 35.0                            # room above for an angled mains plug, which stands 17
PSU_INLET = (25.0, 29.0)                       # middle of its mains inlet, along X and Y from the PSU's corner
# The three mounting holes of Intel's SFX12V guide, along X, Y from the PSU's corner: a pair at the tray's
# side and one at the open side, the end the guide draws the mains inlet at. With its fan toward the
# board, the SF450 and the Focus SGX-550 both have the inlet at the open side. The shelf has the same
# three mirrored as well, so that it takes a unit with all four corners threaded.
PSU_HOLES = [(6.0, 119.0), (57.5, 119.0), (31.7, 6.0)]
PSU_HOLES_SPARE = [(6.0, 6.0), (57.5, 6.0), (31.7, 119.0)]
# The bottom panel's front lip, behind the front panel: a stiffener, nothing is fixed to it.
LIP_BOTTOM = 14.0
# The shelf hangs from the top panel on four screws. Its rear wall stands 2.8 behind the supply's fan
# face, which puts the supply's two rear holes 5.7 from the wall's bend line, outside the reach of OSH
# Cut's die. Its front wall stands just behind the front panel, 1.1 in front of the supply.
SHELF_X = (PSU_X - 2.8, LX - GAP)
# The rear wall's two tabs fold toward the rear, away from the PSU, so that nothing stands over the PSU's
# screws when the shelf is out of the case. Each ends at the corner of the cell diagonally behind its
# screw's, so that cell's cut-out takes the tab's corner off at a slant and stops there.
SHELF_FLANGE = SHELF_X[0] + T - round(TOP_FAN[0] + 7 * PITCH_X, 4)   # rounded as the cells' corners are
# two screws down through the top panel into nuts in the rear wall's tabs: a cell in the outermost row on
# each side, the rows the fan screws are in
SHELF_SCREWS = [(TOP_FAN[0] + 7.5 * PITCH_X, LY / 2 + j * PITCH_Y) for j in (-HEX_NY, HEX_NY)]
# and two into the front wall's tabs. The front wall is only as wide as the space between the switch
# and the lamps, which stand behind the front panel at its two ends: Y of its ends.
SHELF_FRONT_SCREWS = [(TOP_FAN[0] + 13 * PITCH_X, LY / 2 + j * PITCH_Y) for j in (-2, 2)]
SHELF_FRONT_WALL = (23.0, LY - 23.0)
SHELF_FRONT_TAB = 12.0     # each tab's width: its nut is 5.6 or more from every edge
# Notch in the tray-side edge of the shelf's rear wall for the mains lead and the wires of the switch and
# the lamps: Y of its closed end, Z of its lower and upper edges, corner radius. It is open toward the
# tray, which shuts it when the shelf is in, so the lead and the wires go in from the side with the shelf
# out. It is over the gap between the board and the supply, and the lead runs down that gap against the
# tray, past the tie slots. It is 13 deep: 8 for the lead at the tray's end and 4 beside it for the three
# wires, one above another. OSH Cut's die needs 5.7 of flange from each bend line: there is 9.0 of wall
# under it and about 8.6 over it, up to the outside of the tab folded from the wall's top.
LEAD_NOTCH = (TRAY_Y - GAP - 13.0, PSU_TOP + 9.0, PSU_TOP + 26.0, 3.0)
# Rubber U channel pushed onto the notch's edge. No part is chosen yet, so this is a placeholder: how thick
# it is over the edge and on each face of the wall, and how far its legs reach onto the wall.
TRIM, TRIM_LEG = 1.0, 4.0

# Cable ties: four pairs of slots in the tray, in the gap between the board's edge and the PSU. A tie
# goes in at one slot, behind the tray and out at the other, round a cable running up the gap. There
# is 1.7 between the tray and the side panel for it, which a 2.5 or 3.6 wide tie's strap fits.
TIE_X = (BOARD_X + BOARD + PSU_X) / 2
TIE_Z = [35.0, 80.0, 125.0, 170.0]
TIE_SLOT, TIE_APART = (2.0, 5.0), 8.0

FEET = [(17, 25), (LX - 17, 25), (17, LY - 25), (LX - 17, LY - 25)]   # clear of the fan screws' heads
FOOT_PAD = 12.0    # solid land around each foot: the nearest cell is 1.3 outside the foot's 20 mm flange
# A screw's head or a nut inside would sit under a fan's frame, so each foot turns onto a flush stud
# pressed into the bottom panel, pointing down.
FOOT_STUD = 9.53   # FH-632-6
FOOT_TAP = 2.7     # tap drill for 6-32, right through, so that an ordinary tap can run out of the far end
FOOT_RECESS, FOOT_RECESS_DEPTH = 9.0, 1.5   # recess underneath for a 3M SJ5076 bumper, 8.0 x 2.8
# A cross slot in the recess's floor, around the hole, to turn the foot tight with the PH2 driver the case's
# screws take. It is printed to +/-0.3, so it is a plain cross that a driver's wings drop into, not a Phillips
# recess: the point goes down the hole and the wings stop on the slot's floor at the hole's edge, 4 below the
# recess's floor and 3 short of the stud. The bumper goes on over it and keeps three fifths of its face.
FOOT_CROSS, FOOT_CROSS_DEPTH = (1.6, 6.0), 2.5   # each slot's width and length; a PH2's shank is 6 across

# side panels and front panel
SHELL_Y0, SHELL_Y1 = -2 * T - SHELL_GAP, LY + 2 * T + SHELL_GAP   # outside faces of the two side panels
SHELL_Z0, SHELL_Z1 = -2 * T - SHELL_GAP, LZ + 2 * T + SHELL_GAP
SHELL_XF = LX + 2 * T + GAP   # outside face of the front panel
SHELL_RETURN = 9.5  # flanges over the top and under the bottom: narrow enough to pass the fan screws' heads
# The top and the front are one part, the hood, folded where they meet. The front has a flange down each
# side, folded back inside the side panels, in the layer of the core's lips. No part is a U with tall legs, which a press brake's punch cannot reach into.
FRONT_FLANGE = 18.0
LIP_END = SHELL_XF - FRONT_FLANGE - GAP   # the flanges' rear edges
# Where a lip of the hood meets a lip of the core, at the top of the rear and at the foot of the front,
# the two are mitred at 45 degrees through the corner of the two panels' inside faces and stand 1.2
# apart, as SolidCraft mitres two lips of one part. Each lip stops MITRE short of that line, measured
# along either panel.
MITRE = 0.85
# The front's foot: a return under the bottom panel, against it, between the side panels' returns. It
# is 9.5, short of the mesh, with a tab at each end that one of the front fan's two front screws goes up
# through. Y of the return's ends and of the tabs' inner edges.
HOOD_Z0 = -2 * T
HOOD_RETURN, HOOD_TAB = 9.5, 17.7
HOOD_RETURN_Y = (SHELL_Y0 + SHELL_RETURN + 0.5, SHELL_Y1 - SHELL_RETURN - 0.5)
HOOD_TABS = (17.0, LY - 17.0)
MOUNT_X = (SHELL_XF - T, SHELL_XF)        # the front panel, which the switch and the lamps are fixed in
# The two side panels are one part: flat, with a flange over the top and one under the bottom, reaching
# from the rear panel's outside face to the front panel's. Four ordinary 6-32 screws hold each, 9.2 in
# from its front and rear edges and 17 from the top and bottom panels, into nuts pressed into the rear
# panel's side lips and the front's flanges. X and Z. Each nut's hole is 5.8 from its lip's bend
# line, outside the 5.7 that OSH Cut's die reaches, and 5.8 from the lip's edge, where PEM asks 5.6. At
# that height the nuts clear the supply, the shelf, the rivets, the nearest of the board's standoffs and
# the relief at the rear panel's top corners. The front
# pair also hold the front panel. All eight can be reached with the case standing where it is.
SIDE_SCREW_Z = (17.0, LZ - 17.0)
SIDE_SCREWS = [(x, z) for x in (8.0, SHELL_XF - T - 8.0) for z in SIDE_SCREW_Z]
REAR_LIP = 15.0
# The rear panel's top lip, under the top panel: 16.5 at the corners, where the rear handle's screws go
# through it 9.5 from the panel, and 9.5 between them, short of the mesh's first cells at 10.0. Y of the
# inner ends of the two corner tabs, each 3 past its screw's hole.
TOP_LIP, TOP_LIP_MID = 16.5, 9.5
TOP_LIP_TABS = (18.5, LY - 18.5)
TOP_SLOT = 2.0     # slot in the top panel's side edge that ends its side lip
NUT_BODY = (7.11, 1.78)   # an S-632-1's body behind the sheet: across, tall
NUT_NOTCH = 8.2           # the tray's notch round the body of a nut in the lip it lies against: 7.2 from a standoff
# Two handles across the top, one at the rear and one at the front: RAF 8120-632-A-24 (Fascomp
# FC8120-632-A-24), 1/4 in black anodised aluminium rod bent twice, 4 in between its legs and 1 1/4 in
# tall, each leg tapped 6-32 3/8 in deep. A case screw goes up into each leg from under the top panel.
# The legs stand in the bare corners beyond the ends of the mesh's outer rows, 3.4 inside the side panels'
# flanges, with the rear pair's screw heads between the rear panel and the top fan and the front pair's
# over the supply.
HANDLE = (101.6, 6.35, 31.75, 9.525)   # between centres, rod, overall height, bend radius to the rod's centre
HANDLE_X = [9.5, LX - 9.5]
HANDLE_Y = [round(LY / 2 - HANDLE[0] / 2, 3), round(LY / 2 + HANDLE[0] / 2, 3)]
HANDLE_HOLES = [(x, y) for x in HANDLE_X for y in HANDLE_Y]
# 12 mm vandal switch, Y and Z: top left seen from the front, under the handle's leg. It is fixed in the
# front panel, its head outside and its nut behind.
FRONT_Z = LZ - 18.5   # the switch, and the middle of the pair of lamps on the other side
SWITCH = (HANDLE_Y[0], FRONT_Z)
SWITCH_HOLE, SWITCH_HEAD, SWITCH_NUT = 12.0, (14.0, 1.5), 16.0
# Two lamps under the other leg, one above the other: power above, in green, and drive activity below, in
# amber. Each is a 5 mm LED in a black panel holder for an 8 mm hole, measured from the part: its bezel is
# 10.8 across where it sits on the panel, tapering to 8.8, and 4.3 tall; 11 of it is behind the bezel. They
# are fixed in the front panel as the switch is. Y and Z.
LEDS = [(HANDLE_Y[1], FRONT_Z + 7.0), (HANDLE_Y[1], FRONT_Z - 7.0)]
LED_HOLE = 8.0
LED_BEZEL, LED_BEHIND, LED_NUT = (10.8, 8.8, 4.3), 11.0, 9.4   # the nut across its flats
LED_COLORS = ["#3fa34d", "#e08a1e"]
INLET = (28.0, FAN_T + 13.0)   # C14 inlet lying flat, low on the rear panel: Y and Z of its centre
# The inlet is the moulded end of the mains lead, Toptekits' screw-mount C14 to right-angle C13, measured
# from the part: body 27.2 x 19.2, flange 48.9 wide, as tall as the body and 3.0 thick, rigid for 50 from
# the flange's face, and 20.5 in of cable, 7 across, between the mouldings. The cut-out is Schurter's for
# the 6100-3, which the lead's seller draws too.
INLET_BODY, INLET_FLANGE, INLET_BLOCK = (27.2, 19.2), (48.9, 19.2, 3.0), 47.0
LEAD, LEAD_LENGTH = 7.0, 520.7
# Its C13 plug stands 17 above the supply and points its cable at the tray's side. How far the plug
# reaches that way from the middle of the inlet, its width, and the cable's height where it leaves are
# guesses.
PLUG = (20.0, 19.5, 17.0)
PLUG_CABLE = 12.0                              # the cable's middle above the supply's top
# The lead as it lies, in four flat pieces. It climbs across the top of the supply toward the tray,
# veering toward the front to make room for its turn; arches through the notch and down into the gap
# between the board and the supply; runs down the tray past the tie slots; then goes across the bottom
# toward the open side and, after one turn, back to the inlet. The bends' radii: over the supply,
# through the notch (18 is what passes between the notch's two edges), at the tray's foot, on the bottom.
LEAD_BENDS = (25.0, 18.0, 20.0, 30.0)
LEAD_GAP_X = 176.8                             # where it goes down the gap: 1.2 from the board, 2.1 from the shelf's wall
LEAD_ARCH = PSU_TOP + 5.5                      # the arch's middle: the cable passes 0.3 from the trim above and below
LEAD_Y = TRAY_Y - 1.0 - LEAD / 2                # in the notch and down the tray, 1.0 from the tray
# The switch's and the lamps' wires, each a twisted pair that fits a 2.5 circle. They go through the notch
# beside the mains lead, one above another, and on to a plug on the board's 9-pin power header, which is
# at the top front corner of Framework's board (its 618013-009101: X, Y and Z of its body in the case).
# The plug, and which pin each wire goes to, are not known: the plug is a block and the wires enter it
# side by side.
WIRE = 2.5
STRAND, TWIST_PITCH = 1.2, 12.0                # each conductor, and the length of one turn of the pair
WIRE_Y = LEAD_NOTCH[0] + TRIM + WIRE / 2 + 0.25
WIRE_Z = [PSU_TOP + 12.0 + 2.6 * k for k in range(3)]   # in the notch: lower lamp, upper lamp, switch
WIRE_COLORS = [("#e08a1e", BLACK), ("#3fa34d", BLACK), ("#e6e6e6", BLACK)]
HEADER = ((143.9, 156.5), (107.2, 118.7), (185.0, 190.0))
HEADER_PLUG = 7.2                              # how far the plug stands off the header, a guess
# The 24-pin and CPU cables, every wire drawn. On the board both connectors are part of Framework's
# envelope body: X and Z of each in the case, and Y of its top. On the supply the sockets are scaled from
# Corsair's picture of the SF750's panel, 125 x 63.5: along the panel from its left end and down from its
# top edge, as the picture has it. The lid is at the picture's top and the fan underneath, so here, with
# the fan toward the board and the panel facing down, the picture's left is the open side and its top the
# front. The 24-pin cable has two plugs at the supply, 18 and 10 pins; nine columns of wires are drawn
# from the first and three from the second, which is not Corsair's pinout. The CPU cable is in the first
# of the three 8-pin sockets.
DC_WIRE, DC_PITCH = 2.3, 4.2
ATX24 = ((55.22, 108.0), (40.23, 51.55))
CPU8 = ((118.02, 137.2), (35.25, 46.57))
DC_HEADER_Y, DC_PLUG = 102.87, 10.0            # the board connectors' tops, and how far a plug stands off one
PSU_ATX18, PSU_ATX10, PSU_CPU = ((33.8, 73.1), (13.9, 23.8)), ((9.8, 32.5), (13.9, 23.8)), ((9.8, 28.5), (26.6, 36.9))
PSU_PLUG = 13.0                                # how far a plug hangs under the supply, a guess
# The wires leave the supply downward and turn toward the rear. The CPU's socket is behind the 24-pin's
# ten, so those three columns lean toward the tray on the way down, to pass beside the CPU's wires, and
# the eighteen's close up from 4.2 to 2.6 apart beside them: a band twelve wide and two deep, with the
# CPU's four under its edge. All run rearward and turn into the board's plugs, the CPU's passing under
# the band. Y of the band's first lane, the lanes' pitch, the bends' radius, and how far along X the
# closing up takes.
DC_LANE, DC_LANE_PITCH, DC_TURN, DC_CLOSE = 28.6, 2.6, 8.0, 38.0
CPU_UNDER = 2.39                               # the CPU's upper row runs this far over its lower one, under the 24-pin's
WIRE_PAST_WALL = 181.5                         # X where the wires' two pieces meet, just behind the shelf's wall

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
                                "clientInfo": {"name": "reactor", "version": "0"}})
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


def lip_flat(c):
    """Where a point c up a lip, from the inside face of the panel it is folded from, lies in the flat:
    its distance inside the panel's edge at Y = 0, which a negative result puts outside. The panel's
    own flat part ends at BEND_R."""
    return 2 * BEND_R - math.pi / 2 * (BEND_R + K_FACTOR * T) - c


LIP_ROOT = BEND_R - math.pi / 2 * (BEND_R + K_FACTOR * T)   # c of the panel's flat edge, where the bend starts


def both_sides(poly):
    """An outline drawn on the open side's lip in the flat, and its mirror image on the tray side's."""
    return [("poly", [[round(a, 4), round(b, 4)] for a, b in pts]) for pts in (poly, [(LY - a, b) for a, b in poly])]


XY = plane([0, 0, -3], [1, 0, 0], [0, 1, 0])           # looks up through the bottom
TOP = plane([0, 0, LZ - 3], [1, 0, 0], [0, 1, 0])
REAR = plane([-4, 0, 0], [0, 1, 0], [0, 0, 1])         # sketch (Y, Z), cuts toward the front
TRAY = plane([0, TRAY_Y + T + 3, 0], [1, 0, 0], [0, 0, 1])   # sketch (X, Z), cuts toward the board
SIDE = plane([0, LY + T + 1, 0], [1, 0, 0], [0, 0, 1])       # the same from outside the side lips


def near(points, r):
    return lambda x, y: any(math.hypot(x - px, y - py) < r for px, py in points)


def core():
    """Bottom and rear in one part; the fans and the tray fasten to it. The rear panel's top
    lip lies under the top panel, which the rear handle's two screws clamp to it."""
    w = LY + 2 * T
    xf = LX + T
    lip = lambda p: {"point": p, "height": str(SIDE_LIP)}
    wide = lambda p: {"point": p, "height": str(JOIN_LIP)}
    s = [("sketch.create", {"plane": "XZ", "offset": str(-T), "name": "core-profile"}),
         ("sketch.line", {"points": [[-T, -LZ], [-T, T], [xf, T]]}),
         ("sketch.finish", {}),
         ("sheet.flange", {"sketch": "core-profile", "curves": ["l1", "l2"], "distance": str(w),
                           "body_name": "core"}),
         ("sheet.flange", {"body": "core", "height": str(FLANGE), "flip": True, "edges": [
             {"point": [xf, LY / 2, -T], "height": str(LIP_BOTTOM)},
             lip([LX / 2, -T, -T]), wide([LX / 2, LY + T, -T]),
             {"point": [-T, -T, LZ / 2], "height": str(REAR_LIP)}, wide([-T, LY + T, LZ / 2]),
             {"point": [-T, LY / 2, LZ], "height": str(TOP_LIP)}]})]
    # The side lips are mitred where the hood's meet them: the rear panel's at the top and the bottom
    # panel's at the front. SolidCraft will not cut across a folded bend, so the core is unfolded for it,
    # the bottom panel lying out below the rear one and each lip beside its panel, and folded again. z
    # here is where a point x along the bottom panel lies in that flat.
    flat = lip_flat
    xi, far = MOUNT_X[0], 25.0
    # with it, the ends of the rear panel's top lip come off, 0.3 clear of the bend of the hood's side lip
    clear, lip0 = BEND_R + 0.3, LZ - T - BEND_R
    rear = [(BEND_R, LZ - LIP_ROOT - MITRE), (flat(far), LZ - far - MITRE), (flat(far), LZ + 30), (clear, LZ + 30),
            (clear, lip0), (BEND_R, lip0)]
    foot = [(BEND_R, flat(xi - LIP_ROOT - MITRE)), (flat(far), flat(xi - far - MITRE)), (flat(far), flat(xi + 45)),
            (BEND_R, flat(xi + 45))]
    s += [("sheet.unfold", {"body": "core"})]
    s += cut("core-mitres", plane([-T - 0.5, 0, 0], [0, 1, 0], [0, 0, 1]), both_sides(rear) + both_sides(foot), T + 1, ["core"])
    s += [("sheet.refold", {"body": "core"})]
    # rear panel: the standard I/O aperture and the mains inlet with its two screws
    iy, iz = INLET
    rear = [(IO_Y[0], IO_Z[0], IO_Y[1], IO_Z[1]), ("round", iy - 14, iz - 10, iy + 14, iz + 10, 1.0),
            (iy - 20, iz, M3_CLEAR), (iy + 20, iz, M3_CLEAR)]
    s += cut("rear-cuts", REAR, rear, 5, ["core"])
    pad = near(FEET, FOOT_PAD + HEX_AF / 2)
    s += cut("bottom-mesh", XY, mesh(BOTTOM_FANS, pad)
             + [(x, y, STUD_632) for x, y in FEET], 5, ["core"])
    # The top lip is its full length only at the two corners, under the rear handle's legs; between them
    # it stops short of the mesh's first row of cells.
    a, b = TOP_LIP_TABS
    s += cut("top-lip", plane([0, 0, LZ - T - 0.5], [1, 0, 0], [0, 1, 0]),
             [(TOP_LIP_MID - T, a, TOP_LIP + 1, b)], T + 1, ["core"])
    front = plane([LX - 0.2, 0, 0], [0, 1, 0], [0, 0, 1])
    # SolidCraft will not cut a countersink in a sheet metal part, so these are plain holes and the
    # countersinks for the rivets' heads are made by hand: see the drawing.
    s += cut("lip-joins", TRAY, [(x, z, RIVET_HOLE) for x, z in TRAY_JOINS if z < LZ - JOIN_LIP and x < LIP_END], 5, ["core"])
    for name, y in (("lip-nuts", -T - 0.3), ("lip-nuts-tray", LY - 0.3)):
        s += cut(name, plane([0, y, 0], [0, 0, 1], [1, 0, 0]), [(z, x, NUT_632) for x, z in SIDE_SCREWS if x < LX / 2],
                 T + 0.6, ["core"])
    s += rounds("front-lip-corners", front, [(BEND_R, LIP_BOTTOM - T, 1, -1), (LY - BEND_R, LIP_BOTTOM - T, -1, -1)], 2.5, ["core"])
    return s


def hood():
    """The top and the front in one part. The top lies on the rear panel's top lip, which the rear
    handle's two screws clamp it to, and its lip on the tray's side is riveted to the tray. The front has
    a flange down each side, which the side panels screw to and the tray is riveted to on its side, and a
    return under the bottom panel with two tabs for the front fan's front screws. The switch and the
    lamps are fixed in it."""
    w = LY + 2 * T
    zt, xf, zr = LZ + T, SHELL_XF, HOOD_Z0
    s = [("sketch.create", {"plane": "XZ", "offset": str(-T), "name": "hood-profile"}),
         ("sketch.line", {"points": [[xf, -zr], [xf, -zt], [-T, -zt]]}),
         ("sketch.finish", {}),
         ("sheet.flange", {"sketch": "hood-profile", "curves": ["l1", "l2"], "distance": str(w), "body_name": "hood"}),
         ("sheet.flange", {"body": "hood", "height": str(FLANGE), "flip": True, "edges": [
             {"point": [xf, LY / 2, zr], "height": str(HOOD_TAB)},
             {"point": [xf, -T, LZ / 2], "height": str(FRONT_FLANGE)}, {"point": [xf, LY + T, LZ / 2], "height": str(FRONT_FLANGE)},
             {"point": [LX / 2, -T, zt], "height": str(SIDE_LIP)}, {"point": [LX / 2, LY + T, zt], "height": str(JOIN_LIP)}]})]
    # The top's side lips and the front's flanges are mitred where the core's lips meet them, and the
    # return under the bottom stops short of the side panels' returns: all cut in the flat, as on the
    # core. The front stays put and the top lies out above it; `flat` is where a point x along the top
    # lies in that flat. The flanges' bends stop 1.6 above the bottom panel, clear of the bends of its lips.
    d = T + BEND_R
    flat = lambda x: zt + xf - 2 * d + math.pi / 2 * (BEND_R + K_FACTOR * T) - x
    far = 25.0
    top_lip = [(BEND_R, flat(LIP_ROOT + MITRE)), (lip_flat(far), flat(far + MITRE)), (lip_flat(far), flat(-T) + 40),
               (BEND_R, flat(-T) + 40)]
    ra, low = HOOD_RETURN_Y[0], 1.6
    foot = [(ra, zr + d), (ra, zr - 60), (lip_flat(far), zr - 60), (lip_flat(far), far + MITRE),
            (lip_flat(low - MITRE), low), (BEND_R, low), (BEND_R, zr + d)]   # one outline: flange, its bend and the return's end
    s += [("sheet.unfold", {"body": "hood"})]
    s += cut("hood-flat", plane([xf - T - 0.5, 0, 0], [0, 1, 0], [0, 0, 1]),
             both_sides(top_lip) + both_sides(foot), T + 1, ["hood"])
    s += [("sheet.refold", {"body": "hood"})]
    # the rear handle's screws go through the core's top lip as well, and the mesh's cells take the
    # corners off its tabs
    s += cut("top-mesh", TOP, top_mesh() + [(x, y, LOOSE_632) for x, y in HANDLE_HOLES], 6, ["hood", "core"])
    s += cut("hood-joins", TRAY, [(x, z, RIVET_HOLE) for x, z in TRAY_JOINS if z > LZ - JOIN_LIP or x > LIP_END], 5, ["hood"])
    for name, y in (("hood-nuts", -T - 0.3), ("hood-nuts-tray", LY - 0.3)):
        s += cut(name, plane([0, y, 0], [0, 0, 1], [1, 0, 0]), [(z, x, NUT_632) for x, z in SIDE_SCREWS if x > LX / 2],
                 T + 0.6, ["hood"])
    s += cut("hood-front", plane([xf - T - 0.15, 0, 0], [0, 1, 0], [0, 0, 1]),
             [SWITCH + (SWITCH_HOLE,)] + [p + (LED_HOLE,) for p in LEDS], T + 0.3, ["hood"])
    # The return is its full length only under the two fan screws, and each tab's inner corner comes off
    # at a slant, 0.6 clear of the front foot's flange.
    a, b = HOOD_TABS
    xm, xt = xf - HOOD_RETURN, xf - HOOD_TAB
    h = FAN_HOLES / 2
    c = [(xm, a), (xm - 2.9, a), (xt, a - 3.0), (xt - 1, a - 3.0)]
    between = c + [(x, LY - y) for x, y in reversed(c)]
    s += cut("hood-return", plane([0, 0, zr - 0.5], [1, 0, 0], [0, 1, 0]),
             [("poly", [[round(x, 3), round(y, 3)] for x, y in between])]
             + [(BOTTOM_FANS[1][0] + h, LY / 2 + j * h, FAN_CLEAR) for j in (-1, 1)], T + 1, ["hood"])
    return s


def top_mesh():
    return mesh([TOP_FAN], lambda x, y: False, [(x, y, LOOSE_632) for x, y in SHELF_SCREWS + SHELF_FRONT_SCREWS])


def tray():
    """A flat plate the length of the case, riveted to the side lips of the bottom, rear and top
    panels and to the front's flange. No flange at the rear: the I/O aperture's keepout reaches to within 5 mm of it."""
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
    holes += [(x, z, RIVET_HOLE) for x, z in TRAY_JOINS]
    # a notch in from the rear or front edge round each nut for a side panel screw in the lip the tray lies against
    for sx, sz in SIDE_SCREWS:
        a, b = (x0 - 2 * NUT_NOTCH, sx + NUT_NOTCH / 2) if sx < LX / 2 else (sx - NUT_NOTCH / 2, x1 + 2 * NUT_NOTCH)
        holes.append(("round", a, sz - NUT_NOTCH / 2, b, sz + NUT_NOTCH / 2, NUT_NOTCH / 2 - 0.1))
    holes += [("round", TIE_X + d - TIE_SLOT[0] / 2, z - TIE_SLOT[1] / 2, TIE_X + d + TIE_SLOT[0] / 2,
               z + TIE_SLOT[1] / 2, 0.9) for z in TIE_Z for d in (-TIE_APART / 2, TIE_APART / 2)]
    s += cut("tray-cuts", TRAY, holes, 5, ["tray"])
    s += rounds("tray-corners", TRAY, [(x0, EDGE, 1, 1), (x1, EDGE, -1, 1), (x0, LZ - EDGE, 1, -1),
                                       (x1, LZ - EDGE, -1, -1)], 5, ["tray"])
    return s


def shelf():
    """The PSU screws up against its underside, exhaust face up. It hangs from the top panel on four screws,
    into nuts in two tabs folded from its rear wall and two from its front wall. The rear wall shuts the
    space above the PSU off from the rest of the case, so the exhaust can only leave through the top mesh;
    the front panel, the side panel and the tray close the other sides."""
    zt = LZ - 0.1
    zb = zt - T - BEND_R    # where the tabs' bends start
    ya, yb = 0.4, TRAY_Y - GAP
    xr, xf = SHELF_X
    f = SHELF_FLANGE
    s = [("sketch.create", {"plane": plane([0, yb, 0], [1, 0, 0], [0, 0, 1]), "name": "shelf-profile"}),
         ("sketch.line", {"points": [[xf, zb], [xf, PSU_TOP], [xr, PSU_TOP], [xr, zb]]}),
         ("sketch.finish", {}),
         ("sheet.flange", {"sketch": "shelf-profile", "curves": ["l1", "l2", "l3"],
                           "distance": str(yb - ya), "body_name": "shelf"})]
    # The front wall stands only between the switch and the lamps. SolidCraft will not cut across a
    # folded bend, so its two ends are cut off in the flat, where the front wall stays put and its bend
    # lies out below it.
    wa, wb = SHELF_FRONT_WALL
    low = PSU_TOP + T + BEND_R - math.pi / 2 * (BEND_R + K_FACTOR * T) - 0.2
    inside = plane([xf - T - 0.5, 0, 0], [0, 1, 0], [0, 0, 1])
    s += [("sheet.unfold", {"body": "shelf"})]
    s += cut("shelf-front-ends", inside, [(ya - 5, low, wa, zb + 40), (wb, low, yb + 5, zb + 40)], T + 1, ["shelf"])
    s += [("sheet.refold", {"body": "shelf"})]
    # Its two tabs fold toward the rear, each with a relief slot at both sides.
    k = SHELF_FRONT_TAB / 2
    tabs = [y for x, y in SHELF_FRONT_SCREWS]
    s += cut("shelf-front-reliefs", inside, [(y + e * k + (0 if e > 0 else -2), zb - 3, y + e * k + (2 if e > 0 else 0), zb + 1)
                                              for y in tabs for e in (-1, 1)], T + 1, ["shelf"])
    ft = round(xf - SHELF_FRONT_SCREWS[0][0] + 5.6, 3)
    s += [("sheet.flange", {"body": "shelf", "height": str(ft), "flip": TAB_FLIP, "position": TAB_POSITION, "edges": [
        [xf - T, y, zb] for y in tabs]})]
    # Each tab loses whatever would show in a cell of the mesh above it, as the rear tabs do.
    hx, hy = HEX_AF / 2, HEX_K * HEX_AF / math.sqrt(3)
    showing = [c for c in top_mesh() if c[0] == "hex" and c[1] + hx > xf - ft and c[1] + hx < xf - 2 * T - BEND_R
               and any(abs(c[2] - y) < k + hy for y in tabs)]
    s += cut("shelf-front-nuts", plane([0, 0, zb + 0.5], [1, 0, 0], [0, 1, 0]),
             showing + [(x, y, NUT_632) for x, y in SHELF_FRONT_SCREWS], 2 * T, ["shelf"])
    # The rear wall is straight, with a tab folded over at each side for the screws and a relief slot
    # beside each. SolidCraft folds only one flange feature on a side of a panel and levels the whole
    # side to where its bends start, so the straight part stops one bend (2.4) short of the tabs' tops
    # and of the top panel. It could not be made to model the straight part carried on up.
    # Each tab's inner edge is 5.6 from its nut. The tab on the open side starts clear of the bend of
    # the top panel's side lip.
    a, b = SHELF_SCREWS[0][1] + 5.6, SHELF_SCREWS[1][1] - 5.6
    y0 = EDGE
    s += cut("shelf-reliefs", plane([xr - 2, 0, 0], [0, 1, 0], [0, 0, 1]),
             [(a, zb - 3, a + 2, zb + 1), (b - 2, zb - 3, b, zb + 1), (ya - 1, zb - 3, y0, zb + 1),
              ("round", LEAD_NOTCH[0], LEAD_NOTCH[1], yb + 2 * LEAD_NOTCH[3], LEAD_NOTCH[2], LEAD_NOTCH[3])], 4, ["shelf"])
    s += [("sheet.flange", {"body": "shelf", "height": str(f), "flip": TAB_FLIP, "position": TAB_POSITION, "edges": [
        [xr, (y0 + a) / 2, zb], [xr, (b + yb) / 2, zb]]})]
    web = [("round", PSU_X + 8, PSU_Y + 12, PSU_X + 55.5, PSU_Y + 113, 3)]
    web += [(PSU_X + u, PSU_Y + v, CLEAR_632) for u, v in PSU_HOLES + PSU_HOLES_SPARE]
    s += cut("shelf-web", plane([0, 0, PSU_TOP - 2], [1, 0, 0], [0, 1, 0]), web, 5, ["shelf"])
    # Each tab loses the corners that would show in the cells beside its screw's. The cell on the wall's
    # side of the screw's is over the tab's root and bend, which have to be there. The tabs fold toward
    # the rear, and this is worked out mirrored in the wall, as if they folded forward.
    mx = lambda x: 2 * xr + T - x
    cells = [("hex", mx(c[1]), c[2]) for c in top_mesh() if c[0] == "hex"]
    h, clear = HEX_AF / 2, 2 * T + 0.2
    beside = [c for c in cells if xr + clear <= c[1] - h < xr + f and not a + 6 < c[2] < b - 6]
    # The cells of the next row inward that lie over the bend still catch the tab's edge with their
    # points. A cut may not reach the bend, so only the point comes off the tab, and only clear of
    # the bend; what is left in those cells is the bend itself.
    rows = [y for x, y in SHELF_SCREWS]
    v = HEX_K * HEX_AF / math.sqrt(3)
    for c in cells:
        if (c[1] - h < xr + clear < c[1] + h and min(abs(c[2] - y) for y in rows) > 1
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
            beside.append(("poly", pts))
    beside = [("hex", mx(c[1]), c[2]) if c[0] == "hex" else ("poly", [[round(mx(x), 3), round(y, 3)] for x, y in c[1]])
              for c in beside]
    s += cut("shelf-tabs", plane([0, 0, zb + 0.5], [1, 0, 0], [0, 1, 0]),
             beside + [(x, y, NUT_632) for x, y in SHELF_SCREWS], 2 * T, ["shelf"])
    s += rounds("shelf-tab-corners", plane([0, 0, zb + 0.5], [1, 0, 0], [0, 1, 0]),
                [(round(xr + T - f, 4), y0, 1, 1), (round(xr + T - f, 4), yb, 1, -1)], 2 * T, ["shelf"])
    return s


def side(name, y, inward):
    """A side panel: flat, with a flange over the top and one under the bottom, and a screw near each
    corner. Both sides are the same part. `y` is its outside face and `inward` the direction of the other one."""
    z0, z1 = SHELL_Z0, SHELL_Z1
    xe = SHELL_XF
    line = [[xe, y], [-T, y]] if inward > 0 else [[-T, y], [xe, y]]
    through = plane([0, y - 0.5 if inward > 0 else y - T - 0.5, 0], [0, 0, 1], [1, 0, 0])
    s = [("sketch.create", {"plane": plane([0, 0, z0], [1, 0, 0], [0, 1, 0]), "name": name + "-profile"}),
         ("sketch.line", {"points": line}),
         ("sketch.finish", {}),
         ("sheet.flange", {"sketch": name + "-profile", "curves": ["l1"], "distance": str(z1 - z0), "body_name": name}),
         ("sheet.flange", {"body": name, "height": str(SHELL_RETURN), "flip": True, "edges": [[LX / 2, y, z1]]}),
         ("sheet.flange", {"body": name, "height": str(SHELL_RETURN), "flip": True, "edges": [[LX / 2, y, z0]]})]
    s += cut(name + "-screws", through, [(z, x, LOOSE_632) for x, z in SIDE_SCREWS], T + 1, [name])
    # free corners of the flanges
    t = y + inward * SHELL_RETURN
    for where, z in (("top", z1 - T - 0.5), ("bottom", z0 - 0.5)):
        s += rounds("%s-corners-%s" % (name, where), plane([0, 0, z], [1, 0, 0], [0, 1, 0]),
                    [(xe, t, -1, -inward), (-T, t, 1, -inward)], T + 1, [name])
    return s


# rivets, tray to the side lips of the bottom, top and rear panels, three in each, and two to the
# front's flange: X and Z
TRAY_JOINS = ([(x, z) for x in (40, LX / 2, LX - 40) for z in (JOIN_IN, LZ - JOIN_IN)]
              + [(JOIN_IN, z) for z in (40, LZ / 2, LZ - 40)]   # between the nuts for the side panel's screws
              + [(SHELL_XF - T - JOIN_IN, z) for z in (45, LZ - 27)])   # to the front's flange, below and above the supply


def bought_in():
    bx, bz = BOARD_X, BOARD_Z
    hx, hz = bx + 18.54, bz + BOARD - 136.06     # fan duct square from Framework's drawing
    cx, cz = hx + 63.1, hz + 63.1
    hy = BOARD_Y - HEATSINK
    # the board as a plain block, with another for its rear ports
    s = box(BLOCK_BOARD[0], "#2f7d4f", bx, bx + BOARD, BOARD_Y, BOARD_Y + PCB, bz, bz + BOARD)
    s += box(BLOCK_BOARD[1], "#7d8791", 0.2, 20, BOARD_Y - 31.1, BOARD_Y, bz + 11.5, bz + 143.9)
    s += box("ref-heatsink", "#b8bcc2", hx, hx + 126.2, hy, BOARD_Y - 4, hz, hz + 126.2)
    s += fan("ref-cpu-fan", [cx, hy - FAN_T, cz], [0, 1, 0])
    s += psu()
    s += mains_lead() + edge_trim()
    for i, (fx, fy) in enumerate(BOTTOM_FANS):
        s += fan("ref-fan-bottom-%d" % (i + 1), [fx, fy, 0], [0, 0, 1])
    s += fan("ref-fan-top", [TOP_FAN[0], TOP_FAN[1], LZ], [0, 0, -1])
    return s


def lead_path():
    """The lead's centre line as four flat pieces, each (origin, x_dir, y_dir, pieces) with its pieces as
    lines and arcs in that plane, and its length."""
    r1, r2, r3, r4 = LEAD_BENDS
    sx, sy, sz = PSU_X + PSU_INLET[0], PSU_Y + PSU_INLET[1] + PLUG[0], PSU_TOP + PLUG_CABLE
    ny = LEAD_Y
    ax, az = LEAD_GAP_X + r2, LEAD_ARCH + r2          # top of the arch
    # across the supply: a plane that climbs toward the notch, a veer to the front and a turn to the rear
    tilt = math.atan2(az - sz, ny - sy)
    run = math.hypot(az - sz, ny - sy)
    th = math.acos(((sx - ax) / r1 + 1) / 2)
    p0 = run - r1 * (1 + 2 * math.sin(th))
    e1 = (p0 + r1 * math.sin(th), -r1 * (1 - math.cos(th)))
    c1 = (p0 + 2 * r1 * math.sin(th), r1 * (2 * math.cos(th) - 1))
    a = ([sx, sy, sz], [0, math.cos(tilt), math.sin(tilt)], [-1, 0, 0],
         [("line", (-1, 0), (p0, 0)), ("arc", (p0, -r1), (p0, 0), -math.degrees(th)),
          ("arc", c1, e1, 90 + math.degrees(th))])
    length = p0 + r1 * (math.pi / 2 + 2 * th)
    # through the notch and down the tray
    zr = INLET[1]
    down = az - zr - r3
    b = ([ax, ny, az], [-1, 0, 0], [0, 0, 1], [("arc", (0, -r2), (0, 0), -90), ("line", (r2, -r2), (r2, -down))])
    length += r2 * math.pi / 2 + down - r2
    # round to the bottom
    c = ([LEAD_GAP_X, ny, zr + r3], [0, 0, -1], [0, 1, 0], [("arc", (0, -r3), (0, 0), -90)])
    length += r3 * math.pi / 2
    y0 = ny - r3
    # along the bottom: across toward the open side, one turn, and back to the inlet
    m1 = y0 - INLET[0] - r4
    n_end = LEAD_GAP_X - (INLET_BLOCK - T) + 1
    d = ([LEAD_GAP_X, y0, zr], [0, -1, 0], [-1, 0, 0],
         [("line", (0, 0), (m1, 0)), ("arc", (m1, r4), (m1, 0), 90), ("line", (m1 + r4, r4), (m1 + r4, n_end))])
    length += m1 + r4 * math.pi / 2 + n_end - 1 - r4
    return [a, b, c, d], length


def mains_lead():
    """The mains lead: its C14 through the rear panel with a flange outside, held by two countersunk M3
    screws, the cable, and its C13 in the supply."""
    iy, iz = INLET
    (bw, bh), (fw, fh, ft) = INLET_BODY, INLET_FLANGE
    n = "ref-mains-inlet"
    s = box(n, "#2b2e33", -T - ft, INLET_BLOCK - T, iy - bw / 2, iy + bw / 2, iz - bh / 2, iz + bh / 2)
    s += [("solid.box", {"length": ft, "width": fw, "height": fh, "corner": [-T - ft, iy - fw / 2, round(iz - fh / 2, 3)],
                         "operation": "join", "targets": [n]}),
          ("solid.box", {"length": 14, "width": 23, "height": 15, "corner": [-T - ft, iy - 11.5, iz - 7.5],
                         "operation": "cut", "targets": [n]})]
    px, py = PSU_X + PSU_INLET[0], PSU_Y + PSU_INLET[1]
    s += box("ref-mains-plug", "#2b2e33", px - PLUG[1] / 2, px + PLUG[1] / 2, py - 13.75, py + PLUG[0], PSU_TOP, PSU_TOP + PLUG[2])
    for i, (origin, xd, yd, pieces) in enumerate(lead_path()[0]):
        s += pipe("ref-mains-lead-%d" % (i + 1), origin, xd, yd, pieces, LEAD, BLACK)
    return s


def pipe(n, origin, xd, yd, pieces, diameter, color, into=None):
    """A round cable along lines and arcs drawn in one plane, each ending exactly where the next starts.
    With `into`, it is joined to that body."""
    if into:
        return pipe(n, origin, xd, yd, pieces, diameter, color)[:-3] + [
            ("solid.pipe", {"path_sketch": "sk-" + n, "path": curve_names(pieces), "diameter": diameter,
                            "operation": "join", "targets": [into]}),
            ("browser.visibility", {"visible": False, "items": ["sk-" + n]})]
    s = [("sketch.create", {"plane": plane(origin, xd, yd), "name": "sk-" + n})]
    names, count = [], {"line": 0, "arc": 0}
    for piece in pieces:
        count[piece[0]] += 1
        names.append("%s%d" % (piece[0][0], count[piece[0]]))
        if piece[0] == "line":
            s.append(("sketch.line", {"points": [list(piece[1]), list(piece[2])], "connect": False, "infer": False}))
        else:
            s.append(("sketch.arc.center_point", {"center": list(piece[1]), "start": list(piece[2]), "sweep": piece[3],
                                                  "connect": False}))
    return s + [("sketch.finish", {}),
                ("solid.pipe", {"path_sketch": "sk-" + n, "path": names, "diameter": diameter, "body_name": n}),
                ("browser.visibility", {"visible": False, "items": ["sk-" + n]})] + paint([n], color)


def curve_names(pieces):
    names, count = [], {"line": 0, "arc": 0}
    for piece in pieces:
        count[piece[0]] += 1
        names.append("%s%d" % (piece[0][0], count[piece[0]]))
    return names


def psu_columns(sock):
    """Y of a supply socket's columns of pins, from the open side, and X of the middle of its two rows."""
    (a0, a1), (b0, b1) = sock
    k = round((a1 - a0) / DC_PITCH)
    return ([PSU_Y + (a0 + a1) / 2 + DC_PITCH * (j - (k - 1) / 2) for j in range(k)], PSU_X + PSU[0] - (b0 + b1) / 2)


def dc_paths():
    """Every wire of the 24-pin and CPU cables as (name, [flat pieces as for lead_path], length)."""
    out = []
    plug_y = DC_HEADER_Y - DC_PLUG
    zs = PSU_TOP - PSU[2] - PSU_PLUG                 # where the wires leave the supply's plugs
    rt = DC_TURN
    ten, x10 = psu_columns(PSU_ATX10)
    eighteen, x18 = psu_columns(PSU_ATX18)
    four, x4 = psu_columns(PSU_CPU)
    atx_y = ten[-3:] + eighteen
    atx_lane = [DC_LANE + DC_LANE_PITCH * c for c in range(12)]
    atx_pass = atx_lane[:3] + eighteen               # Y of each as it turns rearward: the ten's are in their lanes by then
    for cable, (bx, bz), psu_x, ys, passes, lanes in (("atx", ATX24, x18, atx_y, atx_pass, atx_lane),
                                                      ("cpu", CPU8, x4, four, four, four)):
        cols = len(ys)
        zc = (bz[0] + bz[1]) / 2
        for row in range(2):                             # 0 the lower row on the board, from the supply's front row
            z_plug = zc + (row - 0.5) * DC_PITCH
            z = z_plug if cable == "atx" or row == 0 else zc - 0.5 * DC_PITCH + CPU_UNDER
            xp = psu_x + (0.5 - row) * DC_PITCH
            x_s = xp - max(math.hypot(passes[c] - ys[c], zs + 1 - z) for c in range(cols))
            for c in range(cols):
                n = "wire-%s-%d-%02d" % (cable, row + 1, c + 1)
                yp, yq, lane = ys[c], passes[c], lanes[c]
                xb = (bx[0] + bx[1]) / 2 + DC_PITCH * (c - (cols - 1) / 2)
                fall = math.hypot(yq - yp, zs + 1 - z)
                r = fall - 1
                down = ([xp, yp, zs + 1], [0, (yq - yp) / fall, -(zs + 1 - z) / fall], [-1, 0, 0],
                        [("line", (0, 0), (1, 0)), ("arc", (1, r), (1, 0), 90), ("line", (1 + r, r), (1 + r, xp - x_s))])
                length = fall - 1 + r * math.pi / 2 + xp - x_s - r
                d, adv = yq - lane, DC_CLOSE
                at = x_s - xb - rt
                if abs(d) < 0.05:
                    flat = [("line", (0, 0), (at, 0))]
                    length += at
                else:
                    rs = (adv * adv + d * d) / (4 * d)
                    if rs > 30.0:    # a small step: SolidCraft refuses to join a pipe bent to a very large radius
                        rs = 30.0
                        adv = 2 * rs * math.sin(math.acos(1 - d / (2 * rs)))
                    th = math.atan2(adv / (2 * rs), 1 - d / (2 * rs))
                    flat = [("arc", (0, rs), (0, 0), math.degrees(th)),
                            ("arc", (adv, d - rs), (rs * math.sin(th), rs * (1 - math.cos(th))), -math.degrees(th)),
                            ("line", (adv, d), (at, d))]
                    length += 2 * rs * th + at - adv
                flat.append(("arc", (at, d - rt), (at, d), -90))
                length += rt * math.pi / 2
                leg = plug_y - lane - rt
                pieces = [down, ([x_s, yq, z], [-1, 0, 0], [0, -1, 0], flat)]
                if z == z_plug:
                    flat.append(("line", (at + rt, d - rt), (at + rt, d - rt - leg - 1)))
                else:                                    # up into the plug, once past the 24-pin's band
                    h = z_plug - z
                    t2 = math.acos(1 - h / (2 * rt))
                    s0 = leg - 2 * rt * math.sin(t2)
                    pieces.append(([xb, lane + rt, z], [0, 1, 0], [0, 0, 1],
                                   [("line", (0, 0), (s0, 0)), ("arc", (s0, rt), (s0, 0), math.degrees(t2)),
                                    ("arc", (leg, h - rt), (s0 + rt * math.sin(t2), rt * (1 - math.cos(t2))), -math.degrees(t2)),
                                    ("line", (leg, h), (leg + 1, h))]))
                    length += 2 * rt * t2 - 2 * rt * math.sin(t2)
                out.append((n, pieces, length + leg))
    return out


def dc_cables():
    """The 24-pin and CPU cables: a plug at each end and every wire between."""
    plug_y = DC_HEADER_Y - DC_PLUG
    z0, z1 = PSU_TOP - PSU[2] - PSU_PLUG, PSU_TOP - PSU[2] - 0.05
    s = []
    for n, (bx, bz) in (("ref-plug-atx24", ATX24), ("ref-plug-cpu8", CPU8)):
        s += box(n, "#2b2e33", bx[0], bx[1], plug_y, DC_HEADER_Y - 0.05, bz[0], bz[1])
    for n, ((a0, a1), (b0, b1)) in (("ref-plug-psu-atx18", PSU_ATX18), ("ref-plug-psu-atx10", PSU_ATX10),
                                    ("ref-plug-psu-cpu", PSU_CPU)):
        s += box(n, "#2b2e33", PSU_X + PSU[0] - b1, PSU_X + PSU[0] - b0, PSU_Y + a0, PSU_Y + a1, z0, z1)
    for n, pieces, length in dc_paths():
        for i, (origin, xd, yd, pcs) in enumerate(pieces):
            s += pipe("%s-%d" % (n, i + 1) if i else n, origin, xd, yd, pcs, DC_WIRE, BLACK, into=n if i else None)
    return s


def wire_paths():
    """The three wires, each as (name, [flat pieces as for lead_path], length): from its part above the
    supply to just behind the shelf's wall, and from there to the plug on the board's header."""
    unit = lambda v: [c / math.sqrt(sum(d * d for d in v)) for c in v]
    back = [-1, 0, 0]
    out = []
    plug_y = HEADER[1][0] - HEADER_PLUG
    zp = (HEADER[2][0] + HEADER[2][1]) / 2
    starts = [("wire-led-2", [MOUNT_X[1] - LED_BEHIND, LEDS[1][0], LEDS[1][1]]),
              ("wire-led-1", [MOUNT_X[1] - LED_BEHIND, LEDS[0][0], LEDS[0][1]]),
              ("wire-switch", [MOUNT_X[1] - 22, SWITCH[0], SWITCH[1]])]
    for k, (n, p) in enumerate(starts):
        zk = WIRE_Z[k]
        o = [p[0] + 0.5, p[1], p[2]]
        a_end = o[0] - WIRE_PAST_WALL
        if k < 2:   # a lamp: an S to the notch's height, then straight back
            b = math.hypot(WIRE_Y - o[1], zk - o[2])
            r = 6.0
            th = math.acos(1 - b / (2 * r))
            front = (o, back, unit([0, WIRE_Y - o[1], zk - o[2]]),
                     [("line", (0, 0), (1, 0)), ("arc", (1, r), (1, 0), math.degrees(th)),
                      ("arc", (1 + 2 * r * math.sin(th), b - r), (1 + r * math.sin(th), r * (1 - math.cos(th))), -math.degrees(th)),
                      ("line", (1 + 2 * r * math.sin(th), b), (a_end, b))])
            length = 1 + 2 * r * th + a_end - 1 - 2 * r * math.sin(th)
        else:       # the switch: back, across behind the mains plug, and back again through the notch
            b = math.hypot(WIRE_Y - o[1], zk - o[2])
            r = 8.0
            a1 = a_end - 4.5 - 2 * r
            front = (o, back, unit([0, WIRE_Y - o[1], zk - o[2]]),
                     [("line", (0, 0), (a1, 0)), ("arc", (a1, r), (a1, 0), 90), ("line", (a1 + r, r), (a1 + r, b - r)),
                      ("arc", (a1 + 2 * r, b - r), (a1 + r, b - r), -90), ("line", (a1 + 2 * r, b), (a_end, b))])
            length = a1 + r * math.pi + b - 2 * r + a_end - a1 - 2 * r
        # behind the wall, level: an S toward the open side and a turn toward the board, each wire 3 outside
        # the one below it; then, side by side, an S up or down into the plug
        yk = plug_y - 10.0 - 3.0 * k
        d = WIRE_Y - yk
        xk = (HEADER[0][0] + HEADER[0][1]) / 2 + 1.3 - 3.0 * k
        at = WIRE_PAST_WALL - xk - 6.0
        adv = at - 0.5
        r = (adv * adv + d * d) / (4 * d)
        th = math.atan2(adv / (2 * r), 1 - d / (2 * r))
        rear = ([WIRE_PAST_WALL, WIRE_Y, zk], back, [0, -1, 0],
                [("arc", (0, r), (0, 0), math.degrees(th)),
                 ("arc", (adv, d - r), (r * math.sin(th), r * (1 - math.cos(th))), -math.degrees(th)),
                 ("line", (adv, d), (at, d)), ("arc", (at, d - 6.0), (at, d), -90)])
        length += 2 * r * th + 0.5 + 6.0 * math.pi / 2
        h, leg = abs(zp - zk), plug_y - yk - 6.0
        t2 = math.acos(1 - h / 12.0)
        s0 = leg - 12.0 * math.sin(t2)
        drop = ([xk, yk + 6.0, zk], [0, 1, 0], [0, 0, 1 if zp > zk else -1],
                [("line", (0, 0), (s0, 0)), ("arc", (s0, 6.0), (s0, 0), math.degrees(t2)),
                 ("arc", (leg, h - 6.0), (s0 + 6.0 * math.sin(t2), 6.0 * (1 - math.cos(t2))), -math.degrees(t2)),
                 ("line", (leg, h), (leg + 1, h))])
        length += s0 + 12.0 * t2
        out.append((n, [front, rear, drop], length - 0.5))
    return out


def wires():
    """The switch's and lamps' wires and their plug on the board's header."""
    (x0, x1), (y0, y1), (z0, z1) = HEADER
    s = box("ref-front-plug", "#2b2e33", x0 + 0.3, x1 - 0.3, y0 - HEADER_PLUG, y0, z0, z1)
    for k, (n, pieces, length) in enumerate(wire_paths()):
        s += twisted_pair(n, pieces, WIRE_COLORS[k])
    return s


def twisted_pair(n, pieces, colors):
    """Two conductors wound round each other along a wire's flat pieces: each line or arc is swept on its
    own, with whole turns, so that the pair comes out of it lying as it went in and the next one carries on."""
    add = lambda a, b, f=1.0: [a[i] + f * b[i] for i in range(3)]
    cross = lambda a, b: [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]
    dot = lambda a, b: sum(a[i] * b[i] for i in range(3))
    rot = lambda v, deg: (v[0] * math.cos(math.radians(deg)) - v[1] * math.sin(math.radians(deg)),
                          v[0] * math.sin(math.radians(deg)) + v[1] * math.cos(math.radians(deg)))
    s, lie, made = [], None, False
    off = (WIRE - STRAND) / 2
    for i, (origin, xd, yd, pcs) in enumerate(pieces):
        # long lines in shorter lengths, so that no sweep is asked for more than four turns
        cut = []
        for pc in pcs:
            if pc[0] == "line":
                (ax, ay), (bx, by) = pc[1], pc[2]
                m = max(1, math.ceil(math.hypot(bx - ax, by - ay) / 45.0))
                cut += [("line", (ax + (bx - ax) * j / m, ay + (by - ay) * j / m),
                         (ax + (bx - ax) * (j + 1) / m, ay + (by - ay) * (j + 1) / m)) for j in range(m)]
            else:
                cut.append(pc)
        sk = "sk-%s-%d" % (n, i + 1)
        s += [("sketch.create", {"plane": plane(origin, xd, yd), "name": sk})]
        names, count = [], {"line": 0, "arc": 0}
        for pc in cut:
            count[pc[0]] += 1
            names.append("%s%d" % (pc[0][0], count[pc[0]]))
            if pc[0] == "line":
                s.append(("sketch.line", {"points": [list(pc[1]), list(pc[2])], "connect": False, "infer": False}))
            else:
                s.append(("sketch.arc.center_point", {"center": list(pc[1]), "start": list(pc[2]), "sweep": pc[3],
                                                      "connect": False}))
        s += [("sketch.finish", {}), ("browser.visibility", {"visible": False, "items": [sk]})]
        normal = cross(xd, yd)
        to3 = lambda v: add([0, 0, 0], add([c * v[0] for c in xd], [c * v[1] for c in yd]))
        for j, pc in enumerate(cut):
            if pc[0] == "line":
                d = (pc[2][0] - pc[1][0], pc[2][1] - pc[1][1])
                length = math.hypot(*d)
                start, t0 = pc[1], (d[0] / length, d[1] / length)
                t1 = t0
            else:
                c, start, sweep = pc[1], pc[2], pc[3]
                r0 = (start[0] - c[0], start[1] - c[1])
                radius = math.hypot(*r0)
                sign = 1 if sweep > 0 else -1
                t0 = (-sign * r0[1] / radius, sign * r0[0] / radius)
                t1 = rot(t0, sweep)
                length = radius * math.radians(abs(sweep))
            b0, b1 = cross(to3(t0), normal), cross(to3(t1), normal)
            if lie is None:
                lie = normal
            cn, cb = dot(lie, normal), dot(lie, b0)   # how the pair lies, in this plane's terms
            at = add(origin, to3(start))
            turns = min(4, round(length / TWIST_PITCH))
            for e, (side, color) in enumerate(zip((1, -1), colors)):
                body = "%s-%s" % (n, "ab"[e])
                pr = "pr-%s-%d-%d-%s" % (n, i + 1, j + 1, "ab"[e])
                s += [("sketch.create", {"plane": plane(at, normal, b0), "name": pr}),
                      ("sketch.circle.center", {"center": [side * off * cn, side * off * cb], "diameter": STRAND,
                                                "connect": False}),
                      ("sketch.finish", {}),
                      ("solid.sweep", dict({"sketch": pr, "path_sketch": sk, "path": [names[j]], "twist": "%d deg" % (360 * turns)},
                                           **({"operation": "join", "targets": [body]} if made else
                                              {"operation": "new", "body_name": body}))),
                      ("browser.visibility", {"visible": False, "items": [pr]})]
            made = True
            lie = add([c * cn for c in normal], [c * cb for c in b1])
    return s + paint([n + "-a"], colors[0]) + paint([n + "-b"], colors[1])


def edge_trim():
    """U channel on the edge of the notch in the shelf's rear wall: a band round the notch through the
    wall and both its faces, with the wall's own thickness cut out of it."""
    xr, yb = SHELF_X[0], TRAY_Y - GAP
    c = 0.05   # clear of the sheet, so that the clash check has no touching faces to give up on
    ye, z0, z1, r = LEAD_NOTCH
    n = "trim-lead"
    ring = lambda d, out: ("sketch.rectangle.rounded", {
        "p0": [round(ye - d, 3), round(z0 - d, 3)], "p1": [round(yb + out, 3), round(z1 + d, 3)],
        "radius": str(round(r + d, 3)), "connect": False})
    at = lambda x: plane([round(x, 3), 0, 0], [0, 1, 0], [0, 0, 1])
    s = [("sketch.create", {"plane": at(xr - TRIM), "name": "sk-" + n}),
         ring(TRIM_LEG, 20), ring(-TRIM, 14), ("sketch.finish", {}),
         ("solid.extrude", {"sketch": "sk-" + n, "distance": str(T + 2 * TRIM), "operation": "new", "body_name": n}),
         ("sketch.create", {"plane": at(xr - c), "name": "sk-" + n + "-groove"}),
         ring(TRIM_LEG + 1, 24), ring(-c, 17), ("sketch.finish", {}),
         ("solid.extrude", {"sketch": "sk-" + n + "-groove", "distance": str(T + 2 * c), "operation": "cut",
                            "targets": [n]}),
         ("solid.box", {"length": T + 2 * TRIM + 2, "width": 30, "height": z1 - z0 + 2 * TRIM_LEG + 4,
                        "corner": [round(xr - TRIM - 1, 3), round(yb, 3), round(z0 - TRIM_LEG - 2, 3)],
                        "operation": "cut", "targets": [n]})]
    return s + paint([n], BLACK)


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
    ix, iy = PSU_X + PSU_INLET[0], PSU_Y + PSU_INLET[1]
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
    """6-32 hex washer head screw with its head on the point `at`, which faces along n: a 1/4 in hexagon
    with a Phillips recess in it."""
    k = [abs(c) for c in n].index(1)
    s = hexagon(name, along(at, n, 0.8), n, 6.35, 2.0) + cyl(name, at, n, 8.0, 0.8) + cyl(name, at, neg(n), 3.5, length)
    lo, hi = sorted((at[k] + n[k] * 1.6, at[k] + n[k] * 3.3))   # 1.2 into the head, from above it
    for j in ((k + 1) % 3, (k + 2) % 3):
        size, corner = [1.0, 1.0, 1.0], [at[i] - 0.5 for i in range(3)]
        size[j], corner[j] = 4.4, at[j] - 2.2
        size[k], corner[k] = hi - lo, lo
        s.append(("solid.box", {"length": size[0], "width": size[1], "height": size[2],
                                "corner": [round(c, 3) for c in corner], "operation": "cut", "targets": [name]}))
    return s + paint([name], BLACK)


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
            # the front fan's two front screws go through the tabs of the front's return as well
            z = LZ + T if f == "top" else HOOD_Z0 if x > SHELL_XF - HOOD_TAB else -T
            s += fan_screw("screw-fan-%s-%d" % (f, i + 1), [x, y, z], out)
    for i, (x, y) in enumerate(SHELF_SCREWS + SHELF_FRONT_SCREWS):
        s += pc_screw("screw-shelf-%d" % (i + 1), [x, y, LZ + T], up)
        s += cyl("nut-shelf-%d" % (i + 1), [x, y, LZ - 0.1 - T], down, 7.11, 1.78, "new")
        s += paint(["nut-shelf-%d" % (i + 1)], ZINC)
    for i, (a, b) in enumerate(PSU_HOLES + PSU_HOLES_SPARE):
        s += pc_screw("screw-psu-%d" % (i + 1), [PSU_X + a, PSU_Y + b, PSU_TOP + T], up)
    for i, (u, v) in enumerate(BOARD_HOLES):
        x, z = BOARD_X + u, BOARD_Z + BOARD - v
        s += hexagon("standoff-%d" % (i + 1), [x, TRAY_Y, z], left, 6.35, STANDOFF)
        s += paint(["standoff-%d" % (i + 1)], ZINC)
        s += pc_screw("screw-board-%d" % (i + 1), [x, BOARD_Y, z], left)
    for i, d in enumerate((-20, 20)):
        n = "screw-inlet-%d" % (i + 1)   # countersunk M3, flush in the inlet's flange
        s += cyl(n, [-T - INLET_FLANGE[2] - 0.1, INLET[0] + d, INLET[1]], fore, 5.6, 0.4, "new")
        s += cyl(n, [-T - INLET_FLANGE[2] + 0.3, INLET[0] + d, INLET[1]], fore, 3.0, 8.0) + paint([n], BLACK)
        s += hexagon("nut-inlet-%d" % (i + 1), [0, INLET[0] + d, INLET[1]], fore, 5.5, 2.4)
        s += paint(["nut-inlet-%d" % (i + 1)], ZINC)
    # side panels: four screws through each into nuts in the rear panel's lips and the front panel's flanges
    right = [0, 1, 0]
    for side_, out, y_panel, y_lip in (("open", left, SHELL_Y0, 0), ("tray", right, SHELL_Y1, LY)):
        for i, (x, z) in enumerate(SIDE_SCREWS):
            n = "%s-%d" % (side_, i + 1)
            s += pc_screw("screw-side-" + n, [x, y_panel, z], out)
            s += cyl("nut-side-" + n, [x, y_lip, z], neg(out), *NUT_BODY, "new")
            s += paint(["nut-side-" + n], ZINC)
    # handles: a pipe along the rod's centre line, and a screw up into each leg
    c, d, ht, r = HANDLE
    top = ht - d / 2
    for i, x in enumerate(HANDLE_X):
        n = "ref-handle-%d" % (i + 1)
        s += [("sketch.create", {"plane": plane([x, HANDLE_Y[0], LZ + T], [0, 1, 0], [0, 0, 1]), "name": "sk-" + n}),
              ("sketch.line", {"points": [[0, 0], [0, top - r]], "connect": False, "infer": False}),
              ("sketch.arc.center_point", {"center": [r, top - r], "start": [0, top - r], "sweep": -90, "connect": False}),
              ("sketch.line", {"points": [[r, top], [c - r, top]], "connect": False, "infer": False}),
              ("sketch.arc.center_point", {"center": [c - r, top - r], "start": [c - r, top], "sweep": -90,
                                           "connect": False}),
              ("sketch.line", {"points": [[c, top - r], [c, 0]], "connect": False, "infer": False}),
              ("sketch.finish", {}),
              ("solid.pipe", {"path_sketch": "sk-" + n, "path": ["l1", "a1", "l2", "a2", "l3"], "diameter": d,
                              "body_name": n}),
              ("browser.visibility", {"visible": False, "items": ["sk-" + n]})] + paint([n], BLACK)
        for j, y in enumerate(HANDLE_Y):
            # the rear pair go up through the core's top lip as well
            s += pc_screw("screw-handle-%d" % (2 * i + j + 1), [x, y, LZ - (T if x < TOP_LIP else 0)], down)
    # rivets: flush in the lip, a bucked head behind the plate
    joins = [("join-tray-%d" % (i + 1), [x, LY + T, z], left) for i, (x, z) in enumerate(TRAY_JOINS)]
    for n, at, d in joins:
        s += cyl(n, at, d, RIVET, 2 * T, "new") + cyl(n, along(at, d, 2 * T), d, RIVET_TAIL[0], RIVET_TAIL[1])
        s += paint([n], ZINC)
    # switch: plain 12 mm body through the front panel, its head outside and its nut behind
    y, z = SWITCH
    s += cyl("switch", [MOUNT_X[1] - 22, y, z], fore, 11.9, 22, "new")
    s += cyl("switch", [MOUNT_X[1], y, z], fore, *SWITCH_HEAD)
    s += hexagon("switch-nut", [MOUNT_X[0], y, z], back, 13.5, 3.0)
    s += [("solid.cylinder", {"diameter": 12.0, "height": 3.0, "base": [MOUNT_X[0], y, z], "axis": back,
                              "operation": "cut", "targets": ["switch-nut"]})]
    s += paint(["switch", "switch-nut"], BLACK)
    # lamps: holder through the front panel with its bezel outside and a nut behind, and the LED's dome in it
    d0, d1, bh = LED_BEZEL
    for i, (y, z) in enumerate(LEDS):
        n, at = "led-%d" % (i + 1), [MOUNT_X[1], y, z]
        s += cyl(n, at, back, LED_HOLE - 0.2, LED_BEHIND, "new")
        s += [("solid.cone", {"diameter": d0, "top_diameter": d1, "height": bh, "base": at, "axis": fore,
                              "operation": "join", "targets": [n]})]
        s += [("solid.cylinder", {"diameter": 5.2, "height": bh + 1, "base": along(at, fore, 0.2), "axis": fore,
                                  "operation": "cut", "targets": [n]})]
        s += hexagon("led-nut-%d" % (i + 1), [MOUNT_X[0], y, z], back, LED_NUT, 2.5)
        s += [("solid.cylinder", {"diameter": LED_HOLE, "height": 2.5, "base": [MOUNT_X[0], y, z], "axis": back,
                                  "operation": "cut", "targets": ["led-nut-%d" % (i + 1)]})]
        s += cyl("lamp-%d" % (i + 1), along(at, fore, 1.0), fore, 5.0, bh - 2.5, "new")
        s += [("solid.sphere", {"diameter": 5.0, "center": along(at, fore, bh - 1.5), "operation": "join",
                                "targets": ["lamp-%d" % (i + 1)]})]
        s += paint([n, "led-nut-%d" % (i + 1)], BLACK) + paint(["lamp-%d" % (i + 1)], LED_COLORS[i])
    for i, (x, y) in enumerate(FEET):
        n = "foot-%d" % (i + 1)
        s += cyl("stud-foot-%d" % (i + 1), [x, y, 0], down, 3.5, T + FOOT_STUD, "new")
        s += paint(["stud-foot-%d" % (i + 1)], ZINC)
        s += [("solid.cylinder", {"diameter": 20, "height": 2, "base": [x, y, -T - 2], "body_name": n,
                                  "operation": "new"}),
              ("solid.cone", {"diameter": 17, "top_diameter": 12, "height": -16, "base": [x, y, -T - 2],
                              "operation": "join", "targets": [n]}),
              ("solid.cylinder", {"diameter": FOOT_TAP, "height": 19, "base": [x, y, -T],
                                  "axis": down, "operation": "cut", "targets": [n]}),
              ("solid.cylinder", {"diameter": FOOT_RECESS, "height": FOOT_RECESS_DEPTH, "base": [x, y, -T - 18],
                                  "axis": up, "operation": "cut", "targets": [n]})]
        w, l = FOOT_CROSS
        for a, b in ((l, w), (w, l)):   # from 1 below the foot, so no face of the cut lies on one of the foot's
            s.append(("solid.box", {"length": a, "width": b, "height": 1 + FOOT_RECESS_DEPTH + FOOT_CROSS_DEPTH,
                                    "corner": [round(x - a / 2, 3), round(y - b / 2, 3), -T - 19],
                                    "operation": "cut", "targets": [n]}))
        s += paint([n], BLACK)
    return s + wires() + dc_cables()


TAB_FLIP, TAB_POSITION = False, "outside"
SHEET = ["core", "hood", "tray", "shelf", "side"]   # what a shop makes: two of the last
PANELS = SHEET + ["side-tray"]                                            # and the bodies drawn


def main():
    sc = Bridge()
    os.makedirs(EXPORT, exist_ok=True)
    os.makedirs(IMAGES, exist_ok=True)
    sc.call("new_design")
    sc.batch([("sheet.manage_rules", {"name": "CRS 1.2", "thickness": "%g mm" % T, "k_factor": str(K_FACTOR),
                                      "bend_radius": "%g mm" % BEND_R, "corner_relief": "%g mm" % RELIEF,
                                      "corner_relief_shape": "round", "active": True})], "rule")
    for name, steps in (("core", core()), ("tray", tray()), ("hood", hood()),
                        ("shelf", shelf()), ("side", side("side", SHELL_Y0, 1)),
                        ("side-tray", side("side-tray", SHELL_Y1, -1))):
        sc.batch(steps, name)
        print("built", name)
    # a body hidden for a render stays hidden by name through a rebuild
    sc.batch([("appearance.assign", {"bodies": [b for b in PANELS if b not in INSIDE], "color": GREEN}),
              ("appearance.assign", {"bodies": INSIDE, "color": BLACK}),
              ("browser.visibility", {"visible": True, "items": PANELS})], "paint")
    sc.call("save", {"path": DESIGN})
    report(sc)
    if "--sheet" in sys.argv:
        return
    for name, steps in (("bought-in", bought_in()), ("hardware", hardware())):
        sc.batch(steps, name)
        print("built", name)
    sc.call("execute", {"command": "file.export_step", "params": {
        "bodies": ["foot-1"], "path": os.path.join(EXPORT, "foot.step")}})
    show = [("browser.visibility", {"visible": True, "items": PANELS})]   # a body hidden for a render stays hidden
    sc.batch(show, "show")
    sc.call("save", {"path": LOW_DETAIL})
    m = sc.call("measure", {"summary": True})
    clashes(sc, [b["name"] for b in m["bodies"]])


# a fastener shares volume with what it threads into, the mains inlet's body with its own screws, and the
# lead's cable with the moulding at each end and each piece of it with the next
THREADED = [("screw-fan-", "ref-fan-"), ("screw-psu-", "ref-psu-sfx"), ("screw-handle-", "ref-handle-"), ("screw-shelf-", "nut-shelf-"), ("screw-side-", "nut-side-"),
            ("screw-board-", "standoff-"), ("screw-board-", "ref-mainboard"), ("stud-foot-", "foot-"), ("screw-inlet-", "nut-inlet-"),
            ("screw-inlet-", "ref-mains-inlet"), ("ref-mains-lead", "ref-mains-inlet"), ("ref-mains-lead", "ref-mains-plug"),
            ("ref-mains-lead", "ref-mains-lead"),
            # a wire with the part it comes from and with its plug
            ("wire-switch-", "switch"), ("wire-led-1-", "led-1"), ("wire-led-2-", "led-2"), ("wire-", "ref-front-plug"),
            ("wire-atx-", "ref-plug-"), ("wire-cpu-", "ref-plug-"),
            ("switch", "switch-nut"),
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
    lo = [min(b["bbox"]["min"][i] for b in m["bodies"] if b["name"] in PANELS) for i in range(3)]
    hi = [max(b["bbox"]["max"][i] for b in m["bodies"] if b["name"] in PANELS) for i in range(3)]
    size = [hi[i] - lo[i] for i in range(3)]
    for b in m["bodies"]:
        if b["name"] in PANELS:
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


if __name__ == "__main__":
    main()
