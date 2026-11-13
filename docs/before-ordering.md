# Before ordering a Mk I

What has been checked, what is still open, and what goes to a shop. Updated
2026-11-12.

## What a shop gets

Everything is in [mechanical/export/](../mechanical/export/):

- `reactor-mk-i-drawings.pdf`: general arrangement, the riveted assembly with
  its thirteen rivets, and a sheet for each part with its flat pattern,
  bends, holes and notes.
- For each of the five parts a STEP model, a DXF flat pattern and a bend table.
- `foot.step` and the drawings' last sheet, for whoever prints the feet:
  one model, four off.

The shop is Fabworks. It cuts and bends five parts in its 0.048 in (1.2 mm)
1008 steel and presses in eleven PEM studs, standoffs and nuts, all on its
hardware list: four BSO-632-12ZI, four FH-632-6ZI and three S-632-1ZI. The
five parts come loose. Riveting the tray and bulkhead to the core and
tapping the four M2 holes are done at home.

## Checked

- Clashes: the whole assembly, 82 bodies with every screw, nut, stud and fan
  in place, has no two parts sharing volume apart from threads in what they
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
  2.07. Features within 5.1 of a bend may distort; those are listed below.
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
- Fits that depend on two bent parts are loose: the shell is 0.5 clear of
  the lips all round, the nub slots 0.5 a side, and the clearance holes for
  the shelf's screws 4.5.

## Open: needs the part in hand

- Mains lead: a ready-made one, a straight screw-mount C14 to a side-angle
  C13, 0.6 long. Its plug points the cable across the top of the supply to
  the grommet hole at the tray's side of the shelf, and the lead then runs
  down the gap between the board and the supply, past the tie slots, along
  the bottom and across between the two bottom fans to the inlet: about 450
  of cable, 500 with slack, which is what a 0.6 lead has between its
  connectors. A plug angled straight at the rear wall would land on the
  shelf, 25 from the inlet.
  - The candidate is Toptekits' "C14 w/screw hole to Right C13", 2 ft /
    0.6 m, 18 AWG. Its seller's drawing gives the C14 a 27.2 x 19.2 cut-out
    and screws 40 apart, which the 28 x 20 cut-out and 40 spacing here
    take.
  - Which hand: holding the plug with its holes toward you and the earth
    hole uppermost, the cable must leave to the left. The "Right" one's
    photograph shows that, but sellers' names and pictures are not to be
    relied on: check it on the supply, and the "Left" one is the same price.
  - Still to measure: how far the plug stands above the supply, which has
    34, and the lead's real length.
  - It crosses the supply's exhaust grille on its way to the grommet, and
    it has no safety listing.

## Open: before the order

- Upload the five STEP models to Fabworks and read what its checker says
  about bending the core and the shell. Both are deep U shapes with return
  lips, and whether a press brake reaches every bend has not been checked by
  anyone who has one.
- Close to bends, inside Fabworks' 5.1 distortion zone: the four M2 holes
  (1.9), the shell's slots (about 3), the supply's front holes and the
  shelf's grommet hole (4). All are clearance or tapped by hand afterwards.
  The shell's four slots are the ones to watch: they have 0.5 a side.
- The shell's outside faces want to arrive unmarked, and Fabworks says die
  marks show on every bend. Ask.
- The feet are printed in 316L stainless steel and tapped 6-32 by a 3D
  printing service. Craftcloud will do both.

## To do at home

Tools: a 100 degree countersink, a flat punch and a hammer, a steel bar to
hold against the rivets' tails, an M2 x 0.4 tap, and thirteen MS20426AD3-4
rivets with a few spare.

1. Countersink the thirteen 2.5 holes in the core's lips from outside, to
   4.6 across, until a rivet's head sits flush.
2. Rivet the tray to the side lips, nine rivets, then the bulkhead to the
   front lips, four: head outside, the bar against the tail inside, until
   the tail is 3 to 4 across and about 1 tall.
3. Tap the four 1.6 holes at the rear corners of the top and bottom panels
   M2 and screw in the four pins.
4. Paint, if wanted, with the threads, studs and standoff bores masked.

## Known limits of what has been checked

- Nothing has been built. Bend accuracy, how flat the rivets pull the joints and the shell's
  slide fit are only known once a first one exists; expect to adjust.
- The airflow and heat study uses a simplified case and assumed fan curves;
  see [thermal.md](thermal.md).
- The clash check does not include the board's own 90 bodies pair by pair;
  the board is checked from its extents and its holes.

## Putting one together

1. Feet onto their studs with a 3 mm hex key, then a bumper into each
   foot's recess, over the key's socket. Supply onto the shelf with three 6-32 screws, exhaust face up.
2. Fans into the core, board onto its standoffs, heatsink fan, mains inlet.
   Cables tied to the tray's slots between the board and the supply.
3. Shelf in through the open side, low, then up against the top panel and
   forward until its three tongues are in the bulkhead's slots. Two screws
   down through the top panel.
4. Switch through the bulkhead, wiring, then the shell on from the front and
   its one screw in the open side, at the rear and halfway up.
