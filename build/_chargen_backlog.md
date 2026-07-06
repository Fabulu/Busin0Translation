# ⛔ SUPERSEDED / FALSIFIED — DO NOT FOLLOW THIS DOCUMENT (banner added 2026-07-05)

**This is an early copy of `data/chargen_spacing_backlog.md` and shares its fatal errors. Kept only as history.**

1. The `0x308040` Path-1 plan below became **Patch 19, which hooks a DEAD PATH** — v133 live diagnostics proved chargen text does not draw through it (see memory `project_chargen_drawpath_falsified`).
2. §1's "R2100-font theory DISPROVEN by disassembly" was itself wrong — **the R2100 theory was CORRECT**: chargen/request renderers (`0x307510`, `0x3A2EF0`) draw the R2100 sub0 upright 16px font. The real fix shipped in **v158** (commit 44e77d1): R2100-measured ADV2/LSH2 metric tables at VA `0x4B1000`/`0x4B1100` feeding Patches 26/27/29/31.

**Current truth:** `CLAUDE.md` + `runs/CLAUDE-RUNS/AUDIT-20260702-full-project.md` (finding H3). Original text below, unchanged, for history.

---

## Chargen + fixed-pitch text spacing fix (backlog, added 2026-06-18)

### 1. Problem + evidence

The character-creation (chargen) screens and several other dynamic-text boxes render with a **fixed ~24px monospace pen advance**, producing wide inter-letter gaps and oversized word-spaces. The narration/dialogue path already got the proportional fix (Patch 13/14 in `build/patch_exe.py`), but the chargen prompt/description boxes were **not** covered because they use a *different code path inside the same renderer function*.

**Key correction to prior project notes:** the memory/roadmap claim that "chargen renders through a DIFFERENT font system — R2100/R2138 atlases" is **DISPROVEN by disassembly**. The chargen prompt (R37 MSG) and description (R38 MSG) text draws from the **same R1188 24x24 serif atlas** (VRAM `TBP0=0x3000`) as narration, via a sibling sub-path (Path 1) of the same function `0x307DA0`. R2100/R2138 only supply pre-rendered stat/keyboard labels that *coexist* on-screen, which created the false impression. Update the incorrect note in `data/text_restructure_roadmap.md`.

**Evidence saves / screenshots (repro):**
- `ramdumps/space1.p2s` … `space6.p2s` (one per chargen phase) — and `ramdumps/spaces3.p2s`, `ramdumps/spaces4.p2s`.
- Screenshots: `build/_space1_shot.png` ("Enter your name."), `build/_space2_shot.png` / `ramdumps/_space2/Screenshot.png` ("Select gender." prompt + "Gender sets base stats…" description), `build/_space6_shot.png` (personality/confirm panel). All show wide centered 24px monospace; the R2138/R2100 sidebar + tab labels next to them render fine.
- Note: `.p2s` are final-VRAM-only. Stage 0 needs a live `.gs.zst` (Shift+F8) capture and/or `eeMemory.bin` single-step, NOT the `.p2s` alone.

### 2. Affected element catalog (grouped)

All affected elements flow through the R1188 glyph-advance path (func `0x307DA0` Path 1, advance `addiu v0,v0,0x18` @ `0x308040`). **One Path-1 fix covers all of them simultaneously.**

**TOP PROMPT BARS (R37 MSG glyph streams):**
- Name (space1): R37 MSG 2 "Enter your name." (has a known overflow/double-wrap bug)
- Gender (space2): R37 MSG 3 "Select gender."
- Race (space3): R37 MSG 4 "Select a race."
- Alignment (space4): R37 MSG 5 "Select alignment."
- Class (space5): R37 MSG 6 "Select a class."
- Stat-alloc (19-8): R37 MSG 7 "Allocate stat points."
- Confirm (space6 / 19-7): R37 MSG 124 "Press O or X to confirm." (wraps to 2 lines) + MSG 8 "Is this OK?", MSG 10 "yes", MSG 11 "no".

