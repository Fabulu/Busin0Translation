# Agent Handoff: Busin 0 English Fan Translation

## Date: 2026-06-02 (updated)
## Current Build: v33 (commit 088367b)
## Context Window: Exhausted after extensive PACKDATA/TOC investigation

---

## CHARGEN KANJI MYSTERY — SOLVED (2026-06-02)

### Root Cause
R2100 (type-04, 139KB, PACKDATA sectors 17-84) and R1370 (type-04, 82KB, sectors 85-124) are embedded in the PACKDATA header gap. rebuild_packdata.py copies them VERBATIM from the original Japanese disc and NEVER modifies them. These resources provide essential data for the chargen/name entry screen.

### Evidence
- Zeroing both R2100+R1370 → name entry screen blacks out
- TOC nuke (zeroing all 125 header sectors) → entire game blacks out
- Zeroing individual resources at TOC sector offsets → no effect (those resources are fine)
- R1188 at TOC[1188] XOR → no crash, no change (R1188 may not be the font atlas we thought)

### Fix Path
1. Isolate which resource (R2100 vs R1370) provides the chargen font data
2. Analyze its type-04 format
3. Modify it with English text/font data
4. Update rebuild_packdata.py to include modified R2100/R1370 instead of copying original

### What Works (confirmed)
- Dialogue text via R1272 + R38/R39 glyph streams ✓
- EXE patches (save slots, NPC names, banner) ✓
- PCSX2 texture replacement for chargen labels ✓ (emulator-only)

---

## WHAT WORKS (confirmed in-game)

1. **12,860+ type-2 dialogue messages** — English text displays correctly in dialogue boxes
2. **R38 translations** — Race names (Human/Elf/Gnome/Dwarf/Hobit/Automa), class names (Fighter/Mage/Priest), personality names + descriptions, alignment values
3. **R37 prompts** — "Enter your name.", "Select gender.", etc. display correctly
4. **R34 item translations** — 564 weapon/armor/item names
5. **R39 equipment translations** — 84 OT-indexed messages + 533 inline extra data translations
6. **R46/R47 bulletin board + combat** — 355 translations
7. **Yes/No buttons** — Fixed (R37/R48/R49 were ALL off-by-one, shifted -1)
8. **Word wrap** — Auto line break at 18 chars for type-2 dialogue
9. **Page breaks** — FFD2 every 3 lines for clickthrough dialogue
10. **EXE patches** — Save slot names, 2 SJIS strings, NPC names (Emilia/Lute)
11. **Name entry keyboard grid** — Shows proper A-Z, a-z
12. **R1272 font atlas** — 67,584 bytes (original size), loads correctly, ASCII positions 0-94 work

## WHAT DOESN'T WORK (the chargen kanji problem)

### The Core Unsolved Problem

The chargen (character creation) screen shows Japanese kanji for:
- **Stat labels**: 力, 知恵, 信仰心, 生命力, 敏捷度, 幸運度 (STR/INT/FTH/VIT/AGI/LCK)
- **Sidebar labels**: 性別, 種族, 属性, 職業 (Gender/Race/Alignment/Class)
- **Banner**: 新規登録 (New Registration)
- **Name entry tabs**: カナ, かな, 英数, 記号, 決定 (Kana/Hira/ABC/Sym/OK)
- **Gender values**: 男, 女 on the sidebar (M/F in text works but sidebar kanji persists)

### What We PROVED

Through elimination testing (wipe tests where ALL pixel data was zeroed directly in the ISO):

| Resource | Wiped? | Effect on stat labels |
|----------|--------|----------------------|
| R1188 (1024x1024 PSMT4, total wipe) | YES, all 524,288 bytes zeroed | **NO EFFECT** — kanji still visible |
| R1272 (256x512 PSMT4, total wipe) | YES, all 65,536 bytes zeroed | **NO EFFECT** — kanji still visible |
| R1269-R1277 (portraits, not fonts) | YES, all zeroed | **NO EFFECT** — these are character art |
| R1302-R1303 | YES, zeroed | **NO EFFECT** |
| R38 minimal test (single byte change) | YES, glyph 346→X | **NO EFFECT** — R38 doesn't control chargen labels |

### What This Means

**NONE of the PACKDATA resources we've tested contain the chargen stat label kanji bitmaps.** Wiping every suspected font resource had zero visual effect. The kanji MUST come from:

1. **A resource we haven't identified** — there are 2,883 resources total, we only tested ~15
2. **The EXE itself** — the font bitmap data might be embedded in the 4.1MB EXE binary (not in PACKDATA)
3. **GS VRAM pre-initialization** — the PS2 might have font data baked into the BIOS or loaded before our ISO data
4. **A completely different rendering mechanism** — maybe these labels aren't font-rendered at all but are pre-rendered 2D sprites from a scene/model resource

### Architecture Summary

