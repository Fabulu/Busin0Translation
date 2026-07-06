# ⛔ SUPERSEDED / FALSIFIED — DO NOT FOLLOW THIS DOCUMENT (banner added 2026-07-05)

**The central premise of this handoff — that the chargen "Ge nde r" spacing is an UNSOLVED defect rooted in the R1188 24px atlas — is WRONG. It was SOLVED in v158 by identifying the WRONG-FONT root cause. This doc was written at v157, one build before the fix.**

1. **§0 / §1 (the "UNSOLVED per-letter spacing defect") — FALSIFIED.** The renderers were drawing the **R2100 sub0 upright 16px font, NOT the R1188 24px oblique atlas.** So the entire §1 root-mechanism analysis (R1188 atlas centering error + inaccurate `data/r1188_ascii_metrics.json`) was measuring the wrong font's metrics. Fixed in **v158** (commit `44e77d1`): new R2100-derived `ADV2`/`LSH2` metric tables at VA `0x4B1000`/`0x4B1100` (`tools/glyph_metrics.py` `ADV2`/`LEFTSHIFT2`, GAP2=2, space=6, clamp 4..15), fed to Patches 26/27/29/31. The spacing is fixed; do not re-chase it as "unsolved."
2. **§2 patch-stack table — OBSOLETE (v157-era).** The live stack is Patches **26/27/29/31** reading the **R2100 `0x4B1000`/`0x4B1100`** tables, not the R1188 `0x4C7564`/`0x4C7690` tables shown here. The one row still true: **Patch 19 hooks a DEAD/inert path** (v133 live diag: fire-counter 0 while chargen mode==5 — see memory `project_chargen_drawpath_falsified`); it is retired/retargeted (audit M5).
3. **§3 renderer map — accurate on the FUNCTIONS (`0x3A2EF0`, `0x307510`, `0x309750` are the real renderers) but WRONG on the font: they sample the R2100 16px font for chargen/request, not R1188.** R1188 is narration/dialogue only, and **R1188 ships PRISTINE** (its own metrics were accurate all along — the problem was never R1188).
4. **§5 "two fix directions" (re-measure R1188 metrics / left-align the R1188 atlas) — BOTH FALSIFIED.** Both operate on the wrong font. Re-measuring R1188 would not have touched the R2100-drawn chargen text; left-aligning the R1188 atlas would have broken narration/dialogue and violated the BUG-3 pristine rule for nothing. The actual fix measured the **R2100** font (`data/r2100_ascii_metrics.json`).
5. **§8 "recommended first steps" — OBSOLETE** (they chase the falsified R1188 metric/atlas theory).

**Still historically useful (NOT falsified):** §0's *block-position vs spacing* distinction is real, and the **block-position axis is a separate, SOLVED problem** (Patch 28 name-column X, Patch 30 sidebar-value X). §6's ruled-out block-position levers remain valid history. The "Patch 19 is a dead path" note is correct.

**Current truth:** `CLAUDE.md` + `runs/CLAUDE-RUNS/AUDIT-20260702-full-project.md` (finding H3, which names §1/§2/§5/§8 obsolete) + memory `project_chargen_font_r2100_rootcause.md`.

---

# HANDOFF — Busin 0 Text Alignment (chargen + global)

**For a new, stronger model.** This supersedes the earlier handoff. It captures the full text-rendering patch stack (through build **v157**), the one **unsolved** defect, and everything already ruled out. Read this and start without repeating any dead end.

`VA↔file: file = VA − 0xFFF80`. RAM dumps: index `ee[VA]` **directly** (RAM==VA). Screen-mode global `0x4FED18`: **5=chargen, 7=town/request, 8=battle**. Target disc: **SLPM-65378**.

---

## 0. TWO SEPARATE THINGS — do not conflate (the core insight)

