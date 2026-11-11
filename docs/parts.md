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
| Tallest part on top | 31.1 above the board; the drawing lists the stacked RJ45 and USB as 31 high | STEP, 1 |
| Lowest part underneath | 8.4 below the board, the spring plate of the underside M.2 holder | STEP |

The M.2 holder is deeper than a standard 6.35 standoff, so the board tray
needs a relief or taller standoffs there. The STEP draws the board 2.0 thick
where the drawing says 1.60; the drawing is taken as right.

The heatsink's own footprint and the direction its fins run are not
dimensioned anywhere published, so they have to be measured from the part.
The 5.50 on sheet 6 is read as the board plus the bracket under it, which
puts the heatsink top 48.88 above the board; that reading needs checking
against the part too.

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

| Part | Hole | Notes |
| --- | --- | --- |
| PEM BSO-M3-10 standoff | 4.22 +0.08 | sheet 1.0 or more, hole centre 6.0 or more from an edge |
| PEM S-M4-1 nut | 5.41 +0.08 | sheet 0.97 or more, hole centre 6.9 or more from an edge |
| 120 fan | four on 105 x 105 | 120 x 120 x 15 slim, as the NF-A12x15 |
| PEM FH-M3 and FH-M4 flush studs | 3.0 and 4.0 | for the PSU bracket and the feet; sizes not yet checked against PEM |
| IEC C14 inlet, screw mount | 20 x 28 cut-out, screws 40 apart | placeholder, not from a datasheet |

From PEM's product pages. Feet, rivets and the thumbscrew are placeholders.

## Still to collect

- Heatsink footprint, height and fin direction, measured from the part.
- Power supply envelopes and mounting holes from the form factor guides.
- Power button.
- Any case fans, once the layout says whether it needs them.