Two font rendering systems exist:
- **System 1 (TextEvent/MSG)**: Uses R1272 PSMT4 atlas, grid formula col=glyph_id%21, row=glyph_id//21. Handles dialogue text. **WORKS** for English.
- **System 2 (Cell Data/Page)**: Uses a cell data table at EXE VA 0x4DB100 with UV/VRAM coordinates. Maps glyph IDs to specific VRAM addresses. The font page dispatch at VA 0x30B770 selects resources. **UNKNOWN** which resource provides the bitmaps. R1188 was the leading candidate but wipe testing disproved it.

### Cell Data Details (from EXE RE)

Glyph 346 (力/STR):
- Cell data at EXE file offset 0x3D9818
- Format: 8 bytes (U, V, W, flag, VRAM_block_lo, VRAM_block_hi, gs_config, 0)
- Values: U=2, V=60, W=100, VRAM block 0xAD70
- Page 16, cell index 7

All stat label glyphs use similar cell data entries pointing to VRAM blocks in range 0xA140-0xA9B0.

## OFF-BY-ONE ISSUE (CRITICAL FOR NEW AGENTS)

The v2 build pipeline (`build_full_english_v2.py`) uses **0-indexed** FFFF group numbers (group 0 = first message after the offset table). 

**Original chunks** (chunk_00-09_translated.json) use this same 0-indexed scheme and are CORRECT.

**Our fix/translated chunks** were created with 1-indexed message IDs. Files that needed -1 shift (already applied):
- chunk_r38_fix.json ✓
- chunk_r37_extra.json ✓  
- chunk_r37_r48_r49_translated.json ✓
- chunk_r40_r42_translated.json ✓
- chunk_r43_r45_translated.json ✓

Files confirmed correct (no shift needed):
- chunk_r36_translated.json ✓
- chunk_r43_fix.json ✓
- chunk_r34_fix.json ✓

**RULE**: When creating new chunk files, use 0-indexed message IDs matching the original chunks.

## BUILD PIPELINE

### build_v9.py Steps:
1. Step 1: v2 pipeline (build_full_english_v2.py) — ALL type-01 resources
2. Step 2: Fixed-size injection for R35, R2654 only
3. Step 3: R39 injection (inject_r39_v2.py)
4. Step 3.1: R39 inline patches (patch_r39_inline.py)
5. Step 3.5: R46/R47 injection
6. Step 3.6: R1188 comprehensive patch
7. Step 4: Type-2 variable-size injection + Section 1 opcode patching
8. Step 5: R1193 manual inject
9. Step 6: Merge patched_type2 into packdata_resources
10. Step 7: Rebuild PACKDATA (rebuild_packdata.py → PACKDATA_v3.DIG)
11. Step 8: Build ISO (copy original, overwrite PACKDATA + directory size)
12. Step 8.4: Patch EXE (patch_exe.py — 18 patches including Patch 5 banner)
13. Step 8.5: Write patched EXE into ISO

### CRITICAL BUILD NOTES:
- **NEVER use `PYTHONIOENCODING=utf-8 python`** — this is Unix syntax and silently fails on Windows
- **NEVER extend R1272 beyond 67,584 bytes** — the game rejects larger atlases
- **ALWAYS regenerate font atlas** before building: `python tools/generate_font_atlas.py`
- **R39 inline patches get OVERWRITTEN** by inject_r39_v2.py — must apply AFTER Step 3
- **The v2 pipeline builds its own ISO** at build/BUSIN0_EN.iso — this is IGNORED by build_v9.py
- **Copy ISO AFTER build completes** — mid-build copy produces corrupt directory size

## KEY FILE LOCATIONS

### Translation Data
- `data/translate_chunks/chunk_00-09_translated.json` — original batch translations (0-indexed, CORRECT)
- `data/translate_chunks/chunk_r*.json` — fix/extra files (0-indexed after shift fix)
- `data/type2_translated/batch_*.json` — type-2 dialogue (auto-discovered by glob)
- `data/menu_labels.csv` — font tile definitions for R1272

### Font Resources
- R1272: `extracted/packdata_raw/1272_type01.raw` — PSMT4 256x512, THE ASCII font atlas
- R1188: `extracted/packdata_raw/1188_type01.raw` — PSMT4 1024x1024, deswizzle dbw_ct32=512
- R1269-R1277: Character/monster PORTRAITS (PSMT8), NOT fonts despite earlier claims

### Tools
- `tools/generate_font_atlas.py` — Creates R1272 atlas with swizzle_psmt4()
- `tools/psmt4_deswizzle.py` — PSMT4 deswizzle/swizzle (working, round-trip verified)
- `tools/psmt8_deswizzle.py` — PSMT8 deswizzle/swizzle (working)
- `tools/patch_r1188_comprehensive.py` — R1188 kana/label patcher
- `tools/render_menu_tiles.py` — Renders English text into font tile positions

### Build Output
- `build/BUSIN0_EN_v33.iso` — latest normal build
- `build/BUSIN0_EN_r1188_total_wipe.iso` — R1188 all zeros (NO EFFECT on kanji)
- `build/BUSIN0_EN_r1272_direct_wipe.iso` — R1272 all zeros (NO EFFECT on kanji)

### Analysis Reports
- `runs/CLAUDE-RUNS/RUN-20260528-remaining-japanese/` — 100+ analysis reports

