# Before ordering a Mk I

What has been checked, what is still open, and what goes to a shop. Updated
2026-11-19.

## What a shop gets

Everything is in [mechanical/export/](../mechanical/export/):

- `reactor-mk-i-drawings.pdf`: general arrangement, the riveted assembly with
  its fourteen rivets, and a sheet for each part with its flat pattern,
  bends, holes and notes.
- For each of the five parts a STEP model, a DXF flat pattern and a bend table.
- `foot.step` and `foot-drawing.pdf`, for whoever prints the feet: one model,
  four off. The drawing is also the last sheet of the set.

The shop is Fabworks. It cuts and bends five parts in its 0.048 in (1.2 mm)
1008 steel and presses in twelve PEM studs, standoffs and nuts, all on its
hardware list: four BSO-632-12ZI, four FH-632-6ZI and four S-632-1ZI. The
five parts come loose. Riveting the tray and bulkhead to the core is done at
home. Nothing is tapped or countersunk by the shop.

## Checked

- Clashes: the whole assembly, 149 bodies with every screw, nut, stud, handle and fan
  in place and the mains lead on its route, has no two parts sharing volume apart from threads in what they
  screw into. Framework's own board model sits on the four standoffs to
  0.00 mm, 0.5 inside the rear panel, 3.0 under the top fan, 7.0 over the
  bottom fans and 13.1 from the supply.
- Mini-ITX and ATX: the four holes, the 158.75 x 44.45 rear aperture and its
  position from the board, the 12.27 from the rear holes to the panel and
  the 0.94 to 1.32 panel thickness, against ATX 2.2 figures 3 and 4.
- SFX: the envelope and the three mounting holes against Intel's SFX12V
  guide. The shelf carries the pattern both ways round.
- Mains inlet: the cut-out is Schurter's for the 6100-3, read from its
  datasheet.
- Power supply: the shelf has the three 6-32 holes of Intel's SFX12V guide
  and their mirror image, so any unit that threads the guide's holes mounts.
- Fasteners: every pressed-in part's hole size, sheet thickness and edge
  distance against PEM's bulletins. The closest is the shelf's two nuts, at
  PEM's minimum of 5.6 from the tab's edge.
- Clear of the shell: the shelf's three tongues stand 0.9 in front of the
  bulkhead, in the 1.5 between it and the shell. Nothing else stands proud
  of the bulkhead or the lips.
- Sheet metal rules, against Fabworks' figures for 0.048 in steel: the parts
  are drawn with its inside radius of 1.0 and K of 0.516, flanges are 9.5 or
  more (6.8 needed, 8.4 advised), and its hardware holes are the ones cut:
  4.8 for the nuts, 3.5 for the studs, 5.4 for the standoffs. Mesh webs are
  2.07. [mechanical/dfm.py](../mechanical/dfm.py) measures every cut-out
  in the five flat patterns against its published figures, read 2026-11-17:
  the smallest is 2.0 across (0.51 needed), the thinnest web 2.07 (1.22
  needed), and none is within 5.11 of a bend line, the zone a bend can
  distort. Getting there moved the shell's screws to 7.6 from the rear,
  made the open side's rear lip 15, and moved the shelf's rear wall to 2.1
  behind the supply.
- Flanges: dfm.py also measures every flange all along its bend, which
  catches a lip that steps back. The shortest is the top panel's front lip
  where it is cut back over the lamps, 7.0 (6.81 needed, 8.4 advised); the
  lip's step over the power button was 5.7 until the button and the lamps
  were set 18.5 below the top panel, and is now 12.4. The mitred last 7 of
  each lip are not counted. The shelf's rear wall has 9.0 under its notch
  and 8.9 over it.
- Lamps and button: each is under a leg of the front handle. The upper
  lamp's holder is 2.9 under a handle screw and the lower one 1.5 over the
  head of a supply screw; the button's body is 6 over the supply's screws.
- Handles: RAF 8120-632-A-24, 4 in between centres, against Fascomp's
  drawing of the same part. Each leg has 2.2 of metal to the nearest mesh
  cell and is 3.4 inside the shell's flange; the screw heads under the top
  panel are 5.5 from the rear panel, 11.3 from the top fan and clear of
  the switch and of every part of the board.
- Rivets: each is 7 or more from its lip's edge and from the bend, with a
  bar's width of flat behind it inside. Flush outside and 1.5 at most
  inside, which the 0.3 to 0.5 outside the lips and the 2.8 between the tray
  and the fans both need.
- The 13.1 between the board and the supply stays. It comes from spacing
  the bottom fans so one mesh pattern suits both, and the 8.3 it leaves
  between those fans is where their cables come up.
- The shelf's tongues have 0.5 each side and 0.5 above and below in their
  slots, and 1.8 of each is in or through the bulkhead, which the 0.25 of
  play at the top screws cannot undo.
