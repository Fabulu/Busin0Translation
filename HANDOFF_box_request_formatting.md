# ⛔ SUPERSEDED / FALSIFIED — DO NOT FOLLOW §1/§4/§5 (banner added 2026-07-05)

**The chargen spacing root cause and fix direction in this doc are WRONG. The chargen renderers do NOT draw the R1188 font — they draw the R2100 sub0 upright 16px font. The spacing shipped FIXED in v158.**

1. **§1 "Universal R1188 glyph renderer … SHARED across chargen, narration, boxed dialogue, request" — FALSIFIED FOR CHARGEN/REQUEST.** R1188 is the narration/dialogue font only. Chargen prompts/descriptions and the request body draw the **R2100 sub0 upright 16px font** via `0x307510` (chargen body) and `0x3A2EF0` (Status/request box). This wrong-font identity is the root cause the whole doc missed.
2. **§4 ISSUE A (chargen wide spacing) — SHIPPED FIXED in v158** (commit `44e77d1`). One part of §4 was *correct*: **Patch 19 writes the dead `sp+0x1cc` pen and is inert** (re-confirmed by v133 live diag — fire-counter 0 while mode==5). But the proposed FIX (retarget Patch 19 to the `s7` stride, indexing the **R1188** `0x4C7564` ADV table) is FALSIFIED — it uses the wrong font's metrics. The real fix: R2100-derived `ADV2`/`LSH2` tables at VA `0x4B1000`/`0x4B1100` (`tools/glyph_metrics.py`, GAP2=2, space=6, clamp 4..15) feeding **Patches 26/27/29/31**, gated to chargen (mode==5) / request (mode==7).
3. **§5 ISSUE B (request overflow/collision) — the SPACING half shipped FIXED in v158** (Patch 27/29 make the request body proportional via the R2100 tables, mode-7 gated). The editorial half (rewriting ~60 quest descriptions shorter, `data/r39_quest_text_aligned.json`) is a separate content task; treat the "make the 18px-mono body proportional by hooking Patch-14/R1188" recipe as obsolete — that landed via the R2100 caves, not R1188.
4. **§2 (box-mode classifier DONE) and §3 (narration left-align DONE) remain ACCURATE** — those are R1188/narration work and were never falsified.

**Current truth:** `CLAUDE.md` + `runs/CLAUDE-RUNS/AUDIT-20260702-full-project.md` (finding H3, which names §1/§4/§5 superseded) + memory `project_chargen_font_r2100_rootcause.md`.

---

# Handoff — Box/Chargen Spacing & Request-Description Formatting

Written 2026-06-23, after the **Talking Ox** milestone (v130). Narration and the
dialogue/narration box-mode classifier are **DONE**. Two formatting issues remain,
captured in `ramdumps/boxes.p2s` and `ramdumps/requestissue.p2s`. **Read this whole
file before touching anything** — the renderer is one giant shared function and
"this draw path is X-only" assumptions have bitten us repeatedly.

---

## 0. Build / test / verify (do this exactly)

```bash
# Build (regenerates atlas + all type-02 + patches EXE + builds ISO) and copy in ONE step:
python tools/generate_font_atlas.py && python build/build_v9.py && cp build/BUSIN0_EN_v9.iso build/BUSIN0_EN_vNN.iso
# Tests (must be green before shipping):
python tests/run_all.py        # expect ~196 passed, verify_iso 7/2 (the 2 are intentional gender glyphs)
```
- EXE file offset convention: `file_off = VA - 0x100000 + 0x80`. (Easy to miscompute — I shipped two off-by-`0x80`/`0x100` bugs. Always verify with a `struct.unpack_from` read against a known instruction.)
- The build embeds the patched EXE into the ISO; the embed LBA varies per build. To verify a patch landed in the ISO, find the EXE base by searching for a 64-byte chunk of `build/SLPM_653.78_patched`, not a hardcoded LBA.
- NEVER `rm` directories (user rule). NEVER use `PYTHONIOENCODING=utf-8` on Windows.
- Real-PS2 only: every fix must modify ISO/PACKDATA/EXE; PCSX2 texture replacement is investigation-only.

---

## 1. Renderer architecture (the load-bearing facts)

Universal R1188 glyph renderer = **func `0x307DA0`**. It is SHARED across chargen,
narration, boxed dialogue, and the request list — gated by an align/mode value, not
by separate functions. Key internals:

