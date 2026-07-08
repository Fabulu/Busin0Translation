# SPEC — Alchemy-shop item-name / quantity overlap (GitHub issue #10 sibling)

Date: 2026-07-08. Status: SPEC ONLY — no patch proposed, no patch applied.
Bug class precedent: Patch-28 (4-5 static guesses falsified) → runtime layout, live-debugger required.

## 1. Evidence

| Asset | Source | Notes |
|---|---|---|
| ramdumps/_alchemyshop_shot.png | Screenshot.png from ramdumps/Alchemyshop.p2s (Jul 6 19:46) | Magic Stones synthesis screen, 2 list items |
| ramdumps/_pillshop_shot.png | Screenshot.png from ramdumps/pillshop.p2s (Jul 6 22:16) | Same screen, 1 list item, wrapped description |
| scratchpad alchemyshop_ee.bin | eeMemory.bin from Alchemyshop.p2s (33,554,432 B, NOT zstd — raw; VA == byte index) | R34/R39 images located |

CAVEAT: Jul-6 saves predate v174–v179 EXE builds (pre-Option-E). Fine for LAYOUT recon;
NOT valid for EXE-state conclusions.

All pixel coordinates below are in the 640x480 PCSX2 screenshot space (the emulator's
output scaling of the GS frame; GS-internal pen units may differ by a scale factor —
treat coordinates as ratios/columns, verify absolute values live).

## 2. Screen anatomy (both shots — "Magic Stones" / "Select the magic to synthesize.")

- Header banner "Magic Stones": top-left, ~x=20..190, y=15..40.
- Item LIST BOX (the collision site): gold frame, outer ~x=35..278, y=103..306.
  Interior text field ~x=44..258. Row pitch ~25 px, glyph height ~18 px.
  Row 1 text band y≈112..136, row 2 y≈137..158. Selected row is a blue highlight
  bar spanning the full interior width (~x=44..258).
- RANK panel (right box, ~x=290..605, y=105..245): "Rank" header + spell rows
  Bewm/Vera/Erika = "Cant" (red), Konde = 0/60 (alchemyshop) / 1/20 (pillshop).
  Quantities here do NOT collide (names are short).
- Selected-item PILL capsule: bottom-left, rounded rect ~x=24..222, y=358..390.
- Description area: bottom, name-header line (orange "Mage Magic Lv2") y≈396..408
  starting x≈240, body text below.

## 3. Collision A — list-row: fixed-column quantity over variable-width name

This IS the "alchemy-shop name/quantity overlap".

- Item name: left-aligned from x≈50, fixed-pitch ASCII glyphs (~12 px/cell,
  the v93 monospace pitch).
- Quantity "held/cap" (e.g. 0/40): right-aligned, ending x≈252 (interior right
  edge ≈258). It is drawn in two parts:
  - numerator digit in a LARGER font, occupying ≈x=209..228 (visibly taller
    than the name glyphs),
  - "/40" in a smaller font, ≈x=228..252.
- No clipping, no ellipsis, no elision: both fields draw at full opacity in the
  same band, quantity drawn over/with the name.

Collision arithmetic (measured):
- Name budget before entering the numerator column: x=50..209 → ~159 px →
  **~13 glyph cells fit clean; character 14+ collides.**
- "Zateal Spell Book" (17 chars, ends x≈232): last ~4 chars under/behind the
  numerator — renders as "Zateal Spell Bo0k40"-style garble.
- "Yaiba Spell Book" (16 chars): the "k" sits directly under the big "0"
  (pillshop shot: reads "Yaiba Spell Boo0/40").

Nature: **a fixed right-anchored quantity column overlapping a variable-width
left-aligned name.** JP names (full-width glyphs, few chars) never reached the
column; 12-px-pitch English names >13 chars do. There is no evidence of any
width clamp on the name draw.

## 4. Collision B — pill capsule overflow (dossier issue A, visible in BOTH shots)

The selected-item pill at bottom-left, capsule extents **x≈24..222, y≈358..390**
(right border pixels x=219..222; vertical run y=358..390).

- alchemyshop: name "Zateal Spell Book" renders as "al Spell Book" — the string
  START is off-screen (extrapolated start x≈−60 at 12 px/cell), text is clipped
  by the SCREEN edge at x=0, and ends at x≈141, leaving ~80 px of the capsule
  interior EMPTY on the right.
- pillshop: "Yaiba Spell Book" renders as "ba Spell Book" (start ≈x−36,
  end ≈x143). Same signature.