**BOTTOM DESCRIPTION / PERSONALITY BOXES (R38 MSG glyph streams):**
- Gender desc (space2): R38 ~145-166 "Gender sets base stats. Men=strong, women=wise."
- Race desc (space3): R38 ~145-166 "Human: High faith & balanced stats overall." (6 races)
- Alignment desc (space4): R38 ~145-166 "Good=justice. May turn Evil. …" (3 alignments)
- Class desc (space5): R38 ~167-218 "Combat expert. Cannot learn any magic spells."
- Personality (space6): R38 ~87-144 trait descriptions ("Must adventure. Hates sitting idle.") + trait NAMES (MSG 53-86: "Advent", "Moody"). Confirmed source: `data/translate_chunks/chunk_02_translated.json` `"resource":38`.

**MENU LIST ITEMS (R38 MSG, same wide pitch — short enough to "look acceptable" but on the same path; fix in same pass):**
- Race list: Human/Elf/Gnome/Dwarf/Hobbit/Automata (R38 MSG 29-34)
- Alignment list: Good/Neutral/Evil (R38 MSG 148-150)
- Class list: Fight/Mage/Priest/… (R38 MSG 37-52)
- Gender options: male/female (R38 MSG 25-26)

**SIDEBAR VALUES (R38 MSG, right summary box):** the *values* "Human"/"Good"/"Fight" are on the R38 wide-pitch path (affected). The *labels* "Sex/Race/Align/Class" are EXE menu-struct kanji tiles — separate Japanese-source issue, NOT this fix.

**NOT affected (different path — must NOT regress):**
- Stat numbers/digits (numeric sprite path), stat-abbrev labels Str/Int/Pie… (R2100/R2138 pre-rendered sprites, `5E/7E` source map).
- Decorative italic section headers (pre-rendered TEX, GS page `0x2254`).
- "New Character" red banner (EXE composite glyph IDs via R1272 tile pairs).
- Keyboard grid A-Z (R37 MSG 20 + EXE grid layout, cell-positioned).
- Tab labels Kana/Hira/ABC/Sym/OK (R1188 sprites via EXE Table 2E / R2138 sub7).
- None of these pass through `0x308040`, so the cave is structurally incapable of touching them.

### 3. Chargen renderer + advance VA(s)

**Universal dynamic-text renderer:** func `0x307DA0` (file `0x2080C0`, spans to `0x309870`). Invoked indirectly (no `jal` callers; reached via computed jump). Contains multiple sub-paths selected by `ctx+0x290 & (4|8)` and modifier byte `0x160(sp)`; centering gated by `ctx+0x2a8==1`. All four monospace `addiu v0,v0,0x18` sites (`0x308040`, `0x308CB0`, `0x308D7C`, `0x3097A4`) live inside it.

**Chargen = Path 1:**
- Grid loop `0x307FE0`–`0x308064` — a true **32×32 grid** (`slti s0,0x20` @ `0x308050`, `slti s2,0x20` @ `0x30805C`).
- **PRIMARY ADVANCE LEVER:** VA `0x308040` (file `0x2080C0`) `addiu v0,v0,0x18` — the fixed 24px pen step. Pen stored at `0x1cc(sp)` via `sh v0,0x1cc(sp)` @ `0x308044`.
- Glyph id re-readable at the advance site via `lh g,0x40(s1)` (s1 NOT yet bumped — `addiu s1,s1,0x2` happens at `0x308054`).
- **Draw primitive:** `0x305E30` (file `0x205EB0`), called via `jal` @ `0x308030`. Draw-X is computed *inside* `0x305E30`; penX is passed via `0x1cc(sp)` and combined at `0x308034` `addu t0,v1,v0` (v1 = penX). This is unlike narration's standalone `addu t4,a3,t4` @ `0x309750`.
- **Centering (count×12):** `0x307FB8`–`0x307FD4`, specifically `0x307FBC` (file `0x20803C`) + `0x307FC4` (file `0x208044`). These compute `count*12` and MUST change in lockstep with any advance change.

Path 1 uses pen `0x1cc(sp)`; narration/dialogue (Path 2/3, already fixed) uses pen `0x1ce(sp)` — so a Path-1 cave cannot disturb the shipped narration fix.