- **Two horizontal pens** on the stack: `sp+0x1ce` = per-glyph proportional ADVANCE accumulator; `sp+0x1cc` = a second origin/Y pen (Patch 23 set this — it feeds **Y**, wrong axis, ignore it).
- **Per-mode draw fns:** narration AND boxed dialogue go through **`0x3060b0`** (the `0x309728-0x309778` draw block); a different path uses `0x307510`. **The 0x3060b0 path is NOT narration-only** — boxed dialogue (e.g. R1196 g577 "Shady Man") uses it too. This is why the narration boxX patch had to be **gated** (see §3).
- **boxX** = descriptor field `desc+0x3c`, read per glyph at `0x30973c (lh t2,0x3c(s0))` and added into the X. Values: narration **0**, dialogue **−228**, request **count*12−184**.
- **Per-line CENTER-anchor** (narration/centered text): origin = boxCenter − glyphCount·12/2 — **count-based** (the per-line count array at `desc+0x40` regenerates each frame as the literal line lengths, e.g. fog = `[23,17,8]`). Proven by register capture (draw-X `t1` = −278px off-left for a wide fog line) + the `indent.p2s` screenshot.
- **Proportional advance is already live** via **Patch 14** (resident ADV table @`0x4C7564`, LEFTSHIFT @`0x4C7690`, hooks at `0x3097A0`/`0x309750`), but only for the ADVANCE — the CENTERING still uses count*12.
- Descriptor array: 32 pointers at RAM `0x565150` (getter `0x3028E0`). Narration uses the **fixed slot `0x565150[0] = 0x1137AC0`** (box_width `+0x1c` = 313, align `+0x2a7` = 0). Its `boxX` is only ever **memset-zeroed**, never set — proven by a live data-write breakpoint on `0x1137AFC` hitting only the memset loop (~`0x11FC44`). That's why we force boxX in the draw, not the setup.
- `glyph_metrics.py` is the SINGLE SOURCE OF TRUTH for advance widths: `ADV[g]=9 if g==0/iw==0 else clamp(ink_width+3,6,23)`, `LEFTSHIFT[g]=max(0,ink_left)`. The #1 desync failure is recomputing widths anywhere else.

**The debugger is what cracked narration.** Save states give RAM only (not mid-draw
registers). PCSX2 EE debugger breakpoints (execute on `0x309778`, data-write on
`0x1137AFC`) + the 128-bit register column gave the live X values that static
analysis + saves could not. For these two remaining issues, **expect to need the
live debugger again** — don't burn days on static disassembly alone.

---

## 2. Box-mode classifier (DONE — don't re-litigate)

`tools/dialogue_classifier.py` reproduces the engine's own dialogue-vs-narration
decision: every `0x04` DISPLAY block is preceded (control-flow order) by a `0x12`
GOSUB to a helper whose first `0x63` align opcode carries the mode (**op0==0
DIALOGUE, >=1 NARRATION**), grounded in EXE write `0x2FA520 → ctx+0x2a7 → renderer
branch 0x307E48`. Validated 19/19. Manual `DIALOGUE_FORCE` is gone. Name-island
groups are handled mode-aware (nameplate-only in narration; kept in dialogue).
See memory `project_box_mode_mechanism.md`.

---

## 3. Narration left-align + reposition (DONE — for reference/pattern)

