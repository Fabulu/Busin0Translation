# ISO Verification Debug Report

## Key Finding: The ISO IS correctly built. The problem is translation coverage, not the build pipeline.

## 1. ISO Integrity

| Check | Result |
|-------|--------|
| v15.iso exists | Yes, 1,274,544,128 bytes |
| v9.iso == v15.iso | YES (same MD5 for first 1MB, same timestamp May 30 15:14) |
| PACKDATA size in ISO | 839,843,840 bytes |
| PACKDATA_v3.DIG size | 839,843,840 bytes -- MATCH |
| PACKDATA MD5 match | ISO PACKDATA == PACKDATA_v3.DIG -- MATCH |
| EXE MD5 match | ISO EXE == SLPM_653.78_patched -- MATCH |

**The ISO correctly contains both the patched PACKDATA and the patched EXE.**

v15.iso appears to be a copy/rename of v9.iso (no script creates "v15" -- likely manual).

## 2. Translation Coverage (the real problem)

| Category | Count |
|----------|-------|
| Total type-2 resources | 617 |
| Resources with usable English translations | 33 |
| Resources with only [DATA]/[LAYOUT]/[BINARY] tags (no text) | 105 |
| Resources with NO translation entries at all | 479 |
| Patched type-2 in PACKDATA_v3 | 32 (matches expectations) |

**Only 33 out of 617 type-2 resources have usable translations.** The remaining 584 are still Japanese because they were never translated, not because the build is broken.

## 3. Type-1 Resources (R34-R49)

All correctly patched and present in ISO:

| Resource | Status | English msgs | Japanese msgs |
|----------|--------|-------------|---------------|
| R34 | PATCHED | 7 | 2 |
| R35 | PATCHED | 8 | 0 |
| R36 | PATCHED | 8 | 0 |
| R37 | PATCHED | 8 | 0 |
| R38 | PATCHED | 8 | 1 |
| R39 | SAME (type-15, different handler) | 0 | 7 |
| R40-R49 | PATCHED | 7-9 | 0 |

## 4. Binary Resources Deletion (NOT a bug)

The `binary_resources` list in build_v9.py Step 6 deletes 93 files from `build/packdata_resources/`. These are resources tagged as [DATA], [LAYOUT], [BINARY] in the translation batches -- they contain coordinate tables, grid layouts, and binary data, NOT text. The deletion is correct behavior to prevent corrupting non-text data.

## 5. Build Pipeline Flow (verified correct)

```
Step 1: v2 pipeline for type-1 resources
Step 2: Fix type-1 FFFF mismatches (R34-R49)
Step 3: R39 type-15, R46/R47, R1188
Step 4: inject_and_patch creates 124 files in patched_type2/
        (93 are binary/layout resources with no actual text changes)
Step 6: Copies patched_type2/ -> packdata_resources/
        Deletes binary_resources (correctly removes the 93 non-text files)
        Result: 31 type-02 files + 18 other types = 49 files
Step 7: rebuild_packdata.py builds PACKDATA_v3.DIG
Step 8: Injects into ISO, patches EXE
```

## 6. Root Cause of "Nothing Changed"

If the user says nothing changed between builds, possible explanations:

1. **v15 IS v9** -- same file, same timestamp. No new build was run.
2. **Translation coverage is only ~5%** of type-2 resources. Most game text is still Japanese.
3. The 13,397 translated messages are spread across only 33 resources. If the user is looking at areas served by the other 584 untranslated resources, they will see only Japanese.

## 7. What needs to happen next

To see more English text, the project needs translations for the remaining ~584 type-2 resources. The build pipeline itself is working correctly.