So the pill text overflows the capsule's LEFT edge (opposite side from the
town-return-potion evidence) while wasting right-side interior space. Mechanism
UNCONFIRMED — the asymmetry is consistent with a centering/right-anchor
computation that measures the string at JP full-width (24 px/char) but draws it
at the 12 px English pitch, but this is a HYPOTHESIS only. Cross-ref:
build/PILL_INVESTIGATION_DOSSIER.md (widget family EXE 0x13F5xx + jal 0x14DF30).
Do NOT touch 0x13F688 (falsified, banner regression).

## 5. Other anomalies visible in these shots

1. **Unwrapped description (alchemyshop):** Zateal body "Deals lightning damage
   to an enemy g…" is ONE line, clipped at the right screen edge x=640
   (band y≈410..428). pillshop's Yaiba description wraps correctly into 4 lines
   (~30 chars/line). Relevant to dossier gap #3 (sub9 36-cell wrap never
   render-verified). Cause UNCONFIRMED: the Jul-6 save may predate the v173
   wrap fix, or this entry missed the wrap injection — needs a current-build
   capture before concluding.
2. **"Cant" (no apostrophe)** ×3 in the Rank panel. Source identified: R39
   (build/packdata_resources/0039_type15.raw contains glyph-encoded "Cant" ×8,
   "Rank" ×3). Cosmetic wording nit; whether intentional (width) is UNCONFIRMED.
3. Rank-panel quantities (Konde 0/60, 1/20) show the same big-numerator/small-
   denominator style but no collision — short names.
4. The pill capsule text is additionally clipped by the physical screen edge
   x=0 (leading characters unrecoverable on-screen).

## 6. EE-RAM findings (Alchemyshop.p2s eeMemory.bin, raw 32 MB, VA == index)

- **R34 item-DB image base = 0xE168C0** (len 0x1D000; matched byte-for-byte
  against build/packdata_resources/0034_type20.raw).
  - "Zateal Spell Book" glyph string @ **0xE2C100** (= R34 file offset 0x15840),
    BE u16 glyphs (id = ASCII−0x20), FFFE FFFF terminated.
  - "Yaiba Spell Book" @ **0xE2C3BA**.
  - "Mage Magic Lv2" ×4 (0xE2D206, 0xE2D2C2, 0xE2DC60, 0xE2DEA4 — all inside R34).
- **R39 image loaded immediately after R34** (~0xE338C0+): "Cant" hits at
  0xE33BF0.. and "Rank" at 0xE358EC lie just past R34's end and match R39 content.
- **Quantities are NOT stored as strings anywhere in RAM** — no glyph-encoded or
  ASCII "0/40"/"0/60" scratch buffer exists in the snapshot. The n/cap display is
  composed digit-by-digit at draw time from a count field.
- **No layout structs adjacent to the strings**: the name records are pure glyph
  streams inside the resource image; no x-coordinate halfwords nearby. The
  quantity column X and the name pen X are runtime-computed — confirming the
  prior analysis that there is **no static patchable immediate** to find from
  dumps alone.

## 7. Live-debugger breakpoint plan (required next step — NO static patch)

Setup: PCSX2 debugger, load ramdumps/Alchemyshop.p2s (layout recon is valid on
this pre-Option-E save; do not draw EXE-state conclusions from it).

1. **Catch the name draw:** hardware READ breakpoint on 0xE2C100 (first u16 of
   "Zateal Spell Book"). Fires on the list-row draw. Record the full caller
   chain and the register/stack slot carrying the pen X at glyph-emit time.
2. **Catch the quantity draw:** breakpoint on the known glyph text-advance VAs
   0x308CB0 / 0x3097A4 (v97 render-truth) conditioned on the frame section after
   (1) fires; log per-glyph draw X. The first digit drawn at column ≈209
   (screenshot space) identifies the quantity routine; walk up to find where its
   right-anchor column is computed/stored (likely a widget struct field).
3. **Pill capsule anchor:** READ breakpoint on the same name string when the
   bottom pill redraws (cursor move re-triggers); diff the caller chain vs (1).
   Record the anchor X computation — specifically whether the string width is
   measured with a per-glyph advance table (which one) or a fixed 24 px
   assumption. Cross-check against PILL_INVESTIGATION_DOSSIER.md's
   0x13F5xx/0x14DF30 widget family.
4. Deliverables from the session: (a) routine + struct offsets for the quantity
   column X, (b) whether the name draw has any width/clip parameter, (c) the
   pill text anchor formula. Only then design a fix.

Explicitly out of scope: any EXE byte change based on this document alone.