- LEFT-ALIGN (build): `build_v9.pad_narration_left_align()` pads each narration line with TRAILING spaces to equal glyph count → equal count-based centering → left edges align.
- REPOSITION (EXE **Patch 24**): hook `0x30973c (lh t2,0x3c(s0))` → cave @`0x4CAA30` that forces `boxX=+96` **only if boxX==0** (narration); leaves dialogue (−228) / request untouched. Gated because the draw path is shared (the ungated `li t2,96` shoved Shady Man's dialogue +324px off-right — `oops.p2s`).
- To change the narration offset later: edit the `96` immediate (`0x240A0060`) in Patch 24's cave. See memory `project_narration_leftalign.md`.

---

## 4. ISSUE A — Chargen/Status box wide letter-spacing  (`ramdumps/boxes.p2s`)

**Symptom:** the New-Character/Status screen renders every label and the personality
text with too-wide MONOSPACE letter-spacing ("Press O or X to confirm.", stat
labels Str/Int/…, "Obsessed with traps", etc.). It should be proportional like the
dialogue/narration text now is.

**Root cause (recon-confirmed, `build/harvest/SAVE_chargen.txt`):** chargen text
draws via `jal 0x305E30` (Block-1, @`0x308030`), and its glyph X is a **flat
monospace stride**: `drawX = box_origin(lh 0x3e(s3)) + s7`, where `s7 = index*12`
computed at `0x307FE4-0x307FF0` (per-glyph index counter `v1` incremented +1 at
`0x307F68`) and summed into the X arg at `0x308010-0x30802C`. **Patch 19 (the
existing chargen-proportional patch) writes pen `sp+0x1cc`, which the chargen draw
path NEVER READS** — it's accumulating correct proportional widths into a dead
register. The mode gate (`gp-0x62d8 == RAM 0x4FED18 == 5` for chargen) is live and
correct; only the WRITE TARGET is wrong.

**Fix direction:** retarget Patch 19 from the dead `sp+0x1cc` pen to the **`s7`
stride** — replace `s7 = index*12` with a running proportional ADV sum (read the
resident Patch-14 ADV table @`0x4C7564`, index `gid = cell>>8` per the `(char-32)<<8`
BE cell layout), keeping the `mode==5` gate and the resident tables. Verify on a
fresh chargen save: per-glyph stride should be variable (`ADV['M']`=23, space=9),
not a flat 12. **CAUTION:** the renderer is shared — confirm the chargen prompt
screen AND the input/stat boxes both run under mode==5, and that no other surface
takes the retargeted branch. Stat labels (Str/Int/…) may come from a different
compositor (R2138/R38) — check whether they're the same Block-1 font or a separate
pre-rendered source before assuming one patch fixes all of them.

---

## 5. ISSUE B — Request description overflow + field collision  (`ramdumps/requestissue.p2s`)

**Symptom (two problems):**
1. **Overflow:** the quest description ("Duhan Castle has recently established an Adventurer Assistance Program…") spills past **both** parchment edges — lines are too wide for the window.
2. **Collision:** the description's tail overlaps the fixed "Client: Duhan" field below it ("Ma**Client**rent Duhan" garble) — the desc is too TALL and runs into the next field row.

**What's known:** the request body renders at FIXED **18px monospace** (Patch 22
pinned the Block-2 pen-`0x1ce` advance to 18). The current build greedy-wraps
descriptions to **28 cells / 504px** (`build/inject_r39_quest.py DESC_WRAP_CELLS`).
An earlier recon (`build/harvest/SAVE_requestdesc.json`) put the body LEFT-anchored
at x=64 in a window x=64..576 (512px), but the live `requestissue` shows BOTH-edge
clipping (looks centered) — so **the box geometry is not yet reliably measured; get
a fresh debugger/GS measurement of the actual desc window (left/right px + row
capacity) before finalizing any wrap budget.** Vertical pitch is 24px; the box holds
~6 rows and verbose English descriptions wrap to 7-8.

**The planned fix (per user) — DO BOTH:**
1. **Rewrite the ~60 quest descriptions to use LESS text** (`data/r39_quest_text_aligned.json`, keys ~348-380; client names ~383-410). Shorter, tighter English → fewer wrapped lines → stops the desc colliding with the Client/Reward/Deadline fields. This is mostly editorial condensation; keep meaning faithful (cross-check the Japanese in the same file). NOTE the title field is separately capped at 12 cells by `draw_clamp12` and is already handled (e.g. "Adv Support").
2. **Fix the horizontal OVERFLOW separately** — shortening text does NOT make individual lines fit if the box is narrower than the wrap budget. Two options: (a) lower `DESC_WRAP_CELLS` to the *measured* box width (needs the fresh measurement above), and/or (b) make the request body **proportional** (compress ~30%) by hooking the Block-2 advance like Patch 14 did for narration — the body is currently 18px mono so spaces are wide; this is the cleaner fix and ties into the same proportional-spacing work as Issue A. Also re-verify the R39 stays ≤16 sectors (the offset-table self-check in `inject_r39_quest.py` aborts the build if a slot fails to resolve; the request-menu softlock was an R39 offset-base bug — don't reintroduce it).

---

## 6. Gotchas / lessons (so you don't repeat ours)

- The big renderer is SHARED. Before patching any draw instruction, find ALL callers/modes that reach it and gate appropriately (boxX==0, mode==5, align byte, descriptor field). The ungated narration patch broke dialogue.
- Don't trust a single recon's mechanistic account; they conflicted on narration repeatedly. Validate against live registers.
- Trailing-space padding is invisible but counts toward the engine's count-based centering — that's the trick that left-aligned narration. Test gates were updated to measure INK width (rstrip) for narration.
- The classifier + DIALOGUE_FORCE removal means narration/dialogue routing is automatic now; if a line wraps wrong, inspect the `0x63` helper for its group, don't add manual overrides.
- Commit hygiene: several source files (the classifier, half the test suite) were historically UNTRACKED — run `git status --untracked-files=all` and make sure new `tools/`/`tests/` files actually get added.