### 4. Implementation approach

**Metrics source — REUSE, do NOT measure or recompute.** The chargen prompt (R37) and description (R38) glyphs are the same R1188 atlas as narration with `gid == char-32`, so `data/r1188_ascii_metrics.json` + `tools/glyph_metrics.py` apply **unchanged**:
- `ADV[g] = 9 if g==0 (space) or ink_width==0, else clamp(ink_width+3, 6, 23)` (GAP=3)
- `LEFTSHIFT[g] = max(0, ink_left)`
- Import `glyph_metrics.adv_table_256()` / `leftshift_table_256()`. Recomputing metrics independently is the project's documented **#1 desync failure mode** — forbidden. No R2100/R2138 ink measurement is needed for this fix.

**One vs two hooks across the boxes:** **ONE shared Path-1 fix covers BOTH** the top prompt bar (R37) and the bottom description/personality box (R38) — they differ only in source resource and line extent, both render through Path 1 (advance `0x308040`, draw `0x305E30`, centering count×12). The menu-list items / tabs / sidebar labels / OK button do not pass through `0x308040` and must not be touched.

**Cave/hook plan** (mirror Patch 14's two-stage design; new VAs — do NOT reuse the narration hook sites):
- **Stage 1 — advance LUT.** Trampoline file `0x2080C0` (`addiu v0,v0,0x18`) → `j <cave>`. Cave: re-read gid via `lh g,0x40(s1)`; `lui base,0x4C; andi g,g,0xFF; addu base,base,g; lbu adv,ADV@off(base)`; `addu v0,v0,adv`; `sh v0,0x1cc(sp)`; `j 0x308048` (return past the replaced insn + its store — verify exact return PC against the live delay slot). Tables from `adv_table_256()`.
- **Stage 2 — draw-shift (LEFTSHIFT).** Path-1 draw-X is inside the shared primitive `0x305E30`. **Prefer Option A:** subtract `LEFTSHIFT[g]` from penX in `0x1cc(sp)` immediately *before* `jal 0x305E30` @ `0x308030` (touches draw-X only, leaves the advance pen intact). **Avoid Option B** (hooking inside `0x305E30`) — it is a shared primitive and could shift non-chargen text. Tables from `leftshift_table_256()`.
- **Stage 3 — centering lockstep (CRITICAL, ship with Stage 1).** Replace `count*12` at `0x307FBC`/`0x307FC4` with the true summed width `Σ ADV[g]` over the line, or cave the centering site to accumulate it. Shipping Stage 1 without Stage 3 reproduces the narration centering-drift bug (−24…−58px, see `build/recon_v86/draw-baseline/FINDINGS.txt`). Minimal interim: leave `count*12` (small residual drift, still far better than 24px monospace) — acceptable only as a temporary ship.

**Cave region:** re-verify a clean rodata pad near the interpreter handler table `0x4C9360` (Patch 14 uses `0x4C75C0+` in-file; tables at `0x4C7564`/`0x4C7690`). The "30 scenes clean" check may NOT have included a chargen scene — re-verify untouched for chargen specifically. The existing `0x4C7564` (ADV) and `0x4C7690` (LEFTSHIFT) tables are byte-identical data and may be reused by the chargen trampolines if reachable; only new code trampolines are then needed.

**Space fix:** no separate hook. `ADV[gid 0] = 9` vs the old 24px cell narrows word-spaces by ~15px automatically via the Stage-1 LUT. Validation only: confirm R37/R38 encode word breaks as glyph id 0 (real space), not zero-width pad cells (screenshots show genuine gaps, so id-0 spaces are expected).

**Wrap/layout (Stage 4):** once advance shrinks, re-flow the R37/R38 box wrap budget (currently authored for 24px monospace), curing the R37 MSG-2 name-prompt overflow. Build-side; add a px-width test gate. The name-entry keyboard/typed-name uses the R2100 16×16 monospace atlas (System C) — SEPARATE backlog, out of scope here.

**All fixes are EXE caves (real-PS2 compatible).** No atlas re-render, no PCSX2 texture replacement.

### 5. Broader render-system families that share the issue

All dynamic glyph-stream text flows through func `0x307DA0` and draws from R1188. Classify each text element by the **dynamic-vs-fixed test**: dynamic (varies with party data / message index / input) → glyph-advance, candidate for this fix; fixed label/button caption → pre-rendered strip, belongs to the separate pixel-strip track.

- **Family A — glyph-advance (this fix applies):**
  - A1 narration/dialogue (Path 2/3, pen `0x1ce`, draw prim `0x3060B0`) — **DONE** (Patch 13/14: advance cave `0x4C7540`/table `0x4C7564` hooking `0x3097A0`; draw-shift cave `0x4C7670`/table `0x4C7690` hooking `0x309750`).
  - A2 chargen prompts (R37) — **UNFIXED**, Path 1.
  - A3 chargen descriptions/personality (R38) — **UNFIXED**, Path 1. One Path-1 cave fixes A2+A3.
- **Family B — other glyph-advance consumers (audit per-screen before fixing):** item/spell descriptions, shop prompts ("Buy/Sell which item?"), confirmation yes/no lines, tavern/inn dialog, quest-board post bodies, level-up/stat-gain results, battle action prompts. Discriminator is `ctx+0x290` bits + `ctx+0x2a8` — measure on live saves, don't guess. Path-1 members need the chargen cave; Path-2/3 members are already fixed.
- **Family C — pre-rendered pixel strips (DIFFERENT system, NOT this fix):** town/facility buttons R2124/R2136/R2147; tavern submenu (R2147 sub0); status/bottom bar R1365; battle menus R1053/R1054; chargen sidebar/tabs R2138 type-29 (`patch_r2138.py`, Step 3.9) + R2100 PSMT4 (`patch_r2100.py`, Step 3.8); banners/headers R1272/TEX. In-place pixel re-render track — separate backlog.
- **Family D — language-neutral/intentional (no fix):** kana input grids (R37 MSG 18/19 + EXE `0x3C83C0`), name-display dashes, ornamental frames, dungeon compass glyphs.

### 6. Risks + open questions

- **HIGH — centering desync (integer cell grid).** Path 1 is a 32×32 grid reserving a fixed 12px/cell. Proportional advance without matching centering drifts every line (the exact narration bug, `FINDINGS.txt`). **Stage 1 and Stage 3 MUST ship together** — never ship the advance cave alone.
- **HIGH — integer per-cell cursor.** Cell iteration is index-based (`s0/s2` counters, `s1+=2`/glyph). Keep ADV integer (glyph_metrics already clamps 6..23) and verify `sh v0,0x1cc(sp)` @ `0x308044` truncates cleanly; a free-pixel pen is required, not a re-quantized cell index (cf. `project_v93` integer-cell constraint).
- **MEDIUM — wrong glyph-id register.** Path-1 selection and the gid register at `0x308040` are **inferred from the screenshot signature** (centered 24px monospace = count×12 + `addiu 0x18`), NOT single-stepped — the R37/R38 `msg_glyph_map` IDs (not char-32) prevented locating the group struct in eeMemory statically. The cave's `addu base,<reg>` must use the confirmed live register.
- **MEDIUM — shared draw primitive `0x305E30`.** Used by other paths; do Stage 2 via Option A (penX in `0x1cc(sp)`), not by hooking inside `0x305E30`.
- **MEDIUM — Family C regression.** Add a screenshot gate proving the stat sidebar + tab labels (R2138/R2100) are byte-identical after the patch.
- **LOW — LEFTSHIFT underflow.** Clamp so penX can't go negative on the first glyph of a centered line.
- **LOW — cave-region cleanliness.** Re-verify the `0x4C9360` pad is untouched across a *chargen* scene specifically.
- **Open question (overlap warning):** `0x303C60`/`0x305980`/`0x308DFC` were named by the 2026-05-28 recon as chargen layout funcs AND by the v97 narration recon as narration-centering funcs. Stage 0 must disambiguate which funcs the LIVE chargen draw uses before patching, or a chargen change could regress narration.

### 7. Ordered checklist (executable later)

- [ ] **0. Live confirm (GATE — do before cutting any cave).** Load `ramdumps/space2.p2s` (eeMemory: VA==offset) and capture a `.gs.zst` (Shift+F8) of the same frame.
  - [ ] (a) Single-step / trace-break func `0x307DA0`; confirm **Path 1** draws BOTH the R37 prompt ("Select gender.") and the R38 description ("Gender sets base stats…").
  - [ ] (b) Confirm advance site is `0x308040` `addiu v0,v0,0x18` and gid is live & re-readable via `lh g,0x40(s1)`; record the EXACT register holding gid.
  - [ ] (c) Read `ctx+0x290` (bits 4|8 @ `0x307E2C`) and `ctx+0x2a8` (centering enable) — confirm both boxes take Path 1 with centering on. Locate the group struct via the renderer's ctx pointer (string search fails — msg_glyph_map IDs ≠ char-32).
  - [ ] (d) GS-dump: confirm sampled atlas is R1188 `TBP0=0x3000` (24×24 serif), gid==char-32 — rule out R2100/R2138.
  - [ ] If any of (a)–(d) fails: STOP, re-recon, do not patch.
- [ ] **1. Metrics — reuse only.** Import `glyph_metrics.adv_table_256()` / `leftshift_table_256()` from `tools/glyph_metrics.py` (data `data/r1188_ascii_metrics.json`). No new measurement, no recompute.
- [ ] **2. Stage-1 advance cave** in `build/patch_exe.py`: re-verify a clean cave region near `0x4C9360`; trampoline `0x2080C0` → cave; index ADV LUT by gid; `addu v0,v0,ADV[g]`; store `0x1cc(sp)`; return past the replaced insn.
- [ ] **3. Stage-3 centering lockstep** (ship with step 2): replace `count*12` @ `0x307FBC`/`0x307FC4` with `Σ ADV[g]` summed width (or interim: leave count×12, accept small drift).
- [ ] **4. Stage-2 draw-shift (Option A):** subtract `LEFTSHIFT[g]` from penX in `0x1cc(sp)` immediately before `jal 0x305E30` @ `0x308030`. Clamp ≥0.
- [ ] **5. Validate spaces:** confirm word breaks encode as glyph id 0 in R37/R38 streams (ADV[0]=9 then auto-narrows).
- [ ] **6. Wrap/layout pass (Stage 4):** re-flow R37/R38 box wrap budget for proportional width; cure R37 MSG-2 name-prompt overflow; add px-width test gate.
- [ ] **7. Build + verify.** Canonical one-command pipeline; `python verify_iso.py build/BUSIN0_EN_vNN.iso`; **FRESH boot** (no save states) to all 8 chargen screens.
- [ ] **8. Regression gate.** Assert chargen cave imports `glyph_metrics` (no recomputed tables) and the `0x308040` hook word + table bytes match `adv_table_256()`. Screenshot-gate that the R2138/R2100 sidebar + tab labels are byte-identical (no Family C regression).
- [ ] **9. Update `data/text_restructure_roadmap.md`:** correct the "chargen uses R2100/R2138 different font system" note — chargen dynamic text is R1188 glyph-advance via func `0x307DA0` Path 1.

**Relevant files/VAs/saves:** `extracted/SLPM_653.78` (func `0x307DA0` @ file `0x2080C0`); `build/patch_exe.py` (Patch 13/14 template; add Path-1 caves); `tools/glyph_metrics.py`; `data/r1188_ascii_metrics.json`; `build/_chargen_dis.py` (disassembler, VA_BASE=0xFFF80); `build/recon_v86/draw-baseline/FINDINGS.txt`; `runs/CLAUDE-RUNS/RUN-20260528-remaining-japanese/chargen_source_map.md`; saves `ramdumps/space1-6.p2s`, `ramdumps/spaces3.p2s`, `ramdumps/spaces4.p2s`; shots `build/_space1_shot.png`…`_space6_shot.png`, `ramdumps/_space2/Screenshot.png`.