| | **Text BLOCK position** | **Per-letter SPACING** |
|---|---|---|
| What | where a whole text block/column *starts* on screen | the gaps *between individual letters* within a block |
| Lever | per-screen X immediates (Patch 28, Patch 30, class list) | the shared proportional **metric tables** (ADV/LSH) + the **atlas** |
| Status | **SOLVED** (levers found & traced) | **UNSOLVED** — this is the real remaining defect |

**Patch 28 was *supposed* to move the whole race/align name blocks left (overflow fix) — NOT fix spacing.** It does that correctly; it just **overshot at `-260`** (v157: `Waytoofarright.png` shows the block shoved to the far-left edge). The uneven letters *inside* the block are the separate spacing defect and no block-position lever touches them.

---

## 1. THE UNSOLVED DEFECT — per-letter uneven spacing, game-wide

**Symptom** (`selectgender.png`, v157): "Ge nde r", "se ts", "Me n=strong", "wome n=wise" — inconsistent gaps between letters, on **every** renderer including the top black header banner ("Se le ct ge nde r."). Letters appear "centered differently depending on the letter."

**Root mechanism (proven from tooling, not yet fully fixed):**
1. `tools/generate_font_atlas.py` renders each glyph **centered inside its 12×12 cell** (`ox = x + (CELL_W-cw)//2 - bbox[0]`). So each glyph's **`ink_left` (left bearing) varies** — narrow letters sit farther right in their cell, wide letters fill it.
2. The renderer draws a **fixed 12-texel (24 screen-px) quad** per glyph slot — there is *no* per-glyph width in the draw call itself (`halfwidth_font_analysis.md`, `analysis_text_renderer.md`). Proportional spacing is achieved **only** by the injected metric tables:
   - `tools/glyph_metrics.py`: `ADV[g] = clamp(ink_width+3, 6, 23)` (space=9); `LEFTSHIFT[g] = max(0, ink_left)`.
   - Source: `data/r1188_ascii_metrics.json` (95 glyphs, measured from **live R1188 VRAM**, TBP0=0x3000).
   - Baked into the **SHARED** in-EXE tables **ADV @ `0x4C7564`** and **LSH @ `0x4C7690`**.
3. Correct math: pen advances `ADV[g]`; draw-X subtracts `LSH[g]` so each glyph's ink starts exactly at the pen → **uniform 3px gaps**. This is right **iff the metrics are accurate.**

**So the unevenness = the metrics are inaccurate and/or the compensation isn't applied on that renderer.** Two contributing causes, both live:
- **(a) Metric inaccuracy.** The VRAM measurement has serif/bleed error. Confirmed outlier: `'f'` (gid 70) = `ink_left 12 / ink_width 12` (the largest in the table) but renders ~6–7px wide → over-advances and over-shifts, leaving a fat trailing gap after every `f` ("Mad if⎵loot", "High f aith"). Likely more glyphs are off.
- **(b) Coverage gaps.** The ADV/LSH compensation is applied on **only some renderers** (see §3), all **mode-gated to chargen/request**. Screens on the stock renderer (headers, menus, most of the game) get no compensation → the atlas centering shows through raw.

**The user believes this "was fixed before and the fix probably killed the battle."** That is consistent with a global (ungated) proportional/atlas change: the metric tables are shared, so making all text proportional — or regenerating the atlas — shifts **battle** command/menu text and trips the battle regression. See §4.

---

## 2. Current patch stack (build/patch_exe.py) — the text-rendering patches

| Patch | Renderer / site | Does | Gate |
|---|---|---|---|
| **14** | narration `0x309750` path | ADV + LSH caves (proportional narration) | narration |
| **19** | `0x308018` | LSH cave — **hooks a DEAD/inert path** (does nothing; see `project_chargen_drawpath_falsified`) | — |
| **26** | chargen body `0x307510` (hook `0x3079CC`) | ADV (proportional desc text) | `==5` |
| **27** | `0x3A2EF0` (hook `0x3A31A0`) | ADV on the Status/request box renderer | `∈{5,7}` |
| **28** | race/align **name column X** — 3 sites `0x149788`/`0x1498A0`/`0x149E5C` | block-move left `-216 → -260` (**overshoot**, tune back) | chargen-only immediates |
| **29** | `0x3A2EF0` (hooks `0x3A30F4`/`0x3A3170`) | LSH draw-shift (companion to P27) | `∈{5,7}` |
| **30** | sidebar **value column X** `0x14C0A0` (file `0x4C120`) | block-move left `72 → 44` (fixes Sex/Race/Align/Class overflow, all screens) | chargen-only |
| **31** | chargen desc `0x307510` (hook `0x307974` → cave `0x4AFA00`+`0x4AB5EC`) | LSH draw-shift (companion to P26) | `==5` |

