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
| Heatsink, no fan | 54.58 deep overall, 5.50 of it the bracket under the board; 123.75 x 123.15 across, six heat pipes (Framework's specification page) | 6 |
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

SFX mounting holes, from Intel's SFX12V Power Supply Design Guide 3.1, figures
17 and 18, read 2026-11-11: three 6-32 holes on the 125 x 63.5 face. Seen from
outside with the fan side up and the origin at the lower left they are at
(6.0, 6.0), (6.0, 57.5) and (119.0, 31.8). The shelf has those three and their mirror
image, six holes, so it takes a unit with all four corners threaded or one
whose pair is at the other end. The guide leaves the mains inlet's place on
that face to the maker and draws it at the single-hole end. The envelope,
125 x 63.5 x 100, is the guide's too, good to +/-1 on the whole numbers.

The case is drawn to that guide, so any SFX supply that follows it should
fit. The two it was laid out around are Corsair's SF450 and Seasonic's Focus
SGX-550 (2021). Both are 125 x 100 x 63.5 with a 92 fan (Corsair gives 63),
from the makers' pages. On both, with the fan toward the board as it stands
here, the mains inlet and switch are at the open side's end of the top
face, away from the board. The inlet's pins run along the supply's 125
width with the earth pin nearest the fan, and the switch is beside it on
the far side from the fan. That is from the makers' pictures and from
Justin; the model's
supply follows that. The mains lead's plug points its cable across the top
of the supply to a grommet hole at the tray's side of the shelf, since a
plug angled at the shelf's rear wall, 25 from the inlet, would land on the
shelf. SFX-L
units, 130 long, have not been checked.

Seasonic's fan is stopped up to about 30 % load, 165 W; Corsair says the
SF450 has a zero-rpm mode without giving its threshold. The cooling study's
supply is a plain SFX box; its noise paragraph was written around the SF750
(2024), whose fan Cybenetics measured stopped up to 300 W. 
## Fasteners and hardware

Every screw on the case is the 6-32 hex washer head screw used for PC cases
and 3.5 in drives, 1/4 in long, apart from the fan screws, the mains inlet's
two and the four M2 screws that hold the shell.

| Where | Screw | Into | Hole in the sheet |
| --- | --- | --- | --- |
| Fans, twelve | ordinary self-tapping fan screw, about 5 x 10 | the fan's own frame | 5.0 clearance |
| Board, four | 6-32 | PEM BSO-632-12 standoff, 9.53 long, in the tray | 5.41 +0.08, 6.9 or more from an edge |
| Supply, three | 6-32 | the supply's own threads | 4.0 clearance in the shelf, six holes |
| Shelf to top panel, two | 6-32 | PEM S-632-1 nut in each shelf tab | 4.76 +0.08, 5.6 or more from an edge; 4.5 clearance in the top panel |
| Shelf to bulkhead, three | 6-32 x 1/4 with a head no taller than 1.2: NBK SETS-#6-32, head 7.5 across and 0.86 tall, Torx T6 | PEM S-632-1 nut in the shelf's front flange | 4.76 +0.08, 7 from the flange's edge; 4.5 clearance in the bulkhead |
| Feet, four | none: the foot is tapped 6-32 and turns on | PEM FH-632-6 flush-head stud, 9.53 long, in the bottom panel, pointing down | 3.5 +0.08, 6.4 or more from an edge |
| Mains inlet, two | countersunk M3, flush in the inlet's flange | a plain M3 nut | 3.5 clearance |
| Shell, four | M2 socket head cap | a thread tapped in the top and bottom panels | 1.6 tap drill; 2.8 clearance in the shell's flange for the one that holds it |

The PEM figures are from PennEngineering's FH, CL and SO bulletins, read
2026-11-11; all three take sheet from 1.02 up. The standoffs are 9.53 where
6.35 is usual, to clear the M.2 holder. A 6-32 hex washer head is 2.0 to 2.4
tall and 7.7 to 8.3 across its washer (ASME B18.6.3, from a reproduction of its
table); it is drawn 2.8 and 8.0. The fan screw's head is drawn 8.5 across, not
measured from a screw.

The shelf has to come out with the supply on it, so nothing that holds it is
permanent. Its front flange is held by three screws through the bulkhead from
the front, where a driver reaches them with the shell off. An ordinary 6-32
head is 2.0 to 2.4 tall and there is 1.5 between the bulkhead and the shell,
so these three are NBK's SETS-#6-32, a stock low-head screw: head 7.5 across
and 0.86 tall (0.295 and 0.034 in, from NBK's table, read 2026-11-12). Flush
studs in the bulkhead with nuts behind the flange were tried first, and the
nuts could not be reached with a tool. The shelf's two tabs for the top
panel's screws fold toward the rear, away from the supply: folded forward
they stood over the supply's rear corner screws, which then could not be
reached with the shelf out of the case.

Cable ties: the tray has four pairs of slots, 2.0 x 5.0 and 8 apart, up the
13 between the board's front edge and the supply. A tie goes in one slot,
behind the tray and out of the other. There is 1.7 between the tray and the
shell for its strap, which suits ties 2.5 or 3.6 wide (1.0 to 1.3 thick).
A lanced bridge would hold a tie without going behind the tray, but it is
a formed feature that laser-and-brake shops do not make.

Three of the M2 screws are nubs for the shell's slots to run onto, their
heads (3.8 across, 2 tall) standing proud of the panel. The fourth goes up
through the shell's flange and is tightened. Pressed-in pilot pins were ruled
out for the nubs: PEM's TPS-3mm comes only 8 long and wants 6.4 from hole
centre to edge, and not every shop stocks pins. The slots are 0.5 clear of the
nubs each side, since both parts are bent and a bend is good to about 0.4.

The tray is fixed to the core's side lips at nine places and the bulkhead to
its front lips at four with PEM's SF-3-1.2 SpotFast, a pressed-in fastener
that joins two sheets and ends flush on both faces: a 3.0 +0.08 hole in the
lip, 2.5 in the plate behind it, 2.54 or more from an edge, for two sheets
of 1.2 (PEM's bulletin SF, read 2026-11-12). Flush matters on both sides:
the shell passes 0.5 from the side lips and 0.3 from the front ones, and the
fans' frames stand 2.8 inside the tray, less than a blind rivet's tail. The
lips are 17 tall (18.5 and 28 at the front) and each fastener is 9.5 from
the panel its lip is
folded from, which also leaves room for spot welds at the same places if a
shop would rather weld.

| Part | Fit | Notes |
| --- | --- | --- |
| 120 fan | four holes on 105 x 105 | 120 x 120 x 15 slim, as the NF-A12x15 |
| Power button | 12.0 hole in the bulkhead, nut behind it; 14.5 hole in the shell for its 14 head | 12 mm vandal switch. Sizes from Justin, who has the part: the body is a plain 12 cylinder inside the case, and the nut needs a 16 circle to turn. Its head is 14 across |
| IEC C14 inlet, screw mount | 28 x 20 cut-out +0.2/0, corners R1 (R3 at most), two 3.5 holes 40 apart | Schurter 6100-3 (6100.3200 with 4.8 tabs), mounted from outside: flange 48 x 23, countersunk for M3, 23.5 behind the panel. From its datasheet, read 2026-11-11. The same cut-out takes Bulgin's PX0580 and Schurter's 6061. The lead to the supply is made up: see before-ordering.md |
| Feet | a 6-32 stud standing 9.5 out of the bottom panel | Our own part, one model made four times, [foot.step](../mechanical/export/foot.step) and the last sheet of the drawings: a 20 flange 2 thick over a cone from 17 to 12, 18 tall, printed in 316L stainless steel and tapped 6-32, with a 9.0 x 1.5 recess underneath for a 3M Bumpon SJ5076 pad (8.0 x 2.8) and, in the recess's floor, a socket for a 3 mm hex key to tighten it by; the pad goes on over the socket and keeps five sixths of its face. A screw from inside is no good, since each foot is under the corner of a fan's frame, so the thread is a flush stud in the panel |

## Still to collect

- Any case fans, once the layout says whether it needs them.
