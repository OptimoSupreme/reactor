# Sitrep, 2026-11-19

Delete this file before the branch is merged to `main`. It is a handover note, not documentation.

## Where things stand

The `high-detail` branch holds four pieces of finished work: the Mk I name is gone and the branch
is `main`, every cable is a smooth spline, the high detail model uses Noctua's own fan models, and
the drawings come from SolidCraft's native drawing workspace. All of it was built and checked on
SolidCraft 0.45.0.

The branch is blocked on one thing. SolidCraft 0.45.0 rebuilds two of the five sheet metal parts to
different sizes than 0.44.1 did, so the shop files on this branch are not the ones that were tested
and audited. Do not merge, and do not order from these files, until that is resolved.

## The problem

0.45.0 replaced SolidCraft's whole sheet metal model (tangency-labs/solidcraft PR #9245). The same
`mechanical/reactor.py` now gives:

- Shell: the front panel ends at Z 210.85 instead of 212.9, so it is 2.05 shorter at the top and at
  the bottom and no longer covers the edge of the core's top panel (211.2). The cut is the sheet
  thickness plus gap/√2, and the rule's default gap is the sheet thickness.
- Core: the corner reliefs on the front lips moved by about 0.15 (24 of 2528 flat pattern entities).
- Tray, bulkhead and shelf: unchanged, entity for entity.
- All five flat patterns are mirrored and their bends read "down" instead of "up". That is the same
  physical part seen from its other face.

Opening the committed 0.44.1 design in 0.45.0 shows the same change, so it is the app and not the
script. No rule or flange setting brings the old shell back: the smallest gap (0.01) only gets the
front edge to 211.69.

It was reported upstream as https://github.com/tangency-labs/solidcraft/issues/19758, with a
100 x 60 x 50 channel that reproduces it: the web is cut back along its whole free edge, and the two
mirror-image corners are closed two different ways. The author of the refactor replied on the
project's chat the same evening that it is "50/50": one of the two changes was made on purpose, the
other is an accident, and he is fixing it. He did not say which is which. Read the issue for that
before assuming anything.

Later that evening he said "fix incoming" and shared a diagram of the proposal. Nothing was public
on GitHub at that point (no PR, branch or comment naming #19758), so treat this as a proposal that
may change:

- The accident is the cut running the whole width of the web, and the missing joint at the second
  corner. Both go.
- The intended part stays: a return and the panel beside it now get a joint at their corner. The
  proposed default is "Miter", which notches the web under each return only, T + gap/√2 deep and
  gap/√2 wider than the return. On the shell that is a notch about 2.05 deep and 10.35 wide at each
  of the four front corners, which 0.44.1 did not have.
- Two lap options are proposed beside it. "Web laps over" leaves the web uncut and stops each
  return at the bend line, which is exactly the 0.44.1 geometry. "Return laps over" notches the web
  T + gap deep under each return.

So the fixed version's default will probably not give the old shell. Expect to ask for the "web
laps over" joint on the shell's returns, and look at what the core's front lips need, once the
release shows how the option is spelled.

## The goal

Wait for the SolidCraft release that carries the fix, then rebuild with it and get back to the
0.44.1 dimensions.

1. Check the issue and the releases. When a fixed version is out, fetch its AppImage and verify the
   checksum.
2. Run the channel from the issue in it first. In 0.44.1 the web's top edge is at z 50 and both
   returns end at x 98.
3. Restart SolidCraft, run `mechanical/reactor.py`, then `mechanical/drawings.py` (the build
   rewrites `reactor.sc` without its drawings, so the drawings always run second), then
   `mechanical/renders.py` and `mechanical/dfm.py`.
4. Compare every flat pattern, bend table and STEP in `mechanical/export/` with the 0.44.1 ones,
   which are in git at commit 1efac52 (`git show 1efac52:mechanical/export/shell.dxf`). The target is the same geometry: front
   panel to Z 212.9, core reliefs as they were. Mirrored flats are fine if upstream confirms that
   part is intended, but say so in the docs, because bend directions on the drawings flip with it.
5. If the fixed version still differs because the remaining change is the intended one, stop and
   ask Justin. Changing the model to suit, or accepting new dimensions, is his decision.
6. Delete this file, then ask Justin about committing and merging.

## Verified on 0.45.0

The last full run gave 0 clashes over 146 bodies, the same board fit report as before, 30 of 30 in
the rule check and no findings in the drawing check. The exports, drawings, renders and both
assemblies in the working tree are that run's, so they carry the 0.45.0 geometry.

## Loose ends

- Nothing on this branch is committed. `main` is one commit ahead of the remote, as it was before.
- `sim/airflow.py` was already broken (it uses `SHELL_Y` names that no longer exist); only its
  import was renamed.
- The Noctua pads are drawn uncompressed and overlap the panels by 0.5 to 0.7.
- On the foot's drawing the automatic "VIEW A" label sits close to the Ø20 dimension.
- Old `.sc.bak` files in `mechanical/` still carry the Mk I name.
- A full build peaks near 17 GB of memory. Restart SolidCraft before each one.