Builds: **v157** = latest (P28 `-260`, P30, P31). **v156** = P28 `-241` + P29. **v152** = last build before the spacing patches.

---

## 3. Which renderer draws what (measured)

- **`0x3A2EF0`** (+ wrapper `0x3A3260`): Status box + request body. ADV (P27) + LSH (P29). ~250 callers incl. **battle (mode 8)** — that's why everything here is mode-gated. `glyphX = baseX(sp+0xE0) + pen(s1)`; draw-X sites `0x3A30F4`/`0x3A3170`.
- **`0x307510`** (line-walk `0x307DA0` → emit `0x3060B0`): chargen race/align **description** boxes. ADV (P26) + LSH (P31). Single draw-X site `0x307974`.
- **`0x309750`**: narration (P14).
- **List renderers**: race/align names via `0x142410`'s 3 handlers (`0x149710`/`0x149820`/`0x149DE0`), each with base-X `t2=-216`→`-260` (P28). Class names via a *different* drawer `0x1435c0` (2 callers, base-X `-184` at `0x14A190`/`0x14A530`).
- **Sidebar values** (Sex/Race/Align/Class): one function `0x142A60` (chargen-only), base-X `72` at `0x14C0A0` (P30). The `-104` at `0x14C070` is the sidebar **Y** (do NOT touch).
- **Header banner / most menus / battle**: **stock** renderer, no ADV/LSH → uneven where the atlas centering shows.

---

## 4. Battle-safety — why a global fix is dangerous

- ADV/LSH tables `0x4C7564`/`0x4C7690` are **shared** by narration, dialogue, menus, **battle**. Any edit to `data/r1188_ascii_metrics.json` or `tools/glyph_metrics.py` changes **every text screen** and can trip: the empty-arena battle crash, narration reflow (baked left-align + Patch 24), dialogue auto-pagination (fixed wrap widths — `test_no_auto_pagebreak.py`).
- Caves: VA **< `0x4B0DCF`**, `assert_install_safe`; never the heap arena `≥0x4B0E00` (empty-arena crash) or libgraph `0x4AF2E0–0x4AF400` (title hang). **R1188 atlas must ship pristine** (BUG-3 — patching it corrupts live glyph cells).
- **Ship gate: fresh-boot A/B (never stale save-states) + one live battle confirming monsters render + battle text intact.**

---

## 5. The two fix directions for the spacing (§1) — with trade-offs

1. **Metric re-measure (surgical, recommended first).** Re-measure `data/r1188_ascii_metrics.json` `ink_left`/`ink_width` accurately from live R1188 VRAM (TBP0=0x3000, isolate each 24px cell, exclude serif bleed). Start with the known outlier `f` (gid70) and spot-check `e`(69), `F`, caps `M/N/H/W`. `glyph_metrics.py` re-derives ADV/LSH; the caves rebake. **Fixes uniformly *where the tables are applied*.** Risk: shared tables → full battle/dialogue/narration regression pass mandatory. Also raise the ADV clamp (`min(iw+3,23)`) if wide caps lose their gap.
2. **Atlas left-align (structural, riskier).** Regenerate the atlas with ASCII glyphs **left-aligned** (`ink_left≈0`) instead of centered → LSH becomes unnecessary and metric error mostly vanishes. BUT this changes the **live R1188 atlas** (BUG-3 pristine rule) and every text screen; **this is the most likely candidate for the prior "fix that killed the battle."**

