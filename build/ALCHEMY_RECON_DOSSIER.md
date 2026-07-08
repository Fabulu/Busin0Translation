# ALCHEMY MENU DOSSIER — prior knowledge recon (2026-07-08)

## 1. Known alchemy-menu issues

### OPEN
**A. Item-name "pill" too small / name spills out** (treasure drops, alchemy shop, town-return potion)
- Evidence: ramdumps/_townreturnpotion_shot.png (2026-07-08 extract) — "Town Return Potion" overflows the pill caps. Save chain: pilltoosmall.p2s, alignpill.p2s (Jul 6 22:42), fitsbutisitenough.p2s (Jul 6 22:16), Treasurepill.p2s, alchemypill.p2s (Jul 6 21:27), pillshop.p2s.
- CLAUDE.md "Remaining": "treasure-drop name placement".
- Prior fix WITHDRAWN: the 0x13F688 "pill width" patch was actually the chargen banner middle TILE ID -> caused the v175-v178 white-banner regression. See build/BANNER_PROBLEM_HANDOFF.md (SOLVED section) and build/PILL_INVESTIGATION_DOSSIER.md. Do NOT touch 0x13F688.

**B. Alchemy-shop name/quantity overlap**
- Evidence: GitHub issue #10 second comment ("Same class as the alchemy-shop name/quantity overlap. Queued for a capture session."). Sibling of in-battle Item-menu "EHealing Staff" spacing overflow (#10, OPEN).
- Prior analysis: driven by runtime layout structs, not a static patchable immediate — flagged as needing a live EE-debugger pass (Patch-28 precedent: 4-5 static guesses falsified on this bug class).
- No standalone write-up exists; primary evidence is Alchemyshop.p2s (Jul 6 19:46) / pillshop.p2s themselves.

### FIXED (do not re-fix; verify only)
**C. sub9 spell-book descriptions ran off the bottom of the WIDE synthesis/alchemy box** — fixed v173 via SUB9_WRAP_CELLS=36 in build/inject_r34_db.py:135-141 (narrow inventory box = 18 cells). Render-verification "by eye" never formally done.
**D. Item descriptions as one flat off-screen line** — fixed via width-based word-wrap for R34 DESC subs {1,3,5,7,11,13} (box renderer VA 0x3A2EF0 honors 0xFFFE breaks, no auto-wrap, no h-clip).
**E. "Handles alchemy" Bishop class-desc overflow** — fixed v17-v23 era.

### FALSIFIED / noise (do not re-chase)
- "編隊 instead of 合成 in alchemy context" — early cross-resource glyph-map artifact (Glyph-Page Law).
- v86 deferred "confirm alchemy/automata/spell-select interior labels" — superseded by R2138 sub26 strips, patched in current builds.

## 2. Resource map
| Resource | Role |
|---|---|
| R44 (type-01) | Alchemy Guild interface text — Automata mgmt, knight-order formation, chip creation, stat customization, synthesis prompts (58 msgs). Translations: chunk_05 (57 entries) + translations_menus.json key resource_44_knight_order. JP decode: _r44_decode.txt |
| R45 (type-01) | Vigger Shop (item shop), NOT alchemy — 197 msgs |
| R2138 sub26 "shop_alchemy" | Pre-rendered alchemy-guild menu labels (19: Go Outside/Magic Stones/Synthesize/Disassemble/Automaton/Buy/Enhance/Customize/Brain-Body-Hand-Arm-Leg Chip/Shop/Sell/"Alchemy Guild"/Buy Automaton/Enhance Auto.) via tools/patch_r2138.py Step 3.9. Preview: build/r2138_sub26_shop_alchemy_preview.png. Gate: tests/test_r2138_containment.py |
| R1359 (type-02 camp strip) | Main menu rects incl. 6 "Alchemy", 7 "Automata", 8 "Stone Fusion", 13 "Materials" via tools/patch_camp_strips.py + data/strip_labels/camp_labels.json. WARNING: game-wide MAIN/FACILITY menu — careless patch corrupts every menu |
| R2124 | Town hub "Alchemy Guild" label (L2_alchguild, 94px @13px in 128px rect) |
| R34 (item DB) | Names + descriptions for alchemy/synthesis screens; sub9 bodies render in WIDE synthesis box; sub11 = material lore blurbs |
| R1196/R1197, R1208 | Alchemist/guild story dialogue (R1208 g720 via tools/fix_b06_r1208.py, batch_06; batches 01/02/03) |
| EXE 0x13F5xx + jal 0x14DF30 | 3-part stretchable box widget family (see PILL_INVESTIGATION_DOSSIER.md for full draw architecture) |

