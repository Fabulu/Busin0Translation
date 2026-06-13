# Busin 0: Wizardry Alternative Neo - English Fan Translation

## ABSOLUTE RULE: REAL PS2 COMPATIBILITY

**ALL fixes MUST work on real PS2 hardware.** PCSX2 texture replacement is an investigation tool ONLY — NEVER propose it as a solution. The user has stated this repeatedly. Every translation must modify the actual ISO data (PACKDATA resources, EXE patches, font atlases). If a fix only works in PCSX2, it is NOT a fix.

## CRITICAL TESTING INSTRUCTIONS

**NEVER load save states from an older ISO build.** PCSX2 save states (.p2s) contain the FULL 32MB EE RAM including all loaded game resources. Loading a save state from v22 will show v22's data regardless of which ISO is mounted. **Always boot FRESH from the title screen** when testing a new ISO.

**Verify the ISO before testing:** `python verify_iso.py build/BUSIN0_EN_vNN.iso`

## CRITICAL BUILD INSTRUCTIONS

**ALWAYS rebuild AND copy the ISO in ONE command to avoid stale ISOs:**

```bash
python tools/generate_font_atlas.py && python build/build_v9.py && cp build/BUSIN0_EN_v9.iso build/BUSIN0_EN_vNN.iso
```

**NEVER copy the ISO while the build is still running.** The build writes the PACKDATA directory size as its LAST step. Copying mid-build produces a corrupt ISO with truncated PACKDATA.

**NEVER use `PYTHONIOENCODING=utf-8 python` on Windows.** This is Unix syntax and silently fails. Use just `python` instead.

## Build Pipeline (build/build_v9.py)

1. **Step 1**: v2 pipeline (build_full_english_v2.py) — ALL type-01 resources (R34-R49, R2124, R2654)
2. **Step 2**: Fixed-size injection for problem type-01s (R34, R35, R2124, R2654 — flat format). R34 group 0 is a structural table (49-entry u16 list): Step 2 skips it and maps message mi = group gi−1. R35 is type-02 in the manifest but is handled here by Step 2.
3. **Step 3**: R39 equipment injection (inject_r39_v2.py)
4. **Step 3.1**: R39 inline Japanese patch (tools/patch_r39_inline.py)
5. **Step 3.2**: R39 quest UI labels + quest titles (build/inject_r39_quest.py)
6. **Step 3.5**: R46/R47 bulletin board (build/inject_r46_r47.py). The renderer centers each post on the widest line counting 0x0000 pads as full cells — R46 injection therefore uses symmetric per-line padding.
7. **Step 3.6/3.7**: **DISABLED in v85** — the old R1188 patchers (patch_r1188_comprehensive.py / patch_r1188_bw256.py; formerly patch_r1188_direct.py) used a layout off by 1008 bytes and corrupted ~150 live glyph cells of the dialogue font (BUG-3: the r/y/V glyph artifacts). R1188 must ship PRISTINE; the build deletes any stale R1188 override.
8. **Step 3.8**: R2100 chargen font atlas (tools/patch_r2100.py)
9. **Step 3.9**: R2138 unified patcher (tools/patch_r2138.py — sub0/4/6/7/25/26/27)
10. **Step 4**: Type-2 variable-size injection + Section 1 opcode patching (tools/patch_section1_offsets.py using the tools/sec1_disasm.py BFS disassembler). Resources whose Section 1 fails the BFS walk (e.g. R989/R990/R1034 — binary Section 1) are SKIPPED by inject_and_patch and ship pristine.
11. **Step 5**: R1193 intro narration (tools/patch_r1193_narration.py) — trailing block after the last FFFF, drawn by 23 opcode-0x14 line records
12. **Step 6**: Merge patched_type2 into packdata_resources
13. **Step 7**: Rebuild PACKDATA (rebuild_packdata.py)
14. **Step 8**: Build ISO (copy original, overwrite PACKDATA + directory size)
15. **Step 8.4**: Patch EXE (patch_exe.py)
16. **Step 8.5**: Write patched EXE into ISO

## Key Architecture

### Translation Data
- `data/translate_chunks/chunk_00-09_translated.json` — original batch translations (0-indexed message IDs)
- `data/translate_chunks/chunk_r38_fix.json` — ONLY entries MISSING from originals (DO NOT override originals)
- `data/type2_translated/batch_*.json` — type-2 dialogue (auto-discovered by glob)
- `data/menu_labels.csv` — font tile definitions for R1272 menu/stat labels (LEGACY — nothing renders from the R1272 atlas, see Font Atlases)

### Message Indexing (CRITICAL)
- The v2 pipeline uses **0-indexed FFFF group numbers** (group 0 = first group after offset table)
- Original chunk files (chunk_00-09) use this same 0-indexed scheme
- **NEVER create fix file entries that override original chunk entries** — the originals are correct
- chunk_r38_fix.json should ONLY contain messages MISSING from chunk_00-09

