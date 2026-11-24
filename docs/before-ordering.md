# Before ordering

What has been checked, what is still open, and what goes to a shop. Updated
2026-11-24.

## What a shop gets

Everything is in [mechanical/export/](../mechanical/export/):

- `reactor-drawings.pdf`: general arrangement, the riveted assembly with
  its eleven rivets, and a sheet for each part with its flat pattern,
  bends, holes and notes.
- For each of the five parts a STEP model, a DXF flat pattern and a bend table.
  The side panel is wanted twice, so six pieces.
- `foot.step` and `foot-drawing.pdf`, for whoever prints the feet: one model,
  four off. The drawing is also the last sheet of the set.

The shop is OSH Cut. It cuts and bends the six pieces in its 0.048 in
(1.2 mm) A1008 cold rolled steel and presses in twenty PEM studs, standoffs
and nuts, all in its hardware catalog: four BSO-632-12ZI, four FH-632-6ZI and
twelve S-632-1ZI. The pieces come loose. Riveting the tray to the core and
the hood is done at home. Nothing is tapped or countersunk by the shop; OSH Cut
does not countersink this thickness. The colour wanted for the core, the
hood and the side panels is its Camo Green FED, Prismatic Powders PSS-11240,
a flat olive matched to FS 34094; the tray and the shelf are to be matt
black, and which of its blacks is not chosen. The model's green is near FS
34094 by eye, not matched to a swatch.

The parts were first drawn as five for Fabworks, with the core's bottom, rear
and top in one piece and the front and both sides in another, the shell. Both
are U shapes with 255 legs on a 210 and a 131 base, and Fabworks' and OSH
Cut's bend simulations both refused the last bend of each: the standing leg
hits the punch. Both shops use the same 220 tall punches, which reach a leg
about 145 tall on a 131 base. So the top and the front are now one part,
the hood, an L like the core, and the two sides are parts of their own. No
part has a leg over 35 beside a base under 86.

Shops that might fold the two U shapes as first drawn were looked for on
2026-11-23. None with an instant quote does. Approved Sheet Metal (Hudson,
New Hampshire) says it forms boxes to 12 in deep with gooseneck and stacked
punch holders, and quotes by hand from a model and a drawing; it has not
been asked. Jugao, whose advertisement prompted the search, makes press
brakes and tooling and does not make parts to order.

## Checked

- Clashes: the whole assembly, 163 bodies with every screw, nut, stud, handle and fan
  in place and the mains lead on its route, has no two parts sharing volume apart from threads in what they
  screw into.
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
- Sheet metal rules, against OSH Cut's figures for 0.048 in A1008, read from
  its catalog 2026-11-21: the parts are drawn with its tooling's inside
  radius of 1.32 (0.052 in) and K of 0.45, and its hardware is the same PEM
  parts with the same holes. [mechanical/dfm.py](../mechanical/dfm.py)
  measures every cut-out in the five flat patterns: the smallest is 2.0
  across (0.61 recommended), the thinnest web 2.07, and none is within 5.72
  of a bend line, which is how far its die reaches. That put the side
  panels' screws 8.0 inside the rear panel and the shelf's rear wall 2.8 behind the
  supply, with the mains lead 0.7 nearer the board to suit, and the shelf's front
  wall is only as wide as the space between the supply's front screws, so
  that none of its holes is near that bend.
- Flanges: dfm.py also measures every flange all along its bend, from the
  bend line to the flange's edge, against the 5.72 of support OSH Cut asks
  for. The shortest are the shelf's, 7.8 and 7.9.
- Bend reliefs: where two bends meet there is a round relief 3.0 across,
  from the sheet rule.
- The hood: the top and the front in one part. Its top lies on the rear
  panel's top lip, 16.5 long at the two corners and 9.5 between them, short
  of the mesh, and the rear handle's two screws go up through the lip and
  the top into the handle's legs. Its rear edge is flush with the rear
  panel's outside face. The top's lip on the tray's side is riveted to the
  tray. The front's flanges stand in line with the core's side lips. Where a lip
  of the hood meets one of the core, at the top of the rear and the foot of
  the front, the two are mitred at 45 degrees and 1.2 apart, as two lips of
  one part are. The side panels screw to both, and the one on the tray's side is
  riveted to the tray. At the front's foot a return goes under the bottom
  panel, against it, between the side panels' returns, with a tab at each
  end for a fan screw, cut at a slant 0.6 clear of a foot.