- Mains lead: Toptekits' "C14 w/screw hole to Right C13", 2 ft / 0.6 m,
  18 AWG, measured from the part by Justin on 2026-11-17. The C14 is
  27.2 x 19.2 with two 3.5 countersunk holes 40.0 apart, as its seller
  draws it, in a flange 48.9 wide and 3.0 thick, and it is rigid for 50
  behind the flange; nothing is within 6 of it there but the bottom fan,
  3.4 below. It mounts from outside: the C13 plug is small enough to go in
  through the 28 x 20 cut-out. On the supply the plug stands 17 where
  there is 34, and its cable leaves toward the tray's side. The cable is
  7 across, for a 12 notch, and 521 long between its mouldings (20.5 in,
  measured again 2026-11-19).
  - The route: across the top of the supply to the notch in the side of the
    shelf's rear wall, down the gap between the board and the supply past
    the tie slots, across the bottom toward the open side and, after one turn,
    back to the inlet. Drawn in the assembly it is 475, so there is about 45
    to spare, and the lead runs down the tray past all four pairs of tie
    slots.
  - The notch is in the tray-side edge of the shelf's rear wall, 13.0 deep
    and 17.0 tall, open toward the tray, which shuts it when the shelf is
    in. The lead and the switch and lamp wires share it, and rubber U
    channel on its edge leaves 12 by 15 of opening: 8 for the lead at the
    tray's end and 4 beside it for the three wires, one above another. There is 9.0 of wall
    under it and 8.9 over it, to the outside of the tab above.
  - Through the notch is the tight part. The cable has to drop into a gap
    13 wide just behind the wall, so it goes through on an arch of 18
    radius, 0.3 from the channel above and below. Its other bends are 20
    to 25.
  - The switch's and the two lamps' wires are drawn as twisted pairs, 1.2
    a conductor, from each part through the notch to a plug on the
    board's 9-pin power header, which is at the top front corner of
    Framework's board, 25 behind the shelf's wall. Along their middles
    they are 214 for the switch, 125 for the upper lamp and 113 for the
    lower one, with nothing to spare; the plug is drawn as a block and
    which pin each goes to is not known.
  - The 24-pin and CPU cables are drawn wire by wire for a Corsair SF750,
    2.3 a wire, from plugs under the supply to the board's two
    connectors, which are low on the board under the heatsink. The
    supply's sockets are scaled from Corsair's pictures of its panel, not
    measured: with the fan toward the board they are toward the open side
    and the front. The wires drop from the supply, run rearward 28 above
    the bottom fans as a band twelve wide and two deep with the CPU's
    four under its edge, and turn into the board's plugs. Between the
    plugs they are 181 to 265 for the 24-pin and 177 to 210 for the CPU,
    with nothing to spare. Which supply pin feeds which board pin is not
    Corsair's pinout, the plugs are blocks 13 and 10 long, and the band
    lies flat over both bottom fans, in the air the CPU cooler draws.
  - The plug's reach toward the tray (drawn 20 from the middle of the
    inlet) and the height its cable leaves at are guesses.
  - It crosses the supply's exhaust grille on its way to the notch, and it
    has no safety listing.
  - The flange is only as tall as the body, so the cut-out shows 0.4 above
    and below it.
- Fits that depend on two bent parts are loose: the shell is 0.5 clear of
  the lips all round, and the clearance holes for
  the shelf's screws 4.5.

## Open: before the order

- Upload the five STEP models to Fabworks and read what its checker says
  about bending the core and the shell. Both are deep U shapes with return
  lips, and whether a press brake reaches every bend has not been checked by
  anyone who has one.
- Fabworks presses hardware in after bending and needs a press on both
  sides of each hole. The two nuts in the rear panel's side lips are 7.6
  from the rear panel, inside the corner, and the four studs are in the
  floor of the core. Ask whether its tooling reaches them.
- The handles: two RAF 8120-632-A-24 (Fascomp FC8120-632-A-24), black
  anodised. AFT Fasteners lists them in tens. The plain stainless
  8120-632-SS is the same size if the black one is out of stock.
- Rubber U channel for the notch in the shelf's rear wall, about 35 of it
  for 1.2 sheet. The one drawn is a placeholder.
- The shell's outside faces want to arrive unmarked, and Fabworks says die
  marks show on every bend. Ask.
- The feet are printed in 316L stainless steel and tapped 6-32 by a 3D
  printing service. Craftcloud will do both. The hole goes right through,
  so an ordinary tap does it, at home if need be.

## To do at home

Tools: a 100 degree countersink, a flat punch and a hammer, a steel bar to
hold against the rivets' tails, and fourteen MS20426AD3-4 rivets with a
few spare. McMaster-Carr sells them as 96685A146, Aircraft Spruce and Van's
Aircraft by weight.

1. Countersink the fourteen 2.5 holes in the core's lips from outside, to
   4.6 across, until a rivet's head sits flush.
2. Rivet the tray to the side lips, ten rivets, then the bulkhead to the
   front lips, four: head outside, the bar against the tail inside, until
   the tail is 3 to 4 across and about 1 tall.
3. Paint, if wanted, with the threads, studs and standoff bores masked.

## Known limits of what has been checked

- Nothing has been built. Bend accuracy, how flat the rivets pull the joints and the shell's
  slide fit are only known once a first one exists; expect to adjust.
- The airflow and heat study uses a simplified case and assumed fan curves;
  see [thermal.md](thermal.md).
- The clash check does not include the board's own 90 bodies pair by pair;
  the board is checked from its extents and its holes.

## Putting one together

1. Handles onto the top panel first, a screw up into each leg from inside,
   while the core is empty: the board and the shelf stand under them later.
   Feet onto their studs with the PH2 screwdriver, then a bumper into each
   foot's recess, over the cross slot. Supply onto the shelf with its 6-32
   screws, three or six as the unit has threads, exhaust face up.
2. Fans into the core, board onto its standoffs, heatsink fan, mains inlet.
   Cables tied to the tray's slots between the board and the supply.
3. Shelf in through the open side, low, then up against the top panel and
   forward until its three tongues are in the bulkhead's slots. Two screws
   down through the top panel.
4. Switch and lamps through the bulkhead, wiring, then the shell on from the front and
   its two screws, one in each side, at the rear and halfway up.