### Font Atlases
- **R1188** (1024x1024 PSMT4, header=3072): The LIVE dialogue/narration font — a 24x24 serif glyph atlas. glyph_id = row*42 + col; ASCII glyphs at char−32. Uploaded VERBATIM from disc to VRAM TBP0=0x3000 as a 512x256 PSMCT32 transfer (proven via GS dump 20260612061701). It MUST ship pristine — see disabled Steps 3.6/3.7 (BUG-3).
- **R1272** (256x512): NOT the main dialogue font. The original resource is a character sprite. No GS-dump-observed scene samples the English atlas written there; the old "menu tile" positions 106-159 now hold a duplicate A-Z and nothing renders from them.
- generate_font_atlas.py MUST be run before build_v9.py

### Known Format Issues
- Type-01 resources have sub-header + offset table — Step 2 CANNOT handle these (corrupts header). Only v2 pipeline handles type-01.
- R38 sidebar/stat labels render via glyph tiles from MSG glyph streams (the old "via R1272" attribution is unverified — v85 GS dumps show no scene sampling the R1272 English atlas)
- R1188 tab labels are composed at runtime from individual glyph cells (NOT pre-rendered sprites)
- Menu struct records (56 bytes each) at EXE 0x3C3000-0x3C5300 have 2 glyph slots per label
- PSMT8 deswizzle: dbw_ct32 = tex_w / 2. PSMT4: varies per resource.
- GS-dump tooling: in PCSX2 GS dump v9 files, VRAM starts at data_start+425 — prior scripts that read from data_start+0 read garbage.

#### Type-02 Section 1 script format (v85 recon)
- Section 1 is a **byte-addressed stream of big-endian u16 opcodes** — odd-length opcodes exist, so it cannot be treated as a u16 array.
- Interpreter dispatcher: va 0x002F3230 in SLPM_653.78, with a 193-entry handler table at 0x004C9360. Recovered per-opcode byte-length table: `build/recon_v85/exe-interpreter/opcode_table_v85.json`.
- Section-2 references come ONLY from: opcode 0x04 (u32 off@+2, u32 cnt@+6), opcodes 0x0C/0x0D (u16 idx@+4), and opcode 0x14 name/label refs (u32 off@+6, u32 cnt@+10 — names are glyph prefixes inside groups).
- Jump targets are Section-1-relative and NEVER need remapping.
- Section-1 patching is done by the BFS disassembler `tools/sec1_disasm.py` + `tools/patch_section1_offsets.py`. **Pattern matching must NEVER be reintroduced.**

## Remaining Untranslated Content

### Type-2 Resources (~587 unscanned)
The type-2 extraction (`tools/extract_untranslated_type2.py`) filtered aggressively — min 5 glyphs, 50% glyph map coverage, 3+ consecutive katakana/kanji. This skipped ~587 of ~617 type-2 resources. Many are genuinely binary (dungeon maps, scene data), but some may contain sparse dialogue (1-3 short messages among binary data). A less aggressive scan is needed to find remaining text. Resources R680-R911 (dungeon scripts) are the most likely to have hidden dialogue.

### Town-Hub Buttons & Status Labels (BUG-4/BUG-5, open)
The old "R1272 menu font tiles" theory is DEAD — nothing renders from the R1272 atlas (see Font Atlases). The verified sources of the remaining Japanese UI text:
- **Town-hub buttons**: pre-rendered kanji strips in **R2136** (~offset 16544) and **R2124** (~offsets 2016/21792)
- **Tavern submenu**: a runtime-composed strip
- **Status labels**: **R1365**
Translating these requires in-place pixel re-rendering of the pre-rendered strips — NOT atlas tiles.

### EXE SJIS Strings — COMPLETE
All player-visible SJIS strings are patched (8 patches). The remaining ~686 SJIS runs are all debug-only (printf format strings, engine error messages). Full audit done 2026-06-09.

### R1188 Tab Labels — COMPLETE
Tab labels (Kana/Hira/ABC/Sym/OK) render through R2138 sub7, NOT R1188. Already fully English via patch_r2138.py. Confirmed in screenshots 2026-06-06.
- **Equipment type icons**: Weapon/armor type labels (剣/斧/杖 etc.) are pre-rendered sprites in an unidentified PACKDATA resource.
- **Dungeon compass**: N/S/E/W directional labels — location unknown.
- **Ending narration**: End-game text — resource location unidentified.

### PACKDATA Overflow Warning
The rebuilt PACKDATA.DIG is ~190KB larger than the original, overflowing into BSN2_0.DSI (audio data) by ~90 sectors. This may corrupt audio on real PS2 hardware. Needs investigation — either shrink PACKDATA or relocate BSN2_0.DSI in the ISO.

## Target Disc
- **SLPM-65378** (original release, NOT Atlus Best Collection SLPM-65876)
- trap15 has an active parallel project targeting SLPM-65876
