# Before ordering a Mk I

What has been checked, what is still open, and what goes to a shop. Updated
2026-11-12.

## What a shop gets

Everything is in [mechanical/export/](../mechanical/export/):

- `reactor-mk-i-drawings.pdf`: general arrangement, the joined assembly with
  its thirteen fasteners, and a sheet for each part with its flat pattern,
  bends, holes and notes.
- For each of the five parts a STEP model, a DXF flat pattern and a bend table.
- `foot.step` and the drawings' last sheet, for whoever prints the four feet.

The shop cuts and bends five parts in 1.2 mm cold rolled steel, presses in
thirteen PEM studs, standoffs and nuts, taps four M2 holes, joins the tray
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
- Fasteners: every pressed-in part's hole size, sheet thickness and edge
  distance against PEM's bulletins. The closest is the shelf's two nuts, at
  PEM's minimum of 5.6 from the tab's edge.
- Screw heads against the shell: nothing stands proud of the bulkhead or the
  lips. The shelf's fixings at the front are flush studs for that reason.
- Sheet metal rules for 1.2 mm steel, against SendCutSend's, Protolabs' and
  Komaspec's published limits: flanges are 9.5 or more (7.6 needed), mesh webs
  2.07 (0.6 needed, 1.2 to 1.8 preferred), every part fits a 762 x 1118 bed,
  and cut-outs are about 6 or more from a bend line except those listed below.
- Joints: each SpotFast is 7 from its lip's edge and from the bend (2.54
  needed), in 14.6 or more of flat overlap, with room for a 12.7 tool on both
  sides; it ends flush, which the 0.3 to 0.5 outside the lips and the 2.8
  between the tray and the fans both need.
- Fits that depend on two bent parts are loose: the shell is 0.5 clear of
  the lips all round, the nub slots 0.5 a side, and the shelf's stud and
  screw holes 4.5.

## Open: needs the part in hand

- Power supply: Corsair's SF450 or Seasonic's Focus SGX-550 (2021). Both are
  standard 100 long SFX units with the inlet along the long edge. Check on
  the part: which mounting holes it threads, and that the angled plug fits
  under the top panel, which is 34 above it. Their fans start at lower loads
  than the SF750's that the noise estimate was written around; see
  [thermal.md](thermal.md).
- Mains lead. First choice is NCASE's Power Supply Inlet Cable, a 54 cm
  ready-made lead from a screw-mount C14 to a right-angle C13
  (NC-CORD-C13C14-R-V60-DG1-72HR, or -L- for the other hand). NCASE does not
  publish its C14's cut-out or screw spacing, so buy it and measure it
  against the 28 x 20 cut-out and 40 spacing before ordering the metal, and
  pick the hand from the supply's inlet. The fallback is all published parts:
  Schurter's 6100.3200 inlet, International Configurations' 57070-A
  rewireable angled C13 (20 proud of the supply), 18 AWG three-core cord and
  TE 2-520275-2 receptacles for the inlet's 4.8 tabs. Either way the wires
  pass over the rear bottom fan and need tying clear of it.

## Open: to settle with the shop

- SpotFast. Any shop that presses PEM hardware can fit it, but ask: it wants
  the two holes lined up across two parts. A shop that would rather spot weld
  the same thirteen places may, leaving the holes out.
- The feet. They are printed in 316L stainless steel by a 3D printing service, not made by
  the sheet metal shop, and tapped 6-32 after printing: ask whether the
  service taps, or do the four by hand.
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

## Open: decisions

- Whether to keep the 13.1 between the board and the supply. It is there so
  one mesh pattern suits both bottom fans; a seam in the bottom mesh would
  take 5.5 off the length.

## Known limits of what has been checked

- Nothing has been built. Bend accuracy, how flat the joints pull and the shell's
  slide fit are only known once a first one exists; expect to adjust.
- The airflow and heat study uses a simplified case and assumed fan curves;
  see [thermal.md](thermal.md).
- The clash check does not include the board's own 90 bodies pair by pair;
  the board is checked from its extents and its holes.

## Putting one together

1. Feet onto their studs. Supply onto the shelf with three 6-32 screws, exhaust face up.
2. Fans into the core, board onto its standoffs, heatsink fan, mains inlet.
3. Shelf in through the open side, low, then up and forward onto the
   bulkhead's three studs. Nuts on behind its flange, two screws down through
   the top panel.
4. Switch through the bulkhead, wiring, then the shell on from the front and
   its one screw underneath.
