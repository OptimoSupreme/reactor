# Pressed-in hardware

What OSH Cut presses in, part by part, and into which holes. Twenty pieces:
twelve nuts, four studs and four standoffs, all PennEngineering (PEM), all
6-32, zinc plated steel. The names are those of OSH Cut's hardware catalog.

The STEP models are in the case's own axes: X from the rear panel to the
front, Y from the open side to the tray's side, Z up. The tray is a flat
plate, so only its axes tell its two faces apart.

In every part the hardware holes can be told by their diameter, with one
exception, on the core: see below. No other hole in any part takes hardware.

| Part | File | Hardware | Qty | Hole | Which holes | Which way |
| --- | --- | --- | --- | --- | --- | --- |
| Core | `core.step` | S-632-1ZI nut | 4 | 4.76 | all four 4.76 holes: two in each side lip of the rear panel, 17 from the bottom and from the top | body inside the case, flush on the outside of the lip |
| Core | `core.step` | FH-632-6ZI flush-head stud | 4 | 3.50 | the four 3.50 holes in the bottom panel, among the mesh, one near each corner | head flush in the upper (inside) face, stud pointing down, out of the case |
| Hood | `hood.step` | S-632-1ZI nut | 4 | 4.76 | all four 4.76 holes: two in each side flange of the front | body inside the case, flush on the outside of the flange |
| Tray | `tray.step` | BSO-632-12ZI blind standoff | 4 | 5.41 | all four 5.41 holes | head flush in the outer face, the one that goes against the core's lips (+Y in `tray.step`), standing 9.53 off the other face, toward the board (-Y) |
| Shelf | `shelf.step` | S-632-1ZI nut | 4 | 4.76 | all four 4.76 holes, one in each tab | body under the tab, flush on top |
| Side panel (two off) | `side.step` | none | | | | |

## The exception: 3.50 holes in the core

The core has six 3.50 holes and only four take a stud. The other two are in
the rear panel, one each side of the rectangular mains inlet cut-out, 40
apart: they are clearance holes for the inlet's M3 screws and get nothing.

## Holes that take no hardware

| Diameter | Where | What for |
| --- | --- | --- |
| 2.50 | core, hood, tray | rivets, fitted at home |
| 3.50 | core, the two beside the inlet cut-out | M3 screws |
| 4.00 | shelf | the supply's screws |
| 4.50 | core, hood, side panel | handle, shelf and side panel screws |
| 5.00 | core, hood | fan screws |
| 8.00, 12.00 | hood | lamps and switch |

## Where they are in the flat patterns

Centres in mm from the lower left corner of each DXF's outline, for finding
a hole on screen. The STEP models govern.

| Part | Hardware | Centres |
| --- | --- | --- |
| Core | S-632-1ZI | 31.4, 5.8; 31.4, 150.4; 207.4, 5.8; 207.4, 150.4 |
| Core | FH-632-6ZI | 241.7, 39.1; 241.7, 117.1; 459.0, 39.1; 459.0, 117.1 |
| Core | nothing (M3) | 196.4, 22.1; 196.4, 62.1 |
| Hood | S-632-1ZI | 35.0, 5.8; 35.0, 150.4; 211.0, 5.8; 211.0, 150.4 |
| Tray | BSO-632-12ZI | 26.9, 10.8; 26.9, 165.7; 184.3, 33.6; 184.3, 165.7 |
| Shelf | S-632-1ZI | 5.6, 41.5; 5.6, 83.5; 161.3, 10.0; 161.3, 115.0 |

## Checked

[mechanical/dfm.py](../mechanical/dfm.py) measures each of these holes
against PEM's figures. The nuts are 5.60 to 5.80 from the nearest edge (5.6
needed), the studs 11.3 (6.4) and the standoffs 8.0 (6.9). All three parts
take sheet from 1.02 up; this sheet is 1.2. Whether OSH Cut's press reaches
the eight nuts in the core's lips and the hood's flanges, which are 8.0 from
a panel inside a 15 lip, is for its quote to say.
