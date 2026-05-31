# Busin 0: Wizardry Alternative Neo - English Fan Translation

## CRITICAL BUILD INSTRUCTIONS

**ALWAYS rebuild AND copy the ISO in ONE command to avoid stale ISOs:**

```bash
python tools/generate_font_atlas.py && python build/build_v9.py && cp build/BUSIN0_EN_v9.iso build/BUSIN0_EN_vNN.iso
```

**NEVER copy the ISO while the build is still running.** The build writes the PACKDATA directory size as its LAST step. Copying mid-build produces a corrupt ISO with truncated PACKDATA.

**NEVER use `PYTHONIOENCODING=utf-8 python` on Windows.** This is Unix syntax and silently fails. Use just `python` instead.

## Build Pipeline (build/build_v9.py)

1. **Step 1**: v2 pipeline (build_full_english_v2.py) — ALL type-01 resources (R34-R49, R2124, R2654)
2. **Step 2**: Fixed-size injection for R35, R2654 only (flat format, no sub-header)
3. **Step 3**: R39 equipment injection (inject_r39_v2.py)
4. **Step 3.5**: R46/R47 bulletin board (inject_r46_r47.py)
5. **Step 3.6**: R1188 name entry (tools/patch_r1188_direct.py)
6. **Step 4**: Type-2 variable-size injection + Section 1 opcode patching
7. **Step 5**: R1193 manual inject
8. **Step 6**: Merge patched_type2 into packdata_resources
9. **Step 7**: Rebuild PACKDATA (rebuild_packdata.py)
10. **Step 8**: Build ISO (copy original, overwrite PACKDATA + directory size)
11. **Step 8.4**: Patch EXE (patch_exe.py)
12. **Step 8.5**: Write patched EXE into ISO

## Key Architecture

### Translation Data
- `data/translate_chunks/chunk_00-09_translated.json` — original batch translations (0-indexed message IDs)
- `data/translate_chunks/chunk_r38_fix.json` — ONLY entries MISSING from originals (DO NOT override originals)
- `data/type2_translated/batch_*.json` — type-2 dialogue (auto-discovered by glob)
- `data/menu_labels.csv` — font tile definitions for R1272 menu/stat labels

### Message Indexing (CRITICAL)
- The v2 pipeline uses **0-indexed FFFF group numbers** (group 0 = first group after offset table)
- Original chunk files (chunk_00-09) use this same 0-indexed scheme
- **NEVER create fix file entries that override original chunk entries** — the originals are correct
- chunk_r38_fix.json should ONLY contain messages MISSING from chunk_00-09

### Font Atlases
- **R1272** (256x512 PSMT4): Main dialogue font. Positions 0-94 = ASCII, 683-866+ = menu tiles
- **R1188** (1024x1024 PSMT4): Name entry/chargen UI font. Deswizzle: dbw_ct32=512, header=3072
- generate_font_atlas.py MUST be run before build_v9.py

### Known Format Issues
- Type-01 resources have sub-header + offset table — Step 2 CANNOT handle these (corrupts header). Only v2 pipeline handles type-01.
- R38 sidebar/stat labels render via R1272 glyph tiles from MSG glyph streams
- R1188 tab labels are composed at runtime from individual glyph cells (NOT pre-rendered sprites)
- Menu struct records (56 bytes each) at EXE 0x3C3000-0x3C5300 have 2 glyph slots per label
- PSMT8 deswizzle: dbw_ct32 = tex_w / 2. PSMT4: varies per resource.

## Target Disc
- **SLPM-65378** (original release, NOT Atlus Best Collection SLPM-65876)
- trap15 has an active parallel project targeting SLPM-65876
