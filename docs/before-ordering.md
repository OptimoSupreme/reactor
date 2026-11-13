# Before ordering a Mk I

What has been checked, what is still open, and what goes to a shop. Updated
2026-11-12.

## What a shop gets

Everything is in [mechanical/export/](../mechanical/export/):

- `reactor-mk-i-drawings.pdf`: general arrangement, the joined assembly with
  its thirteen fasteners, and a sheet for each part with its flat pattern,
  bends, holes and notes.
- For each of the five parts a STEP model, a DXF flat pattern and a bend table.
- `foot.step` and the drawings' last sheet, for whoever prints the feet:
  one model, four off.

The shop cuts and bends five parts in 1.2 mm cold rolled steel, presses in
fourteen PEM studs, standoffs and nuts, taps four M2 holes, joins the tray
and bulkhead to the core with thirteen PEM SpotFast fasteners, and paints
them if it offers that. The shelf and shell come loose.

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
- Screw heads against the shell: the shelf's three front screws have heads
  0.86 tall in the 1.5 between the bulkhead and the shell. Nothing else
  stands proud of the bulkhead or the lips.
- Sheet metal rules for 1.2 mm steel, against SendCutSend's, Protolabs' and
  Komaspec's published limits: flanges are 9.5 or more (7.6 needed), mesh webs
  2.07 (0.6 needed, 1.2 to 1.8 preferred), every part fits a 762 x 1118 bed,
  and cut-outs are about 6 or more from a bend line except those listed below.
- Joints: each SpotFast is 7 from its lip's edge and from the bend (2.54
  needed), in 14.6 or more of flat overlap, with room for a 12.7 tool on both
  sides; it ends flush, which the 0.3 to 0.5 outside the lips and the 2.8
  between the tray and the fans both need.
- The 13.1 between the board and the supply stays. It comes from spacing
  the bottom fans so one mesh pattern suits both, and the 8.3 it leaves
  between those fans is where their cables come up.
- Fits that depend on two bent parts are loose: the shell is 0.5 clear of
  the lips all round, the nub slots 0.5 a side, and the clearance holes for
  the shelf's screws 4.5.

## Open: needs the part in hand

- The shelf's three front screws. NBK's SETS-#6-32-1/4, sold in packs of ten
  from NBK America's own shop, with their SKX-6 key or a T6 driver; or any
  6-32 with a head under 1.2 tall. An ordinary case screw does not fit
  there.
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

## Open: to settle with the shop

- SpotFast. Any shop that presses PEM hardware can fit it, but ask: it wants
  the two holes lined up across two parts. A shop that would rather spot weld
  the same thirteen places may, leaving the holes out.
- The feet are printed in 316L stainless steel and tapped 6-32 by a 3D
  printing service, not made by the sheet metal shop. Craftcloud will do
  both.
- M2 threads. A 1.2 sheet holds three threads of M2 x 0.4, and at least one
  shop does not tap below 1.5. The four holes are also 1.9 from a bend, so
  they should be drilled and tapped after bending. Doing these four by hand
  at home is a fair fallback: they only hold the shell.
- Holes close to bends, which may pull slightly out of round: the supply's
  two front holes and the grommet hole in the shelf (4 from a bend), and the
  shell's slots and screw hole (about 3). All are clearance features.
- Bend allowance. The flat patterns are drawn for an inside radius of 1.2 and
  K 0.44. A shop will redo them for its own tooling from the STEP models.
- Paint, if the shop offers it, and then masking: threads, studs, standoff bores, and both
  faces of the rear panel within 2.5 of the I/O aperture.
- The shell's outside faces want to arrive unmarked. Say so on the order.

## Known limits of what has been checked

- Nothing has been built. Bend accuracy, how flat the joints pull and the shell's
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
3. Shelf in through the open side and up against the top panel. Two screws
   down through the top panel, three low-head screws in from the front.
4. Switch through the bulkhead, wiring, then the shell on from the front and
   its one screw in the open side, at the rear and halfway up.