## 3. Prior attempts timeline
1. 2026-05-22 initial decode: R44/R45 identified; R44 matched to guide ALCHEMY/AUTOMATA sections ~90% conf.
2. v86: R2138 sub26 re-inked English (containment + roundtrip gates, passing).
3. R34 DB injection: 18-cell wrap; then sub9 36-cell budget after alchemypill.p2s (v173).
4. v174-era blind pill patch 0x13F688 185->440 — FALSIFIED, withdrawn v179 (banner regression).
5. Shop overlap: analyzed as runtime-layout; deliberately not statically patched; queued for live capture.

## 4. Evidence assets (newest first)
- ramdumps/_townreturnpotion_shot.png (Jul 8 extract) — pill overflow, freshest
- ramdumps/pilltoosmall.p2s, alignpill.p2s (Jul 6 22:42)
- ramdumps/fitsbutisitenough.p2s, pillshop.p2s (Jul 6 22:16)
- ramdumps/alchemypill.p2s, Treasurepill.p2s (Jul 6 21:27)
- ramdumps/Alchemyshop.p2s (Jul 6 19:46) — likely the name/quantity-overlap evidence
- ramdumps/townreturnpotion.p2s (Jul 6 18:36); ramdumps/townreturnpotion_ee.bin already extracted (VA==index)
- CAVEAT: Jul-5/6 saves predate v174-v179 EXE builds — fine for LAYOUT recon, but EE-RAM EXE bytes are pre-Option-E; verify a known patched byte before trusting for EXE-state debugging.

## 5. Gaps for follow-up — v180 status (2026-07-08 evening)
1. ~~No written spec of the shop name/quantity overlap~~ **DONE** — build/ALCHEMY_SHOP_OVERLAP_SPEC.md (fixed right-anchored quantity column ending x≈252 over variable-width name from x≈50; 13 chars fit; runtime layout, live-debugger breakpoint plan included; no strings for quantities — composed at draw time).
2. ~~Pill disc source~~ **FOUND + option-1 fix BUILT (v180)** — see the v180 UPDATE atop build/PILL_INVESTIGATION_DOSSIER.md. Shop pill = R2138 sub27 art + R2139 sub13 rec2 {0,136,192,64,3}; widened to 256 + band re-inked (tools/patch_pill_widen.py, gated). Boot of build/BUSIN0_EN_v180_pill.iso decides natural-vs-explicit width. Treasure-scene pill = same art from an R1364-family copy, geometry still unlocated (wants a GS draw-dump at a chest). The old "seven 188x24 records" and the 0x170E98 site are FALSIFIED (misaligned parses / shop dialog box).
3. sub9 36-cell wrap: static PASS on built R34 (all lines ≤36 cells, max=36); pillshop.p2s render-proves the FFFE-wrap mechanism + 4-line vertical fit at an intermediate ~30-cell budget; exact-36 on-screen render still capture-gated (one synthesis-screen screenshot).
4. ~~R44 completeness~~ **CLOSED** — the 58th message is M0, a 4-byte dummy (glyph 0x0000 + FFFE, renders as a blank line). Nothing to translate; Step 6.1 guard correct not to flag it.
5. "Stone Fusion" sub-screen strips never explicitly captured/confirmed. (Still open, capture-gated.)
