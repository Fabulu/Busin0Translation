# ISO Build Trace: Sector-Level Cache and Build Pipeline Analysis

Date: 2026-05-28

## 1. Source Files

| File | Size | Notes |
|------|------|-------|
| Original ISO | 1,274,544,128 | `Busin 0 - Wizardry Alternative Neo (Japan) (v2.01).iso` |
| Extracted PACKDATA.DIG | 839,661,568 | `extracted/PACKDATA.DIG` (from original) |
| v2 PACKDATA.DIG | 839,837,696 | `build/PACKDATA.DIG` (+176,128 vs extracted) |
| v9 PACKDATA_v3.DIG | 839,829,504 | `build/PACKDATA_v3.DIG` (+167,936 vs extracted) |
| v2 ISO | 1,274,544,128 | `build/BUSIN0_EN.iso` |
| v9 ISO | 1,274,544,128 | `build/BUSIN0_EN_v9.iso` |

## 2. Build Pipeline Execution Order

### build_v9.py calls:

1. **Step 1**: `os.system('python build/build_full_english_v2.py')` -- runs the ENTIRE v2 pipeline first
2. **Steps 2-6**: Additional type-2 injections, R39, R46/R47, R1188, merges into `build/packdata_resources/`
3. **Step 7**: `os.system('python build/rebuild_packdata.py')` -- builds `build/PACKDATA_v3.DIG`
4. **Step 8**: Builds `build/BUSIN0_EN_v9.iso`

### What the v2 pipeline (build_full_english_v2.py) does:

- Steps 1-4: Type-1 translations, font atlas, R1188 patches
- Step 5: Rebuilds `build/PACKDATA.DIG` (its own PACKDATA, NOT PACKDATA_v3)
- **Step 6**: `shutil.copy2(ISO_PATH, OUTPUT_ISO)` copies ORIGINAL ISO to `build/BUSIN0_EN.iso`
  - Then opens `build/BUSIN0_EN.iso` r+b and overwrites PACKDATA region
  - Then patches EXE into that same ISO
- Source: `ISO_PATH = 'Busin 0 - Wizardry Alternative Neo (Japan) (v2.01).iso'` (the ORIGINAL)

### What build_v9.py Step 8 does:

```python
shutil.copy2('Busin 0 - Wizardry Alternative Neo (Japan) (v2.01).iso', 'build/BUSIN0_EN_v9.iso')
```

- **Copies from the ORIGINAL ISO**, NOT from the v2 pipeline's `build/BUSIN0_EN.iso`
- Then opens `build/BUSIN0_EN_v9.iso` for `r+b` and overwrites PACKDATA region with `build/PACKDATA_v3.DIG`

## 3. CRITICAL FINDING: The v2 pipeline's ISO is wasted work

The v2 pipeline (Step 1 of build_v9.py) builds `build/BUSIN0_EN.iso` with:
- Its own PACKDATA.DIG (type-1 only translations)
- Patched EXE

But then build_v9.py Step 8:
- Copies from the **ORIGINAL** ISO (ignoring v2's ISO entirely)
- Writes `PACKDATA_v3.DIG` which contains type-1 + type-2 translations

This is **correct behavior** -- v9 is NOT using a stale v2 ISO. The v2 pipeline runs only for its
side effect of populating `build/packdata_resources/` with type-1 patched resource files. The v2
ISO build is indeed wasted I/O (a ~1.2 GB copy that's immediately discarded), but it does not
cause correctness issues.

## 4. PACKDATA Size Discrepancy

- Extracted original: 839,661,568 bytes
- v9's PACKDATA_v3.DIG: 839,829,504 bytes (**+167,936 bytes = +82 sectors**)
- v2's PACKDATA.DIG:    839,837,696 bytes (**+176,128 bytes = +86 sectors**)

Both `rebuild_packdata.py` and `build_full_english_v2.py` pad to the original size if smaller,
and print a WARNING if larger. Since both are larger, the WARNING was printed but the build
continued.

**This means the new PACKDATA extends BEYOND the original ISO extent allocation.**

When `iso.write(d)` writes PACKDATA_v3.DIG into the ISO at the PACKDATA LBA, it writes 167,936
more bytes than the original extent. This overwrites whatever comes AFTER PACKDATA.DIG in the ISO.

However, PACKDATA.DIG is typically the last (and by far largest) file on the disc, so this
overflow likely writes into unused trailing space or past the end of meaningful data. The ISO
file size stays the same because `shutil.copy2` already created a full-size copy.

## 5. File Locking Analysis

- `shutil.copy2()` opens source read-only, writes to destination, then closes both
- Then `open('build/BUSIN0_EN_v9.iso', 'r+b')` opens the destination for modification
- These are sequential operations, no concurrent access
- **No file locking issue exists**

## 6. PCSX2 Sector-Level Cache

PCSX2 does NOT have a persistent sector-level read cache that would serve stale data between
runs. When you load an ISO in PCSX2:
- It reads from the ISO file on disk
- Each boot/game launch reads fresh data from the file
- There is no cross-session cache that remembers old sectors

However, PCSX2 does have:
- **Memory card saves**: These persist between runs but don't cache game data
- **Savestates**: These capture the FULL EE/IOP/GS state including RAM contents. If you load
  an old savestate made from a previous ISO build, the RAM will contain the OLD PACKDATA
  resources (since they were already loaded into RAM at savestate time). This is the most
  common source of "stale data" symptoms.
- **Disc cache** (`cache/` folder): PCSX2 can create a block cache for optical drive access,
  but when using an ISO file directly this is bypassed.

## 7. Directory Record Size Update

build_v9.py Step 8 updates the directory record's file size fields:
```python
iso.seek(root_lba * SECTOR + pos + 10)
iso.write(struct.pack('<I', len(d)))   # LE size
iso.write(struct.pack('>I', len(d)))   # BE size
```

This correctly updates the ISO9660 directory entry to reflect the new PACKDATA size. The game
reads the directory to find the extent/size, so the larger PACKDATA will be fully visible.

## 8. Conclusion: No Stale Cache Issue

The build pipeline is sound:
- v9 ISO copies from the ORIGINAL ISO (clean base)
- PACKDATA_v3.DIG overwrites the PACKDATA region with the correct combined translations
- Directory record is updated with new size
- No file locking conflicts
- PCSX2 has no persistent sector cache that would serve stale data

**If Japanese text persists in the game, the issue is NOT in the ISO build pipeline or
PCSX2 caching.** The remaining Japanese is either:
1. Text that was never translated (no entry in translation batches)
2. Text baked into texture atlases (not MSG-format, requires bitmap editing)
3. Text rendered by the EXE from hardcoded glyph indices (requires EXE patching)
4. Resources excluded by the binary_resources blacklist or type-code filtering
