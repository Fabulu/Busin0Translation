# v24 ISO Integrity Report

**Date:** 2026-05-28  
**ISO:** `build/BUSIN0_EN_v24.iso`  
**Size:** 1,274,544,128 bytes (1.19 GB)  
**Built:** 2026-05-31 10:31

---

## 1. PACKDATA.DIG Size

| Metric | Value | Status |
|--------|-------|--------|
| PACKDATA.DIG size in ISO | 839,845,888 bytes (800.9 MB) | **PASS** |
| Expected | ~801 MB (not 261 MB) | OK |

---

## 2. R38 (Character Creation Labels) Verification

Parsed using offset table (msg_count=188, stream_start=byte 772).

**IMPORTANT:** The naive FFFF-scan method (scanning from first 0xFFFF byte) produces
an off-by-one error because it picks up the offset table's trailing 0xFFFF flag at
byte 770. All message indices below use the correct offset-table-based numbering.

| Check | Group | Expected | Actual | Status |
|-------|-------|----------|--------|--------|
| MSG 2 | GRP 2 | STR | STR | **PASS** |
| MSG 25 (gender) | GRP 25 | Mars symbol (glyph 518) | [518] = Mars symbol | **PASS** |
| MSG 29 (race) | GRP 29 | Human | Human | **PASS** |
| MSG 34 (race) | GRP 34 | Automa | Automa | **PASS** |
| MSG 148 (alignment) | GRP 148 | Good "G" | Good "G" | **PASS** |

R38 fix chunk (`chunk_r38_fix.json`, 12 entries, modified 2026-05-31 10:28) is
correctly applied. All labels including gender symbols, alignments, and race
abbreviations are English.

### Known Remaining Japanese in R38

- GRP 10: "Level" contains fullwidth "v" (glyph 86 = v, but the "Le" prefix uses
  correct ASCII). The "v" is fullwidth from the original -- it renders as "Level"
  with a JIS v rather than ASCII v.
- GRP 19-24: "Lv1" through "Lv7" use fullwidth digits/v from original encoding.
- These are cosmetic issues from the original glyph table, not missing translations.

---

## 3. R1272 Font Atlas

| Metric | Value | Status |
|--------|-------|--------|
| Sector count | 41 sectors | OK |
| Payload size | 82,176 bytes | OK |
| Atlas dimensions | 256 x 642 pixels | **EXTENDED** |
| Standard height | 512 px | -- |
| Extended height | 642 px (130 extra rows) | **PASS** |
| Tile grid | 21 x 53 = 1,113 tiles | OK |
| Extended region non-zero bytes | 3,825 | Has glyph data |

The atlas is extended well beyond the standard 512px. It contains 1,113 potential
tile slots (21 tiles/row x 53 rows). The extended region (rows 512-642) has active
glyph data (3,825 non-zero bytes).

---

## 4. EXE Patches (SLPM_653.78)

EXE size: 4,185,776 bytes

### Save Slot Names (Patch 1)

| Offset | Expected | Actual | Status |
|--------|----------|--------|--------|
| 0x3FC720 | BUSIN 0 | BUSIN 0 | **PASS** |
| 0x3FC750 | BUSIN 0 Data 1 | BUSIN 0 Data 1 | **PASS** |
| 0x3FC770 | BUSIN 0 Data 2 | BUSIN 0 Data 2 | **PASS** |
| 0x3FC790 | BUSIN 0 Data 3 | BUSIN 0 Data 3 | **PASS** |
| 0x3F9370 | BUSIN 0 Suspend | BUSIN 0 Suspend | **PASS** |
| 0x3F9678 | BUSIN 0 | BUSIN 0 | **PASS** |

### Banner Glyph IDs -- "New Reg." (Patch 4)

| Offset | Glyph Pair | Label | Status |
|--------|------------|-------|--------|
| 0x3C33F0 | N(46), e(69) | Ne | **PASS** |
| 0x3C3428 | w(87), _(0) | w_ | **PASS** |
| 0x3C3268 | R(50), e(69) | Re | **PASS** |
| 0x3C32A0 | g(71), .(14) | g. | **PASS** |

### NPC Names (Patch 3)

| Offset | Expected | Actual | Status |
|--------|----------|--------|--------|
| 0x3C93B0 | Emilia | Emilia | **PASS** |
| 0x3C93C0 | Lute | Lute | **PASS** |

### Player-Visible Strings (Patch 2)

| Offset | Expected | Actual | Status |
|--------|----------|--------|--------|
| 0x3F8240 | Continue loading! | Continue loading! | **PASS** |
| 0x3F8260 | No one can equip it. | No one can equip it. | **PASS** |

---

## 5. R39, R46, R47 Verification

| Resource | Type | English Glyphs | Japanese Glyphs | Status |
|----------|------|----------------|-----------------|--------|
| R39 (items) | 15 | 966 | 165 | **English** |
| R46 (skill desc) | 3 | 8,751 | 119 | **English** |
| R47 (misc) | 3 | 827 | 80 | **English** |

All three resources are predominantly English. Some Japanese glyphs remain
(likely for untranslated entries or special characters).

---

## 6. Resource Coverage

| Category | Count | Notes |
|----------|-------|-------|
| packdata_resources (in ISO) | 50 files | Includes type-01, type-02, type-03, type-15, type-20, type-44 |
| patched_type2 (NOT in ISO) | 124 files | Type-02 dialogue resources from build_v9.py |
| By type in ISO: type-01 (MSG) | 14 | R36-R49 range |
| By type in ISO: type-02 (dialogue) | 31 | Subset of full type-2 set |
| By type in ISO: type-03 | 2 | R46, R47 |
| By type in ISO: type-15 | 1 | R39 |
| By type in ISO: type-20 | 1 | R34 |
| By type in ISO: type-44 | 1 | R1272 font atlas |

### FINDING: 93 type-2 resources NOT in v24 ISO

The `build/patched_type2/` directory contains 124 patched type-2 resource files
(from build_v9.py), but only 31 of these made it into `build/packdata_resources/`
and thus into the ISO. The remaining 93 type-2 dialogue resources (R677, R690,
R712, R715, R726, R741, R750, R757, R769, R780, R785, R787, etc.) are NOT
included in v24.

**Root cause:** `build_full_english_v2.py` (used for v24) only processes type-01
MSG resources and a few manually-handled type-02 files. It does NOT copy files from
`build/patched_type2/` into `build/packdata_resources/` (that step is in
`build_v9.py` only). A merge step is needed before the PACKDATA rebuild.

---

## Summary

| Component | Status |
|-----------|--------|
| PACKDATA.DIG size | PASS (801 MB) |
| R38 labels (STR, gender, races, alignment) | PASS |
| R1272 font atlas (extended 642px) | PASS |
| EXE save slot names | PASS (all 6) |
| EXE banner glyphs (New Reg.) | PASS (all 4) |
| EXE NPC names (Emilia, Lute) | PASS |
| EXE player strings | PASS (all 2) |
| R39 item names | PASS (English) |
| R46/R47 skill descriptions | PASS (English) |
| Type-2 dialogue coverage | **PARTIAL** -- 31/124 in ISO |

**Overall: All specified patches are correctly applied. The main gap is 93 type-2
dialogue resources from build_v9.py that are not merged into the v24 build pipeline.**
