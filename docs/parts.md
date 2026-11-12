# Bought-in parts

Dimensions of the parts the case is built around, and where each number came
from. All in millimetres. Anything marked placeholder has not been checked
against a datasheet, standard or the part itself.

## Framework Desktop mainboard

Source: Framework's own drawing and CAD in
[FrameworkComputer/Framework-Desktop](https://github.com/FrameworkComputer/Framework-Desktop)
(CC BY 4.0), `Mainboard/FRAMEWORK_DESKTOP_MAIN_PCB_V0.pdf`, read 2026-11-11.
The same folder has a STEP model, `FRAMEWORK_DESKTOP_MAIN_PCB_V01.stp` (73 MB),
measured in SolidCraft on 2026-11-11. It is the bare board with its connectors,
SSD and WLAN card; the heatsink, fan and duct are not in it. It is kept
outside the repo because of its size.

The drawing's origin is a point 3.00 outside the board's corner, so its
ordinates run from 3.00 to 173.00.

| What | Value | Drawing sheet |
| --- | --- | --- |
| Board outline | 170.00 x 170.00, 1.60 thick | 2 |
| Mounting holes | standard Mini-ITX pattern, 154.94 x 157.48 with the fourth hole 22.86 in from the corner; ø3.96 | 2 |
| Heatsink holes | 78.00 x 87.00 rectangle | 2, 6 |
| Component height limit, underside | 3.0 over most of the board | 3 |
| Heatsink, no fan | 54.58 deep overall, 5.50 of it the bracket under the board | 6 |
| Heatsink with 120 x 25 fan and duct | 75.88 to the top of the fan, 83.2 maximum | 6 |
| Fan screws | M3 x 26.5, four | 6 |
| Fan duct footprint | 126.2 square, from 21.54 and 12.84 on the drawing's axes | 6 |
| Tallest part on top | 31.5 above the board; the drawing lists the stacked RJ45 and USB as 31 high | STEP, 1 |
| Lowest part underneath | 8.4 below the board, the spring plate of the underside M.2 holder | STEP |

The M.2 holder is deeper than a standard 6.35 standoff, so the board tray
needs a relief or taller standoffs there. The board in the STEP is 1.60 thick,
as the drawing says, with pads standing 0.4 above its top face.

The heatsink's own footprint and the direction its fins run are not
dimensioned anywhere published, so they have to be measured from the part.
The 5.50 on sheet 6 is read as the board plus the bracket under it, which
puts the heatsink top 48.88 above the board; that reading needs checking
against the part too.

## Mini-ITX fit

From the ATX specification 2.03, section 3.3.5 and figure 4, which Mini-ITX
shares for its rear panel:

| What | Value |
| --- | --- |
| I/O aperture | 158.75 x 44.45 (6.25 x 1.75 in), +/-0.2; corners up to 0.99 radius |
| Along the board | from 2.44 past the board's edge on the port side to 13.69 short of the slot side |
| Across the board | its lower side 2.24 below the underside of the board (3.81 below the top of a 1.57 board) |
| Keepout round it | 2.5 on both faces of the panel: no features, and no paint if a shield is to ground |
| Rear panel thickness | 0.94 to 1.32, for the shield to clip in |
| Rear holes to the panel | 12.27, so the board's rear edge is 2.11 from the panel |
| Connector faces | 11.30 from the rear holes |

The Framework board's own ports run from 11.5 to 143.9 along that edge and up
to 31.5 above the board (from its STEP), inside the aperture. Its I/O shield is built on and does not come off, and
fits the same aperture as a board with a loose shield (from Justin, who has
the board).

The case uses 9.53 standoffs where 6.35 is usual. The aperture is placed from
the board, not the tray, so this does not affect fit.

## Fans

Noctua NF-A12x15 PWM, from
[Noctua's specification page](https://www.noctua.at/en/products/nf-a12x15-pwm/specifications):
120 x 120 x 15 (16 with the pads), holes on 105 x 105, 450 to 1850 rpm,
94.2 m³/h and 1.53 mm H₂O at full speed, 23.9 dB(A).

## Power supplies

Envelopes as width x height x depth. These agree across several secondary
sources but have not been read from the form factor design guides yet, so
treat them as placeholders.

| Form factor | Envelope | Usual fan |
| --- | --- | --- |
| ATX | 150 x 86 x 140, deeper on larger units | 120 to 140 |
| SFX | 125 x 63.5 x 100 | 80 or 92 |
| SFX-L | 125 x 63.5 x 130 | 120 |

Rear mounting holes, four 6-32, on the 150 x 86 face with the origin at one
corner: (6, 16), (6, 80), (144, 80), (120, 6). The 138, 114, 64, 16 and 6
figures are in Intel's ATX12V design guide; which corner they start from comes
from a secondary source, so the rear panel carries the pattern both ways up.

SFX mounting holes, 6-32, on the 125 x 63.5 face: a 113 x 51.5 rectangle 6 in
from each edge. The spacings are in Intel's SFX12V design guide, which calls
out three holes; the bracket has all four corners.

## Fasteners and hardware

Every screw on the case is the 6-32 hex washer head screw used for PC cases
and 3.5 in drives, 1/4 in long, apart from the fan screws, the mains inlet's
two and the four M2 screws that hold the shell.

| Where | Screw | Into | Hole in the sheet |
| --- | --- | --- | --- |
| Fans, twelve | ordinary self-tapping fan screw, about 5 x 10 | the fan's own frame | 5.0 clearance |
| Board, four | 6-32 | PEM BSO-632-12 standoff, 9.53 long, in the tray | 5.41 +0.08, 6.9 or more from an edge |
| Supply, four | 6-32 | the supply's own threads | 4.0 clearance in the shelf |
| Shelf to top panel, two | 6-32 | PEM S-632-1 nut in each shelf tab | 4.76 +0.08, 5.6 or more from an edge |
| Bulkhead to front lips, four | none: a 6-32 nut on a stud | PEM FH-632-6 flush stud, 9.53 long, in the lips | 3.5 +0.08, 6.4 or more from an edge; 4.0 clearance in the bulkhead |
| Mains inlet, two | countersunk M3, flush in the inlet's flange | a plain M3 nut | 3.4 clearance |
| Shell, four | M2 socket head cap | a thread tapped in the top and bottom panels | 1.6 tap drill; 2.4 clearance in the shell's flange for the one that holds it |

The PEM figures are from PEM's catalogue pages and its CL and FH datasheets,
read 2026-11-11; all three take sheet from 1.02 up. The standoffs are 9.53
where 6.35 is usual, to clear the M.2 holder. The 6-32 screw's head is drawn 8.0
across its washer and the fan screw's 8.5 across, neither measured from a
screw; at 8.5 a fan screw's head passes 0.2 from the shell's flange as the
shell slides.

Three of the M2 screws are nubs for the shell's slots to run onto, their
heads (3.8 across, 2 tall) standing proud of the panel. The fourth goes up
through the shell's flange and is tightened. Pressed-in pilot pins were ruled
out for the nubs: PEM's TPS-3mm comes only 8 long and wants 6.4 from hole
centre to edge, and not every shop stocks pins.

The tray is riveted to the core under the shell, which sits 0.3 off it, so
those nine rivets have to be flush on the outside, or be spot welds. The
shelf is riveted to the bulkhead with three ordinary 3.2 rivets.

| Part | Fit | Notes |
| --- | --- | --- |
| 120 fan | four holes on 105 x 105 | 120 x 120 x 15 slim, as the NF-A12x15 |
| Power button | 12.0 hole in the bulkhead, nut behind it; 13.0 hole in the shell for its head | 12 mm vandal switch. Sizes from Justin, who has the part: the body is a plain 12 cylinder inside the case, and the nut needs a 16 circle to turn |
| IEC C14 inlet, screw mount | 20 x 28 cut-out, screws 40 apart | placeholder, not from a datasheet |
| Feet | 4.0 hole for a pressed-in M4 stud | placeholder |

## Still to collect

- Heatsink footprint, height and fin direction, measured from the part.
- Power supply envelopes and mounting holes from the form factor guides.
- Any case fans, once the layout says whether it needs them.
