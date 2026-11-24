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
of the supply to a notch in the tray-side edge of the shelf's rear wall, since a
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
two. It has a Phillips recess in its hexagon, so one PH2 driver turns
every one of them, the feet too.

| Where | Screw | Into | Hole in the sheet |
| --- | --- | --- | --- |
| Fans, twelve | ordinary self-tapping fan screw, about 5 x 10 | the fan's own frame | 5.0 clearance |
| Board, four | 6-32 | PEM BSO-632-12 standoff, 9.53 long, in the tray | 5.41 +0.08, 6.9 or more from an edge |
| Supply, three or six | 6-32 | the supply's own threads: three by Intel's guide, six on a unit threaded for both ways round | 4.0 clearance in the shelf, six holes, 5.7 or more from the rear wall's bend line |
| Shelf to top panel, two | 6-32 | PEM S-632-1 nut in each shelf tab | 4.76 +0.08, 5.6 or more from an edge; 4.5 clearance in the top panel |
| Feet, four | none: the foot is tapped 6-32 and turns on | PEM FH-632-6 flush-head stud, 9.53 long, in the bottom panel, pointing down | 3.5 +0.08, 6.4 or more from an edge |
| Mains inlet, two | countersunk M3, flush in the inlet's flange | a plain M3 nut | 3.5 clearance |
| Side panels, four each | 6-32 | PEM S-632-1 nuts, two in each side lip of the rear panel and two in each flange of the front panel | 4.76 +0.08, 9.2 from the outside face of the rear or front panel and 17 from the top and bottom panels: 5.8 from the bend line and 5.8 from the edge of a 15 lip; 4.5 clearance in the side panel; the tray is notched 8.2 wide round the four nuts on its side |
| Handles, four | 6-32, up from under the lip the top panel lies on, the rear panel's or the bulkhead's, which they clamp the top panel to | the handle's own thread, 3/8 in deep | 4.5 clearance in the top panel and in the lip |

The PEM figures are from PennEngineering's FH, CL and SO bulletins, read
2026-11-11; all three take sheet from 1.02 up. The standoffs are 9.53 where
6.35 is usual, to clear the M.2 holder. A 6-32 hex washer head is 2.0 to 2.4
tall and 7.7 to 8.3 across its washer (ASME B18.6.3, from a reproduction of its
table); it is drawn 2.8 and 8.0. The fan screw's head is drawn 8.5 across, not
measured from a screw.

The shelf has to come out with the supply on it, so nothing that holds it is
permanent, and its front has no screws. An ordinary 6-32 head is 2.0 to 2.4
tall and there is 1.5 between the bulkhead and the front panel, so no ordinary
screw goes in from the front, and one from behind cannot be reached with a
driver. Instead three tongues on the shelf's front edge, 12 wide, go through
three slots in the bulkhead, 13.0 x 2.2, and stand 0.9 in front of it, 0.6
short of the front panel. The bulkhead carries the supply's weight there, and the
two screws through the top panel hold the shelf up at the rear and keep it
from sliding the 2.4 back out of the slots. Flush studs with nuts behind,
and then low-headed screws from the front, were both tried first: the nuts
could not be reached, and the screws were a special part with its own
driver. The shelf's two tabs for the top
panel's screws fold toward the rear, away from the supply: folded forward
they stood over the supply's rear corner screws, which then could not be
reached with the shelf out of the case.

Cable ties: the tray has four pairs of slots, 2.0 x 5.0 and 8 apart, up the
13 between the board's front edge and the supply. A tie goes in one slot,
behind the tray and out of the other. There is 1.7 between the tray and the
side panel for its strap, which suits ties 2.5 or 3.6 wide (1.0 to 1.3 thick).
A lanced bridge would hold a tie without going behind the tray, but it is
a formed feature that laser-and-brake shops do not make.

