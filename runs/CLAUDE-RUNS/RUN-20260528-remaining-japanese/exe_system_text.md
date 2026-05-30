# EXE System Text Scan: Confirmation Dialogs, Error Messages, Config Labels

**Date:** 2026-05-28
**EXE:** `extracted/SLPM_653.78` (4,185,776 bytes)
**Scan ranges:**
- `0x3B0000`-`0x3C3000` (before menu structs)
- `0x3C5300`-`0x3C83C0` (between menu and chargen)
- `0x3C93A0`-`0x3DDC40` (large gap between chargen and font data)

**Method:** SJIS string scan + glyph ID cluster detection + FFFF-terminated string search + known-term glyph sequence search

---

## Executive Summary

**No new system text, confirmation dialogs, error messages, or config labels were found in the EXE.**

All three scan ranges contain only:
- Font infrastructure (ordering tables, width tables, sort tables, glyph cross-references)
- Rendering data (coordinate pairs, animation parameters, sprite positioning)
- Structural lookup tables (combinatorial index arrays, enum mappings)
- Name entry keyboard grids (hiragana/katakana input -- addressed separately if English name entry is needed)

The game's system UI text (save/load dialogs, yes/no prompts, config options, difficulty settings) is **not hardcoded in the EXE**. It is loaded from MSG resources in PACKDATA.DIG at runtime.

---

## Detailed Scan Results

### 1. SJIS Scan (All Three Ranges)

Only 2 SJIS hits found, both already classified as false positives:

| Offset | Decoded | Verdict |
|--------|---------|---------|
| `0x3DCFE8` | 囮劔劔 | MPEG decoder library data |
| `0x3DCFF0` | 囮劔劔 | MPEG decoder library data |

**No genuine SJIS system strings exist in these ranges.**

### 2. Glyph ID Cluster Scan

Scanned all three ranges for consecutive valid glyph IDs (3+ in a row). Found hundreds of clusters, all classified as:

| Category | Description | Example Locations |
|----------|-------------|-------------------|
| Font ordering table | Sequential glyph IDs for atlas layout | `0x3B3226`-`0x3B368A` |
| Width/spacing metadata | Paired glyph IDs with rendering config | `0x3B3690`-`0x3B3752` |
| UI label index arrays | Cross-reference tables for menu system | `0x3B376A`-`0x3B3838` |
| Sort order table | All kana in gojuuon order | `0x3B5FC0`-`0x3B6136` |
| Animation/sprite data | Coordinate + glyph ID tuples | `0x3B6140`-`0x3B7E00` |
| Name entry keyboards | Input grid positions | `0x3C5F00`-`0x3C6700` |
| Combinatorial pair tables | ID x ID lookup arrays | `0x3C6700`-`0x3C7A60` |
| Rendering parameter blocks | Repeated patterns with positioning data | `0x3C9400`-`0x3D0C00` |
| Sorting/ordering data | Permutation tables for various lists | `0x3D1200`-`0x3D1500` |

**None of these are readable text strings.** They are all rendering infrastructure, lookup tables, or UI layout data. The repeating patterns (e.g., every ASCII character paired with every other) confirm these are combinatorial data structures, not text.

### 3. FFFF-Terminated String Search

Found FFFF-terminated glyph sequences at:

| Offset | Content | Verdict |
|--------|---------|---------|
| `0x3C93AE` | Emilia (NPC name) | Already patched in patch_exe.py |
| `0x3C93C0` | Lute (NPC name) | Already patched in patch_exe.py |
| `0x3D0DA0`+ | Short 2-glyph entries | Structural index data, not text |
| `0x3D12B6`+ | ASCII character lists | Permutation/sorting tables |

**No system dialog text found in FFFF-terminated format.**

### 4. Known-Term Glyph Sequence Search

Searched full EXE for glyph ID sequences matching system terms:

| Term | Japanese | Glyph IDs Available | Found in EXE? |
|------|----------|---------------------|---------------|
| system | システム | ALL (8A01 8B01 9101 9F01) | **No** |
| title | タイトル | ALL (8E01 8001 9201 A701) | **No** |
| no | いいえ | ALL (7401 7401 7601) | **No** |
| save | セーブ | PARTIAL (missing ー, ブ) | N/A |
| load | ロード | PARTIAL (missing ー, ド) | N/A |
| yes | はい | PARTIAL (missing は) | N/A |
| confirm | 確認 | PARTIAL (both missing) | N/A |
| settings | 設定 | PARTIAL (both missing) | N/A |
| option | オプション | PARTIAL (missing プ, ョ) | N/A |
| cancel | キャンセル | PARTIAL (missing ャ) | N/A |

Even for terms where we had complete glyph ID sequences (system, title, no), **zero matches were found anywhere in the EXE**. This confirms these labels are stored in the MSG data, not the EXE.

---

## Already Patched (for reference)

The following EXE strings are already handled by `build/patch_exe.py`:

| # | Offset | Original | Patched To | Type |
|---|--------|----------|------------|------|
| 1 | `0x3FC720` | BUSIN0 (SJIS fullwidth) | "BUSIN 0" | Save card title |
| 2 | `0x3FC750` | BUSIN0 Data 1 (SJIS) | "BUSIN 0 Data 1" | Save slot 1 |
| 3 | `0x3FC770` | BUSIN0 Data 2 (SJIS) | "BUSIN 0 Data 2" | Save slot 2 |
| 4 | `0x3FC790` | BUSIN0 Data 3 (SJIS) | "BUSIN 0 Data 3" | Save slot 3 |
| 5 | `0x3F9370` | BUSIN0 Suspend (SJIS) | "BUSIN 0 Suspend" | Suspend save |
| 6 | `0x3F9678` | BUSIN0 (SJIS) | "BUSIN 0" | Busin 1 compat card |
| 7 | `0x3F8240` | Continue loading! (SJIS) | "Continue loading!" | Load screen msg |
| 8 | `0x3F8260` | No one can equip (SJIS) | "No one can equip it." | Equip error |
| 9 | `0x3C93B0` | Emilia (glyph IDs) | "Emilia" | NPC name |
| 10 | `0x3C93C0` | Lute (glyph IDs) | "Lute" | NPC name |

---

## Remaining Items (from prior scans, not new findings)

### Medium Priority
- **Name entry keyboards** (`0x3C5F00`-`0x3C6700`): Two keyboard grids (hiragana + katakana) for character name input. Only relevant if switching to English name entry.

### Low Priority  
- **Menu structs** (`0x3C3000`-`0x3C5300`): Already handled -- menu tile replacement done.
- **Chargen grid** (`0x3C83C0`-`0x3C93A0`): Already handled (R38).
- **Tab labels** (`0x3C9DA0`-`0x3C9DFC`): Already handled (Table 2E).

---

## Conclusion

**The EXE is clean of system/config text.** All player-visible system UI strings (save/load confirmations, yes/no prompts, config labels, difficulty settings, error messages) are stored in the MSG resources within PACKDATA.DIG, not hardcoded in the EXE binary.

The only EXE-hardcoded player-visible text was:
- Save card titles (6 strings) -- PATCHED
- Two gameplay messages (continue loading, equip error) -- PATCHED
- Two NPC names (Emilia, Lute) -- PATCHED
- Debug/TTY strings (12+ strings) -- not player-visible, no action needed

**No further EXE patches are needed for system/config text.**
