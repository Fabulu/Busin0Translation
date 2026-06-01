# PACKDATA_v3.DIG Output Verification

Date: 2026-05-28

## R38 Analysis

- **TOC**: sector=1971, sectors=5, type_code=1
- **R38 is type 1 (binary), NOT type 2 (MSG text)**
- It is NOT a text resource and was never expected to contain translatable FFFF-delimited text
- R38 grew from 4 sectors (original) to 5 sectors (patched) -- the build DID modify it
- The first bytes are a pointer/offset table, not glyph indices
- Nearby type-2 resources: R35 is the only type-2 in the R34-R43 range

## R1272 (Font Atlas) Analysis

- **TOC**: sector=211364, sectors=33, type_code=1
- **Size**: 67584 bytes = 33 sectors (correct)
- **Font atlas IS properly injected**
  - The patched 1272_type01.raw in `build/packdata_resources/` contains the english_font_atlas.bin at offset 16
  - 19,390 bytes differ between original and patched (out of 67,584)
  - PACKDATA_v3.DIG R1272 matches the patched file exactly
- The injection path works: build_full_english_v2.py Step 3 writes `build/packdata_resources/1272_type01.raw`, then rebuild_packdata.py picks it up

## Step 8 Pipeline Verification

- **Step 8 reads `build/PACKDATA_v3.DIG`** (line 262 of build_v9.py) -- this is CORRECT
- It does NOT read the wrong file
- The pipeline flow:
  1. Step 1: `build_full_english_v2.py` runs (injects font atlas + type-1 patches into `build/packdata_resources/`)
  2. Steps 2-5: Type-2 MSG patching, outputs to `build/patched_type2/`
  3. Step 6: Merges patched_type2 into packdata_resources, removes unsafe binary resources
  4. Step 7: `rebuild_packdata.py` builds `PACKDATA_v3.DIG` from packdata_resources
  5. Step 8: Reads `PACKDATA_v3.DIG` and writes it into the ISO

## Conclusion

**No pipeline routing bug found.** Both R38 and R1272 are handled correctly:

- R38 is type-1 (binary data, not translatable text) -- if Japanese text appears to come from "R38", the actual source resource index may be different
- R1272 has the English font atlas properly injected
- Step 8 reads the correct file (PACKDATA_v3.DIG)

If Japanese text is still visible in-game, the issue is likely:
1. The specific resource containing that text was not included in the translation chunks
2. The resource is a type that the pipeline doesn't handle (type 3, 6, 15, 20, etc.)
3. The text is hardcoded in the EXE rather than in PACKDATA resources
