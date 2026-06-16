# Spacing & Box-Geometry Baseline (v101, 2026-06-16)

Empirical measurements from GS dumps (Shift+F8) of the v101 build, for the planned
**pixel-aware re-wrapping of all dialogue + narration** (task: longer lines once
spacing is final). Glyph X positions = min sprite vertex x / 16, from
build/recon_v86/gs-vram-atlas/gs_atlas.py (font sprites tex0.tbp0==0x3000, psm 0x14).

## Current per-glyph spacing (v101, PATCH 13/14)
- Letters: **18px** advance (monospace), uniform.
- Space (glyph id 0): **9px** advance.
- Applies to BOTH intro narration AND barkeep/scene dialogue (same render path,
  hook VA 0x3097A0). Confirmed across heavy_fog, spaces1-4, desolatecity dumps.

## Narration text area (CENTERED)
- Lines are centered (origin x0 = 279 - count*9 after PATCH 13's count*18 centering).
- Observed x range across lines: ~87 .. ~339; screen center ~213.
- Widest observed line: **252px** ("settled over the", 16 chars incl spaces).
- 4 lines visible per screen (y = 199, 223, 247, 271; pitch 24px).

## Dialogue box (barkeep — LEFT-ALIGNED)
- Left margin: **x = 51** (text origin).
- Widest non-clipping line observed: **324px** = "handles requests for" (20 chars),
  spanning x=[51, 375]. Did NOT clip horizontally -> box right edge >= ~375, and the
  20-char wrap is conservative (room for more).
- Lines at y = 327(name) then 375,399,423,447,471 (24px pitch). Body shows 5 lines
  here and OVERFLOWS (line 5+ cut off, does not continue to a next page) -> overflow
  is VERTICAL, not horizontal.
- Rough char capacity: 20 chars = 324px -> ~16px/char avg at 18/9. If usable box
  width ~430px (NEEDS precise measurement), that is ~26 chars/line.

## OPEN (measure precisely during the re-wrap task)
- Exact dialogue box RIGHT edge / clip width (the 512x512 "box quad" the parser
  found is the font-atlas upload, NOT the text box; the parchment frame is drawn in
  an earlier frame and not re-issued, so it wasn't in these single-frame dumps).
  Get it from the dialogue renderer (func 0x307510) clip/box setup, or a GS dump
  taken on the frame the box is drawn.
- Vertical line capacity of the dialogue box (Patch-12 era note: box y≈363..473).
- Proportional per-glyph advance table (in flight: workflow proportional-narration).

## Re-wrap design implication
Wrapping must become PIXEL-aware: wrap when summed per-glyph advance exceeds the box
usable width, NOT at a fixed char count (TYPE2_WRAP_WIDTH). Narration uses the
centered area (~screen width, centered); dialogue uses [51 .. box_right]. This packs
more per line and fixes residual vertical overflow (barkeep) everywhere at once.