## 2026-06-01 SESSION FINDINGS (CRITICAL)

### TOC Nuke Test: BLACK SCREEN
Zeroed the entire PACKDATA TOC (first 23,072 bytes) in the built ISO. Result: **BLACK SCREEN** on boot. This proves PCSX2 reads from the correct location in the ISO file and the TOC is essential. The game cannot function without it.

### Individual Resource Zeroing: NO VISIBLE EFFECT
Despite the TOC nuke proving correct byte offsets, zeroing individual resources (R1188, R1272, etc.) at their TOC-indicated offsets produces no visible change. The bytes ARE at the correct positions (verified), yet the game renders everything normally.

### PACKDATA Header Has 221KB Secondary Structure
`rebuild_packdata.py` copies a 221KB block verbatim from the original PACKDATA header. This secondary structure (beyond the TOC) is copied as-is without modification. **Next investigation: this secondary structure may contain embedded resource data or alternate pointers that the game actually reads.**

### R1188 XOR Test: Definitive Dead Resource
XOR-flipped the entire 528KB of R1188 at TOC[1188]. Result: **no crash, no visual change, nothing.** The game does not read TOC[1188] at all. All prior R1188 pixel patching work targeted a dead resource.

### All Working Translations Confirmed
Dialogue, R38 sidebar labels, EXE patches -- all confirmed present and functional in the built ISO. The build pipeline produces correct output.

### PCSX2 Texture Replacement Works for Chargen
Texture replacement at the GS level successfully shows English stat labels. This is emulator-only (not an in-ISO solution) but confirms the rendering path uses R1272 glyphs.

### PACKDATA Overflow Bug
PACKDATA overflows into BSN2_0.DSI by 90 sectors, causing audio corruption. The rebuilt PACKDATA is larger than the original due to variable-size type-2 resources growing from translation. This needs a fix (shrink resources or relocate BSN2_0.DSI).

---

## SUGGESTED NEXT APPROACHES

### 0. PACKDATA secondary structure analysis (HIGHEST PRIORITY)
The 221KB secondary structure in the PACKDATA header is copied verbatim by rebuild_packdata.py. It may contain embedded resource data, alternate offset tables, or cached copies of font/texture data. Analyze its format: does it contain pointers? Does it duplicate TOC entries? Does it embed small resources inline? If the game reads font data from THIS structure rather than the TOC-indexed resources, that explains why individual resource zeroing has no effect.

### 1. Brute-force resource elimination
Systematically wipe EVERY resource in PACKDATA (one at a time or in groups) until the stat labels disappear. There are 2,883 resources -- but you can skip type-02 (dialogue), type-03/04/05/06 (3D data), and focus on type-01 resources we haven't tested.

### 2. GS VRAM capture during rendering
Use PCSX2's GS debugger to capture the EXACT GS state (TEX0 register with TBP0) at the moment stat labels render. TBP0 tells you which VRAM page the kanji texture is at. Cross-reference with resource upload addresses to find the source resource.

### 3. EXE-embedded font data
Search the 4.1MB EXE for the kanji bitmap data directly. The stat label kanji (力, 知, 恵, etc.) are simple 12x12 or 24x24 bitmaps. Search for recognizable pixel patterns in the EXE's data section.

### 4. MIPS breakpoint debugging
Set a hardware breakpoint in PCSX2's debugger on the GS TEX0 register write. When the stat label renders, the breakpoint fires and shows the call stack — revealing which code uploaded the font texture and from where.

### 5. Scene/model resource investigation
The chargen screen might use a pre-rendered 3D scene resource (type-03/04) that has the stat labels baked into a texture map, not rendered from a font atlas at all.

### 6. trap15's project
trap15 has a parallel Busin 0 translation project (targeting SLPM-65876, not our SLPM-65378). His RPGCodex posts from Dec 2025/Jan 2026 show he solved font rendering. Contacting him for technical insights about the font system would be the fastest path.

## TRAP15 REFERENCE
- RPGCodex thread: Busin 0 discussion, posts #96 and #99 by trap15 (Dec 2025)
- Targets: SLPM-65876 (Atlus Best Collection v2.01)
- Status: Font renderers wrangled, character creation mostly done, tavern far along
- Has working in-game English screenshots

## GIT LOG (key commits)
```
09ac4c8 v33: Fix 349 more off-by-one entries, M/F gender, Neut alignment
4be18d5 BREAKTHROUGH: Stat labels from R39 (WRONG — they were equipment descriptions)
d6db2eb CRITICAL: Revert atlas to 67,584 bytes (game rejected 83KB)
7a1a329 CRITICAL: Font atlas swizzle fix (LINEAR→PSMT4)
86690f3 Fix R1272 palette (was reading pixel data as palette)
d9470b8 CRITICAL: All os.system() calls broken on Windows
318e4ef CRITICAL: Race condition in ISO build + R38 pipeline fix
6c166ec Wave 5: System menus R36-R49
58e3d3d Wave 6: R46/R47 bulletin board + combat
a62c7bb Initial commit (v11 baseline)
```