**Coverage decision (orthogonal):** even with correct metrics, screens on the stock renderer stay uneven unless you extend the ADV/LSH hook to them — which pushes toward the shared/global change and the battle risk. Decide per-screen mode-gating vs a verified-safe global proportional pass.

---

## 6. Already ruled out — do NOT re-chase (race-overflow lever hunt, ~6 falsified)

| VA | what it is |
|---|---|
| `0x4D0270` / `0x3D02F0` | off-screen marker coord table (dead) |
| `0x14C070` / `0x4C0F0` | sidebar **Y** (moves banners vertically) |
| `0x14C090` (`t0=17`) | wrong param |
| `0x1498A8` (`-104`) | race-list **Y** (v154 moved the box *up*) |

**Levers that ARE correct (traced byte-for-byte + RAM-verified):** race/align name-block X = the three `t2=-216` sites (P28); sidebar value X = `72@0x14C0A0` (P30); class name X = `-184` at `0x14A190`/`0x14A530` (class list, not yet built — needs a class-screen capture to confirm it clips).

**The reliable method that cracked all of these:** memory-**READ** BP on the live glyph stream (Human@`0x00E144D4`, Good@`0x00E153AA`, Fight@`0x00E14534`) → "run until return" walk-up → find the renderer + trace baseX@`sp+0xE0` back to the originating immediate. Do NOT trust "t1=X" (it's often a color `0xE9FE`); prove X-not-Y (the `-104` traps).

---

## 7. Toolkit

- Build: `python tools/generate_font_atlas.py && python build/build_v9.py && cp build/BUSIN0_EN_v9.iso build/BUSIN0_EN_vNN.iso`
- Verify: `python verify_iso.py build/BUSIN0_EN_vNN.iso` · `python tests/run_all.py` (the 2 R38 `[672]/[673]` gender-symbol FAILs are pre-existing by-design)
- Metrics: `tools/glyph_metrics.py`, `data/r1188_ascii_metrics.json`; atlas: `tools/generate_font_atlas.py`
- Patcher: `build/patch_exe.py` (Patches 14/19/26/27/28/29/30/31); cave map: `build/_reloc_v147_design.py`
- v157 screenshots: `runs/CLAUDE-RUNS/RUN-20260630-polish-chargen/debug/v157/{selectgender,Waytoofarrightandstillnotfixed,betta,goodnewt,betterspacing}.png`
- RAM dumps (`ee[VA]` direct): `ramdumps/*.p2s` (extract `eeMemory.bin`/`Screenshot.png` via 7-Zip; sort by mtime, use newest)
- Repro scripts: `subagents/20260701-1947-race-name-lever/`
- Prior-work pointers: `runs/CLAUDE-RUNS/RUN-20260528-remaining-japanese/{halfwidth_font_analysis.md,analysis_text_renderer.md,debug_font_atlas_positions.md,fix_race_overflow.md}`; `runs/.../RUN-20260522-1932-initial-recon/subagents/{diag-atlas-pixels,recon-font-atlas,recon40-grid-align}/FINDINGS.md`
- Key VAs: renderers `0x3A2EF0`/`0x307510`/`0x309750`; ADV `0x4C7564`, LSH `0x4C7690`; race glyph data `0x00E144D4`; baseX `sp+0xE0`; mode `0x4FED18`; safe-cave ceiling `0x4B0DCF`.

## 8. Recommended first steps
1. **Settle the spacing root cause live:** memory-READ BP on `0x00E144D4` during a desc draw; measure actual per-glyph pen advances vs `r1188_ascii_metrics.json`. Confirms metric-inaccuracy (§5.1) vs atlas-centering (§5.2) as the dominant cause.
2. **Pick a direction** (metric re-measure first; atlas left-align only with a full battle regression plan).
3. **Tune Patch 28 back** from the `-260` overshoot (measure off `Waytoofarright.png`; likely ~`-245`).
4. Build → `verify_iso` + `run_all` + **a live battle** → fresh-boot A/B every affected screen.
