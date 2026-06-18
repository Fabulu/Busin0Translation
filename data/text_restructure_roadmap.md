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

## Playtest-observed issues to fix in this restructure (added 2026-06-18)
Evidence saves live in ramdumps/ (and build/) — boot FRESH to reproduce.
- **Overflow WITHOUT wrap, top-right element** — `anotheroverflow.ps2`. A text box (top-right of
  screen) renders past its right edge and never wraps. Its render path is NOT covered by the
  build wrap helpers (Step 2a list) — find which box/resource it is and route it through `wrap_px`.
- **Too-early text wrap** — text wraps well before the box right edge (wasted line width). The
  current wrap budget is too conservative for the proportional metrics; this is the flip side of
  Step 2a (DIALOGUE_BOX_PX=324 interim is a guess). Must measure the real box right-edge clip
  (Open decision #1) and widen the budget so lines fill the box.
- **Chargen text boxes need the spacing fix** — full executable plan in
  **`data/chargen_spacing_backlog.md`** (6-agent analysis wvc2fwiw6, 2026-06-18).
  CORRECTION to earlier assumption: chargen prose text is NOT a different font system. The prompt
  bars (R37 MSG) and description/personality boxes (R38 MSG) render through the SAME R1188 24x24
  atlas as narration, via a sibling sub-path (Path 1) of the SAME renderer func 0x307DA0 — so the
  fix REUSES tools/glyph_metrics.py + data/r1188_ascii_metrics.json unchanged (gid==char-32).
  Path 1 uses pen 0x1cc(sp) (narration uses 0x1ce(sp)), so a Path-1 cave can't disturb the shipped
  narration fix. ONE Path-1 cave at the advance site VA 0x308040 (addiu v0,v0,0x18 fixed 24px) covers
  ALL chargen boxes; ship Stage-1 advance + Stage-3 centering (count*12 @0x307FBC/0x307FC4) TOGETHER
  or every line drifts. R2100/R2138 only supply the pre-rendered stat/keyboard/tab labels that
  coexist on-screen (Family C, separate pixel-strip track). GATE: a live .gs.zst + single-step of
  0x307DA0 on ramdumps/space2.p2s must confirm Path 1 + the gid register BEFORE cutting the cave.

## Request menu (R39) remaining polish (added 2026-06-18) — freeze + content FIXED, two cosmetic items left
The request-menu FREEZE is fixed (section-table remap) and v115 fixed the offset BASE so all quest
content (titles/descriptions/clients/labels) resolves to correct English. Two cosmetic issues remain:

### BUG A — 12-cell title/label field clip (needs a decision)
The single-line request TITLE/LABEL field is drawn by `draw_clamp12` @ VA 0x3A3300: HARD cap 12 cells
(`slti r1,r3,0x0d` @0x3A3370; `addiu r23,r0,0x0c` @0x3A337C) + RIGHT-ANCHOR (shows the TAIL). So
"Treasure of the Ancient Royal Palace" (offset correct) displays as "t Royal Palace". Physical field
width ~15-18 cells before colliding with the R1 page/scroll glyph. EXE cap-raise needs 2 more traces
(the un-located right-anchor pre-advance + box geometry) and STILL can't fit 36-char titles -> recon
recommends OPTION A: shorten the 33 quest titles to <=12 cells (data edit in
data/type2_translated/batch_r39_equip_b.json, groups G443-476). Proposed short forms exist in workflow
wd76rp3we synthesis (e.g. "Treasure of the Ancient Royal Palace"->"Royal Hoard"). LOSSY — needs user
sign-off on wording. Full text stays legible in the uncapped description body (draw_stream 0x3A2EF0).

### 民 kanji on some detail labels — DUAL-PURPOSE TABLE corruption (intricate; pre-existing since v84)
ROOT (verified against pristine R39): the four R39 quest offset tables are DUAL-PURPOSE. G411 and G442
embed a SHARED KANJI GLYPH DICTIONARY in their interiors, and 13 cross-table slots point INTO it:
  - G381 (client) slots 55,57,59,61,63,65 -> G411 interior (g5,g10,g26,g31,g37,g43)
  - G411 (uilabel) slots 54,56,58,60,62,64,66 -> G442 interior (g11,g25,g29,g37,g42,g48,g56)
  - G442 dictionary GLYPHS live at slots [40:71] (pristine values 540,566,584... = 口重全聞突誰功能獲焼...)
inject_r39_quest.py's offset rebuild (new_target=new_gs for ALL slots) does TWO wrong things:
  (1) collapses the 13 cross-table pointers to g0 (value -> 966=民 / 786) -> the "民 民 民" run;
  (2) REMAPS the dictionary-glyph slots (G442 [40:71]) as if they were offsets -> destroys the kanji
      (pristine 口重全聞... -> garbage 頼合...).
THE FIX (careful, not yet done): in build/inject_r39_quest.py rebuild loop, classify slots:
  - target = content group -> new_gs (current, correct);
  - target = inside an offset table (gi in TABLE_GROUPS, the dictionary) -> preserve glyph ORDINAL:
    new_target = new_group_starts[gi] + glyph_idx*2 (re-point at the dict glyph's new position);
  - the dictionary-GLYPH slots themselves (glyph ids, not offsets) -> PRESERVE VERBATIM (do not rebuild).
The hard part: distinguishing dictionary-glyph slots from real offsets by value alone is impossible
(a glyph id 540 also resolves as an offset to a content group). Need to HARDCODE the dict regions
(G442 [40:71], G411's dict slots) from the verified pristine map above, or detect via "value resolves
mid-group / not to a group start". Cosmetic + pre-existing (v114 had it too) -> deferred, not urgent.

## Translation QA: NAME CONSISTENCY audit (backlog, added 2026-06-18, user)
A character/place is romanized DIFFERENTLY in different places, and the dialogue body can disagree
with the character's actual NAME slot. Confirmed example: Japanese **ライマン** appears as "Layman"
in some dialogue and "Rainman" in others (name slot vs dialogue text disagree). ライマン (Raiman) is
genuinely ambiguous romanization — a canonical form must be DECIDED then applied everywhere.
TASK: scour ALL dialogue + name data for name-spelling discrepancies and reconcile to ONE canonical
form per name.
APPROACH (scriptable audit):
1. Build the canonical name list from data/glossary.json (225 entries, has "name" fields) + the EXE
   NPC name table (patch_exe.py Patch 3, Table 2F) — map each Japanese name (e.g. ライマン) -> its
   ONE intended English spelling. Decide canonical where ambiguous (Layman vs Rainman -> pick one).
2. For each canonical Japanese name, grep ALL translation sources — data/type2_translated/batch_*.json,
   data/translate_chunks/chunk_*_translated.json, R39 client names, R46/R47 bulletin, strip_labels —
   for every English variant currently used, and flag mismatches.
3. Produce a discrepancy report (japanese | canonical | variants-found | files) and a fix worklist;
   apply the canonical spelling everywhere.
4. Special care: names rendered via glyph-id streams (NPC name table, R39 clients) vs ASCII text —
   both must match. Cross-ref data/guide_crossref_inferences.json (has the ライマン decoded contexts).
This is a polish-pass task; can be a dedicated name-audit workflow.

## CONFIRMED playtest priorities (2026-06-18, user) — the high-value wins now that spacing is solved
These are no longer "maybe" — they are confirmed visual problems to fix. The narrow/proportional
spacing reclaimed BOTH horizontal and vertical room; spend it:
1. **Dialogue + narration must USE the reclaimed HORIZONTAL space** — the wrap budget is still too
   conservative, so lines break early and waste width. We have the room now. Raise the wrap budget
   (Step 2a DIALOGUE_BOX_PX, Step 1b NARR_BOX_PX) after measuring the true box right-edge clip
   (Open decision #1). This is the "too-early wrap" item, now a confirmed priority.
2. **Narration ALIGNMENT is broken** ("fucked") — confirmed in-game, not just the known ~11-34px
   centering drift. The Stage-3 summed-width centering (replace PATCH 13 count*18 reserve with a
   SUM(ADV) reserve so origin = center - sum/2) is REQUIRED, not optional. Roadmap step 1a.
3. **Dialogue vertical overflow — TARGET = 3 lines per box.** Clarified by user: the dialogue box
   comfortably fits ~3 lines; 4 lines already spill OVER the box edge (still legible, but wrong).
   So the goal is NOT to cram more lines in — it is to wrap WIDER so dialogues need only 3 lines.
   PRIMARY lever: spend the reclaimed HORIZONTAL space (priority 1) — a higher px-wrap budget puts
   more chars per line → 3 lines instead of 4+. SECONDARY: dialogues that STILL exceed 3 lines after
   wider wrap need authored ' // ' page-splits (never auto 0xFFD2). Do NOT pursue a line-pitch
   tightening to fit 4-5 lines — box capacity is ~3 comfortable lines; aim for 3. (a) measure box
   vertical capacity to confirm 3-line target (Open decision #2, y~363..473); (b) tune
   DIALOGUE_BOX_PX so typical dialogue lands in 3 lines; (c) worklist the dialogues that still need
   ' // ' splits. Goal: no dialogue spills past the box edge; 3 lines is the design target.