- Lips: every side lip of the core and the hood, and the bottom panel's
  front lip, is 15 on both sides of the case. That is the least a lip with a
  pressed nut can be: OSH Cut's die needs the nut's hole 5.72 from the bend
  line and PEM needs the nut's centre 5.6 from the lip's edge, 14.8 in all.
  A lip with only rivets could be about 13. The rivets are on the nuts'
  line, 8.0 from the panel.
- The shelf hangs from the top on four screws: two into tabs on its rear
  wall, as before, and two into tabs on a front wall 82 wide, between the
  switch and the lamps. No tab shows in a cell of the mesh. The supply's weight goes into the top and from
  there into the rear panel, the tray and the front.
- The side panels: one part, used on both sides turned end for end. Each
  covers the edges of the rear panel and the front and is 0.5 clear of the lips
  and flanges behind it. Every nut is 5.76 or more from an edge (PEM asks
  5.6) and its hole 5.76 from a bend line (5.72).
- Lamps and button: each is under a leg of the front handle, fixed in the
  front. The clash check has them clear of the shelf, the supply's screws
  and the handle's screws.
- Handles: RAF 8120-632-A-24, 4 in between centres, against Fascomp's
  drawing of the same part. Each leg has 2.2 of metal to the nearest mesh
  cell and is 3.4 inside the side panel's flange; the screw heads under the top
  panel are 5.5 from the rear panel, 11.3 from the top fan and clear of
  the switch and of every part of the board.
- OSH Cut's rules, in full: [mechanical/dfm.py](../mechanical/dfm.py) also
  checks each flat pattern's size against the 119 x 59 in sheet, that there
  is a hole to hang the part by for coating, each pressed-in part's hole and
  its distance to the nearest edge against PEM's figure, a straight edge of
  0.25 in or more parallel to every bend for the back gauge, and a relief
  wherever two bends meet. All 81 checks pass. It found one fault, now
  fixed: the bottom panel's front lip met each side lip with no relief.
- The punches: OSH Cut publishes Wilson's bend limit graphs for its two,
  61228010 (28 degree) and 61086010 (86 degree swan neck). Read from them, a
  leg already standing d from a bend may be about d tall under the first and
  d + 30 under the second, for d from 25 to 110. The tightest part is the
  shelf, folded tabs first, then the front wall, then the rear wall: at the
  last bend the front wall stands 34 tall 66 away, and its tab reaches back
  to 47 away at that height, where 47 tall is allowed. The other way round
  would not fold. On
  the core and the hood the bend between the two panels is 122 long between
  lips 128 apart, which wants a punch made up to between those, 125 say.
  Everything else is a lip or return under 17 beside a base over 200.
- Clearances: [mechanical/clearances.py](../mechanical/clearances.py) lists
  every gap under 1.0 in the assembly, the wires apart. None is unintended.
  The smallest that matter: the supply 0.7 from the front's flange and 1.1
  from the tray, the front feet 0.8 from the tabs of the hood's return (0.2
  before the return was shortened to 8.5), a side screw's tip 0.6 beside the
  rear fan's frame, and the side panels 0.5 from the lips.
- Screws, all the 1/4 in case screw: a side panel's goes right through its
  nut; a handle's has 5.2 of thread in the leg at the front and 4.0 at the
  rear, where the leg is tapped 7.9 or more; a shelf screw goes right
  through its nut; a fan screw has 8.8 in the fan's frame, 7.6 for the two
  through the hood's tabs.
- Rivets: eleven, all holding the tray: three along each of its bottom, top and rear edges and two up its front edge, into the front's flange below and above the supply. Each is 7 or more from its lip's edge and from the bend, with a
  bar's width of flat behind it inside. Flush outside and 1.5 at most
  inside, which the 0.3 to 0.5 outside the lips and the 2.8 between the tray
  and the fans both need.
- The 13.1 between the board and the supply stays. It comes from spacing
  the bottom fans so one mesh pattern suits both, and the 8.3 it leaves
  between those fans is where their cables come up.
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
- Fits that depend on two bent parts are loose: the side panels
  are 0.5 clear of the lips all round, and the clearance holes for the
  shelf's and side panels' screws are 4.5. OSH Cut holds +/-0.38 on a bend, and powder coat takes
  some of the 0.5: see below.

