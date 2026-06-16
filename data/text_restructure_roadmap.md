# Game-Wide Text Restructure Roadmap (px-aware wrap + centering + corpus re-author)

Source: recon workflow ws2mazf2u (2026-06-16). Confidence: medium. Goal: exploit the
solved proportional+narrow spacing (uniform 3px gaps) to fit MORE chars/line across ALL
dialogue + narration, fix line centering, and re-author the corpus.

## CRITICAL PRINCIPLE (the #1 failure mode to avoid)
The build wrap, the in-EXE advance table, the centering reserve, and every test gate MUST
read **one shared metrics module**. If any computes glyph widths independently they silently
desync. So Stage 0 first, always.

## Verified grounding
- `build/recon_v86/r1188_ascii_metrics.json` = 95-elem list, gid 0..94 = char-32 = `enc(ch)`
  = in-game ADV table index (zero remapping).
- `ADV[g] = 9 if g==0 else clamp(ink_width+3, 6, 23)`; `LEFTSHIFT[g] = max(0, ink_left)`
  (byte-identical to `build/apply_prop_diag2.py` L36-40). avg ~17.5px; real prose ~13-15px/char.
- Build wrap is isolated to 3 helpers in build/build_v9.py (`_wrap_line` L258, `wrap_type2_text`
  L274, `reflow_dialogue` L287); encoder L449-456 is break-agnostic (glyphs + 0xFFFE, never 0xFFD2).
- Narration is a SEPARATE path: tools/patch_r1193_narration.py `_flow_page` (MAX_LINE_GLYPHS=23)
  + a HARD per-record assert and a FIXED 23-record 0x14 trailing layout (PAGE_LINES) — the px
  wrap must still yield the same PAGE_LINES count per page.

## Ordered steps
0a. **Single metrics module** — NEW `tools/glyph_metrics.py`: ADV[], LEFTSHIFT[], `px_width(s, enc)`.
    Feeds build wrap + EXE cave tables + centering + tests. (pure extraction, no behavior change)
0b. **Bake proportional into patch_exe.py** — promote the 2 caves from apply_prop_diag2.py:
    Stage-1 ADV cave @0x4C7540 + table @0x4C7564; Stage-2 draw-shift cave @0x4C7670 hooking
    0x309750 + LEFTSHIFT table @0x4C7690. Tables generated from glyph_metrics. REPLACES monospace
    PATCH 14. (currently proportional lives ONLY in the diagnostic, not the shipped EXE)
1a. **Centering Stage-3** — replace PATCH 13 count*18 reserve (0x305988/90, 0x3059F8/A00, the
    (c<<3)+c idiom) with a cave that reserves SUM(ADV) per line so origin = center - sum/2.
    Layout pre-pass glyph id live in a1 @0x302E88; origin 0x305980-0x305998; per-line 0x308364/0x30836C;
    renderer reads origin from desc+0x3c(+0x3e). Cave per-line sum MUST equal build px_width.
1b. **Narration px-wrap** — build_v9 `_wrap_line` -> px-based vs NARR_BOX_PX (interim 300);
    patch_r1193 `_flow_page` -> pixel budget; relax the count assert to width<=NARR_BOX_PX but
    KEEP a glyph-count ceiling at the record limit (FIXED 23-record layout).
2a. **Dialogue px-wrap (opt-in)** — single `wrap_px(text, box_px, collapse)`; DIALOGUE_BOX_PX=324
    interim (x375-x51 proven non-clipping; raise only after box-right measured). Gate behind a
    DIALOGUE_PXWRAP_ALLOW set starting with R1197 (barkeep baseline). Choice + (1197,1) excluded.
2b. **Re-derive R1203_MAX_GROUP** — px-wrap = fewer 0xFFFE = Section 2 shrinks; rerun
    build/recon_v89/phase2/r1203_cap.py; do NOT assume.
2c. **Convert test gates** — tests/test_line_width.py MAX_GLYPHS=20 -> px_width<=box_px; add
    G2 box vertical-capacity, G4 centering, G5 choice/(1197,1) byte-identity, G6 R1203, G7 BFS Sec1.
2d. **Corpus dry-run worklist** — run wrap_px over WHOLE corpus (batch_*.json, chunk_00-09 +
    r38_fix, R1193 TRAILING_PAGES); report old vs new line counts, chars/line gain, groups still
    overflowing VERTICALLY (need authored ' // ' split or tighter wording — NEVER auto 0xFFD2).
3. **Full rollout** — remove the opt-in; apply manual re-author edits from the worklist; final build.

## Open decisions (must measure before raising limits)
- Exact DIALOGUE box right-edge clip (from func 0x307510 clip setup or a box-draw-frame GS dump)
  before raising DIALOGUE_BOX_PX past 324.
- Dialogue box VERTICAL line capacity (y~363..473): does px-wrap line-count reduction alone clear
  the barkeep 5-line overflow, or are authored ' // ' splits still needed?
- NARR_BOX_PX exact value (interim 300) vs the Stage-3 centering reserve clamp.
- Confirm renderer reads narration origin ONLY from desc+0x3c(+0x3e) (single cave suffices).
- R1193 per-record glyph ceiling (the 23-record 0x14 layout max addressable glyphs/record).
- New R1203_MAX_GROUP after px-wrap.
- Net PACKDATA size delta (latent BSN2_0.DSI overflow may shrink/grow/cross a boundary).