Eight ordinary 6-32 case screws hold the side panels, four through each,
9.2 in from its front and rear edges and 17 from the top and bottom panels,
into nuts in the rear panel's side lips and the front panel's flanges. Each
head stands 2.8 proud of the side, and all of them come out with the case
standing where it is; the panel then lifts straight off. The front pair on
each side also hold the front panel. The two side panels are one part: the
holes are the same at both ends, so one turned end for end fits the other
side. The height is the one that clears everything: the supply and shelf
behind the front flanges, the tray's rivets, the board's nearest standoff
(7.2 from the tray's notch, PEM asking 6.9) and the relief at the rear
panel's top corners (the nut is 5.76 from it, PEM asking 5.6). Screws through
a lip folded round the rear panel were looked at and dropped: the lower one
has nowhere to go, with the rear fan 1.3 inside the panel where a nut is 1.78
deep, the mains inlet in one corner and the I/O aperture up the other side.

The front panel has no screws of its own. Its flanges stand in the same
layer as the core's side lips, which stop 15.3 short of the front to make
room. The switch and the two lamps go through its face and through the top
panel's front lip into the bulkhead, and their nuts clamp the three
together, which holds it while the side panels are off. The switch's thread
has to span 3.9 of sheet and the lamps' the same; neither has been checked
on the parts.

The tray is riveted to the core's side lips at seven places and the bulkhead
to its front lip at two, by hand, with 3/32 in flush solid rivets,
MS20426AD3-4 (2117 aluminium, 100 degree head 0.179 in across and 0.036 in
tall, 1/4 in long, in a No. 40 hole; from Olander's and Hanson's tables, read
2026-11-12). The holes are cut 2.5 in both parts. The head sits in a
countersink made by hand in the lip, flush outside, and the tail is bucked
inside to a head 3.0 to 4.1 across and 0.8 to 1.5 tall. Both sides matter:
the side panels pass 0.5 from the side lips and the front panel 0.3 from the front one, and the
fans' frames stand 2.8 inside the tray, less than a blind rivet's tail. The
lips are 17 tall (28 at the front) and each tray rivet is 9.5 from the
panel its lip is folded from. PEM's SpotFast was drawn first, and no
prototyping shop found lists it or joins parts. The rivet is a standard
aircraft part, used by the thousand in kit aircraft: McMaster-Carr sells it
as 96685A146 (250 for about $8), and Aircraft Spruce and Van's Aircraft by
weight, read 2026-11-17. For the 2.4 of sheet here 1/4 in is the right
length, grip plus one and a half diameters.

| Part | Fit | Notes |
| --- | --- | --- |
| 120 fan | four holes on 105 x 105 | 120 x 120 x 15 slim, as the NF-A12x15 |
| Lamps, two | 8.0 hole in the bulkhead for each, nut behind it; 8.6 holes in the front panel and the top panel's front lip, which they clamp to the bulkhead | 5 mm LEDs in black panel holders, both from Justin, who has the parts: 08L53GD, green, for power, above 08H53ED, amber, for drive activity, 12.4 apart. The holder's bezel is 10.8 across where it sits on the front panel, tapering to 8.8, and 4.3 tall; 11 of the holder is behind the bezel, 7.1 of it inside the case. Its nut is 9.4 across flats. Under the tray-side leg of the front handle, their middle level with the power button |
| Power button | 12.0 hole in the bulkhead, nut behind it; 12.6 holes in the front panel, which its 14 head sits on, and in the top panel's front lip | 12 mm vandal switch. Sizes from Justin, who has the part: the body is a plain 12 cylinder inside the case, and the nut needs a 16 circle to turn. Its head is 14 across |
| IEC C14 inlet, screw mount | 28 x 20 cut-out +0.2/0, corners R1 (R3 at most), two 3.5 holes 40 apart | The moulded end of the mains lead, Toptekits' "C14 w/screw hole to Right C13", 0.6 m, mounted from outside with two countersunk M3 screws and nuts. Measured from the part, 2026-11-17: body 27.2 x 19.2, flange 48.9 wide, as tall as the body and 3.0 thick, 3.5 countersunk holes 40.0 apart, rigid for 50 behind the flange; cable 7 across and 20.5 in (521) between the mouldings, measured again 2026-11-19; the C13 plug passes through the cut-out and stands 17 above the supply. The cut-out is Schurter's for the 6100-3 (datasheet, read 2026-11-11), which also takes Bulgin's PX0580 and Schurter's 6061 if a separate inlet is ever wanted |
| Handles, two | two 4.5 holes 101.6 apart, a 6-32 screw up into each leg | RAF 8120-632-A-24, also Fascomp FC8120-632-A-24: 6061 aluminium, black anodised, 1/4 in rod, 4.000 +/-0.031 in between the legs, 1 1/4 in tall, 1/4 in bend radius, each leg tapped 6-32 5/16 to 3/8 in deep. From Fascomp's drawing, read 2026-11-17; it does not say that the 4 in is between centres, which is taken from RAF's drawing of the family. The 4.5 holes allow for the +/-0.8. One across the rear of the top and one across the front, legs 9.5 from each end. 8120-632-SS is the same in plain stainless, and 8130 is 1 1/2 in tall |
| Edge trim | pushed onto the edge of the notch in the shelf's rear wall, 1.2 sheet | Rubber U channel. No part is chosen yet, so the one drawn is a placeholder: 1.0 thick over the edge and on each face, legs 4.0 onto the wall. About 35 |
| Feet | a 6-32 stud standing 9.5 out of the bottom panel | Our own part, one model made four times, [foot.step](../mechanical/export/foot.step) and [its drawing](../mechanical/export/foot-drawing.pdf), also the last sheet of the drawings: a 20 flange 2 thick over a cone from 17 to 12, 18 tall, printed in 316L stainless steel and tapped 6-32 right through, with a 9.0 x 1.5 recess underneath for a 3M Bumpon SJ5076 pad (8.0 x 2.8) and, in the recess's floor around the hole, a cross of two slots 1.6 x 6.0, 2.5 deep, to tighten it with the same PH2 screwdriver as the case's screws; the pad goes on over the cross and keeps three fifths of its face. A screw from inside is no good, since each foot is under the corner of a fan's frame, so the thread is a flush stud in the panel |

## Still to collect

- Any case fans, once the layout says whether it needs them.