## Open: before the order

- Upload the five STEP models to OSH Cut and read its bend simulation for
  each. The check against the published graphs above is by hand and is not
  that simulation. The core and the hood are each an L with lips down both sides of
  both panels, so the bend between the panels needs a punch that fits
  between the lips. The shapes are inside the published limits of its punches, but its
  simulation is the test, and nobody has run it on these files yet.
- Powder coat. OSH Cut does not publish how thick its coat is, whether it
  masks threads, or whether hardware goes in before or after. Ask, because:
  the side panels go over the lips with 0.5 to spare, and a coat
  on both faces takes 0.1 to 0.2 of it; the I/O aperture and the
  holes for the switch and lamps are sized bare; the nuts, studs and standoffs must stay clean;
  and the board grounds to the case through the standoffs and the tray,
  which a coat on the joint faces would insulate. Coating only the hood
  and the side panels would avoid most of this, but the hood's four nuts
  would then want masking.
- The rivets go in after the parts arrive, so on coated parts their heads
  and the countersinks are bare metal. All eleven are on lips under the
  tray-side panel.
- OSH Cut presses hardware in after bending. The four nuts in the rear
  panel's side lips and the four in the front's flanges are 8.0 from
  the panel, inside the corner, and the
  four studs are in the floor of the core. Its quote checks hardware
  against bends; read what it says.
- The handles: two RAF 8120-632-A-24 (Fascomp FC8120-632-A-24), black
  anodised. AFT Fasteners lists them in tens. The plain stainless
  8120-632-SS is the same size if the black one is out of stock.
- Rubber U channel for the notch in the shelf's rear wall, about 35 of it
  for 1.2 sheet. The one drawn is a placeholder.
- The switch's and the lamps' holes in the front are sized bare, 12.0 and
  8.0; a coat narrows them.
- The hood's and side panels' outside faces want to arrive unmarked, and
  die marks show on every bend. Ask.
- The feet are printed in 316L stainless steel and tapped 6-32 by a 3D
  printing service. Craftcloud will do both. The hole goes right through,
  so an ordinary tap does it, at home if need be.

## To do at home

Tools: a 100 degree countersink, a flat punch and a hammer, a steel bar to
hold against the rivets' tails, and eleven MS20426AD3-4 rivets with a
few spare. McMaster-Carr sells them as 96685A146, Aircraft Spruce and Van's
Aircraft by weight.

1. Countersink the eleven 2.5 holes in the lips of the core and the hood
   from outside, to 4.6 across, until a rivet's head sits flush.
2. Rivet the tray to the core's side lips, six rivets: head outside, the
   bar against the tail inside, until the tail is 3 to 4 across and about 1
   tall. Slide the hood on from the front, its return under the bottom
   panel, and fit the rear handle, whose two screws hold its top down. Then
   the other five rivets, tray to hood.
3. Paint, if wanted, with the threads, studs and standoff bores masked.

## Known limits of what has been checked

- Nothing has been built. Bend accuracy, how flat the rivets pull the joints and how the
  side panels sit are only known once a first one exists; expect to adjust.
- The airflow and heat study uses a simplified case and assumed fan curves;
  see [thermal.md](thermal.md).
- The board is drawn as a block. Framework's own model of it was last
  checked against the standoffs and the panels on 2026-11-21, before the
  parts were split, and nothing that it sits against has moved since.

## Putting one together

1. The front handle onto the top, a screw up into each leg from inside,
   while the case is empty (the rear one is on already). Feet onto their
   studs with the PH2 screwdriver, then a bumper into each
   foot's recess, over the cross slot. Supply onto the shelf with its 6-32
   screws, three or six as the unit has threads, exhaust face up.
2. Fans into the core, the front one's two front screws through the tabs of
   the hood's return. Board onto its standoffs, heatsink fan, mains inlet.
   Switch and lamps into the front. Cables tied to the tray's slots between
   the board and the supply.
3. Shelf in through the open side, low, then up against the top. Four screws
   down through the top.
4. Wiring, then the
   two side panels, four screws each.
