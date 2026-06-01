# Stepwise Build Test Results (2026-05-28)

## Conclusion: The pipeline is NOT silently failing.

The build pipeline (build_v9.py) works correctly at every step. R38 and R1272
contain English data throughout the entire pipeline, from packdata_resources
through PACKDATA_v3.DIG through the final ISO.

The "remaining Japanese" the user sees is NOT caused by data loss or overwriting
in the pipeline. It is caused by **untranslated resources** -- resources that
simply have no English translations available yet.

---

## Step-by-Step Verification

### Step 1: v2 Pipeline (build_full_english_v2.py)
- **Return code**: 0
- **R38 in packdata_resources**: ENGLISH (first msg: "HP")
- **R1272 in packdata_resources**: English font atlas (65,792 bytes payload, matches english_font_atlas.bin)
- **Resources modified**: 20 type-01 resources
- **Messages encoded**: 1,834 across 20 resources

### Step 7: Rebuild PACKDATA (rebuild_packdata.py)
- **Return code**: 0
- **R38 in PACKDATA_v3.DIG**: ENGLISH (sector=1971, 5 sectors, first msg: "HP")
- **R1272 in PACKDATA_v3.DIG**: English font (65,792 bytes payload)
- **R1196 in PACKDATA_v3.DIG**: ENGLISH (first msg: "The medal earned from...")
- **Patched resources**: 52 total

### Step 8: ISO Build
- **R38 in v29 ISO**: ENGLISH (first msg: "HP")
- **R1272 in v29 ISO**: English font confirmed (65,792 bytes payload)
- **R1196 in v29 ISO**: ENGLISH (923 EN messages, 30 JP messages from untranslated entries)

---

## Root Cause of "Remaining Japanese"

### Type-02 Resource Coverage
| Category | Count |
|----------|-------|
| Total type-02 resources | 617 |
| With translations available | 29 |
| Without any translations | 588 |
| Of untranslated: binary/non-text | 94 |
| Genuinely untranslated text resources | 494 |

### Type-02 Message-Level Coverage
- English messages: 12,989
- Japanese messages: 46,493
- **Coverage: 21.8%**

### What's translated (type-02):
Resources in batch_01 through batch_11, plus specialized batches (dungeon, intro,
gap, etc.) -- total of ~30 resources with ~13,400 messages.

### What's NOT translated (type-02):
494 text-bearing type-02 resources have zero translations. These are dungeon
event scripts, town dialogue, etc. that haven't been translated yet.

Examples of untranslated resources: R27-R32, R51, R134, R136, R145, R151, R155,
R156, R165, R167, R183, R231, R240, R241, R245, R307, R308, R311, R314, R315,
R319, R322, R325, R326, and ~470 more.

### Type-01 Resources (all working correctly):
R34, R35, R36, R37, R38, R39, R40, R41, R42, R43, R44, R45, R46, R47, R48, R49
-- all injected with English text.

---

## Minor Issue Found: R1350

R1350 has 1 translation (msg 0: "Ibakaaaa--- go!") in batch_gap1347.json, but
inject_and_patch skips it because its Section 2 has 0 FFFF terminators (only 12
words / 24 bytes). This is an edge case -- the resource format doesn't match the
expected FFFF-delimited structure. Impact: 1 message out of ~60,000 total.

---

## Pipeline Flow (verified working at each step):

```
Step 1: build_full_english_v2.py
  -> packdata_resources/ gets 20 type-01 files (R34-R49, R1053, R1188, R1272, R1908, R2124, R2654)
  -> Also builds PACKDATA.DIG and BUSIN0_EN.iso (both superseded by later steps)

Step 2: Fix type-01 R35, R2654 FFFF mismatches

Step 3: R39 type-15 injection

Step 3.5: R46/R47 type-03 injection

Step 3.6: R1188 comprehensive patch

Step 4: Variable-size type-02 injection (inject_and_patch)
  -> patched_type2/ gets ~29 files
  -> Section 1 offsets patched for each

Step 5: R1193 manual inject

Step 6: Merge patched_type2 into packdata_resources, remove binary resources

Step 7: rebuild_packdata.py -> PACKDATA_v3.DIG (52 patched resources)

Step 8: ISO build from PACKDATA_v3.DIG + EXE patching
```

No data is lost. No step overwrites English with Japanese. The pipeline is correct.
The gap is in translation coverage, not in the build pipeline.
