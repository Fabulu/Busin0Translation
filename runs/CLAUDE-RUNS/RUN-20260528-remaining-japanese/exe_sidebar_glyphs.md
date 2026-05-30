# EXE Chargen Sidebar Labels & Banner: Exact Locations and Replacement Strategy

**Date**: 2026-05-28
**Analyst**: Claude Opus 4.6
**EXE**: `extracted/SLPM_653.78` (4,185,776 bytes)
**ELF mapping**: vaddr = file_offset - 0x80 + 0x100000

---

## 1. The 56-Byte Menu Struct Table

A table of 56-byte records starts at **file offset 0x3C3000** (VA 0x004C2F80).
Each record represents ONE kanji glyph used in menus, sidebars, and labels.

### Record layout (56 bytes)

| Offset | Size | Field | Description |
|--------|------|-------|-------------|
| +00 | 2 | padding | Always 0 |
| +02 | 2 | type_id | Record type/ID (~glyph_id + 125) |
| +04 | 4 | float | X scale (typically 1.0) |
| +08 | 4 | float | Y position / dimension |
| +12 | 4 | float | Parameter 3 (scale/size) |
| +16 | 4 | float | Parameter 4 |
| +20 | 4 | float | Parameter 5 |
| +24 | 4 | [flag, tile_normal_A] | R1272 tile index, normal state, half A |
| +28 | 4 | [flag, tile_normal_B] | R1272 tile index, normal state, half B |
| +32 | 4 | [flag, tile_hover_A] | R1272 tile index, hover state, half A |
| +36 | 4 | [flag, tile_hover_B] | R1272 tile index, hover state, half B |
| +40 | 4 | [flag, tile_selected_A] | R1272 tile index, selected state, half A |
| +44 | 4 | [flag, tile_selected_B] | R1272 tile index, selected state, half B |
| +48 | 4 | [padding, glyph_id] | MSG system glyph ID (upper 16 bits) |
| +52 | 4 | [index, padding] | R38 MSG index or grouping (lower 16 bits) |

**Key mapping**: `record_number = glyph_id - 480`, `record_address = 0x3C3000 + record_number * 56`

Each glyph uses **two R1272 tile slots** (tile_A and tile_B), likely representing
left-half and right-half of the 24x12 kanji rendering area (each tile is 12x12).

---

## 2. Sidebar Labels: Exact Records

The chargen sidebar shows four 2-kanji labels. Each label uses **two consecutive
struct records** (one per kanji), for a total of **four R1272 tiles** per label.

### 2.1 Gender: 性別

| Component | Rec | EXE Offset | Glyph ID | Kanji | R1272 Tiles |
|-----------|-----|------------|----------|-------|-------------|
| 性 (sei) | 31 | **0x3C36C8** | 511 | 性 | 745, 746 |
| 別 (betsu) | 32 | **0x3C3700** | 512 | 別 | 747, 748 |

R38 MSG 11 glyph stream: `[511, 512]` -> translated to `"gender"`

### 2.2 Race: 種族

| Component | Rec | EXE Offset | Glyph ID | Kanji | R1272 Tiles |
|-----------|-----|------------|----------|-------|-------------|
| 種 (shu) | 33 | **0x3C3738** | 513 | 種 | 749, 750 |
| 族 (zoku) | 34 | **0x3C3770** | 514 | 族 | 751, 752 |

R38 MSG 10 glyph stream: `[513, 514]` -> translated to `"race"`

### 2.3 Alignment: 属性

| Component | Rec | EXE Offset | Glyph ID | Kanji | R1272 Tiles |
|-----------|-----|------------|----------|-------|-------------|
| 属 (zoku) | 35 | **0x3C37A8** | 515 | 属 | 753, 754 |
| 性 (sei) | 31 | **0x3C36C8** | 511 | 性 | 745, 746 |

**NOTE**: Reuses rec31 from Gender. R38 MSG 12: `[515, 511]` -> `"alignment"`

### 2.4 Class: 職業

| Component | Rec | EXE Offset | Glyph ID | Kanji | R1272 Tiles |
|-----------|-----|------------|----------|-------|-------------|
| 職 (shoku) | 24 | **0x3C3540** | 504 | 職 | 731, 732 |
| 業 (gyou) | 37 | **0x3C3818** | 517 | 業 | 757, 758 |

**NOTE**: Records are NOT consecutive (rec24 and rec37). R38 MSG 13: `[504, 517]` -> `"class"`

### 2.5 Personality: 性格 (confirmation screen only)

| Component | Rec | EXE Offset | Glyph ID | Kanji | R1272 Tiles |
|-----------|-----|------------|----------|-------|-------------|
| 性 (sei) | 31 | **0x3C36C8** | 511 | 性 | 745, 746 |
| 格 (kaku) | 36 | **0x3C37E0** | 516 | 格* | 755, 756 |

*Glyph map maps 516 to 性 but the actual R1272 tile shows 格.

R38 MSG 14: `[511, 516]` -> `"personality"`

---

## 3. Title Banner: 新規登録 (New Registration)

The red banner uses **four struct records** (one per kanji):

| Component | Rec | EXE Offset | Glyph ID | Kanji | R1272 Tiles |
|-----------|-----|------------|----------|-------|-------------|
| 新 (shin) | 18 | **0x3C33F0** | 498 | 新 | 719, 720 |
| 規 (ki) | 19 | **0x3C3428** | 499 | 規* | 721, 722 |
| 登 (tou) | 11 | **0x3C3268** | 491 | 登 | 705, 706 |
| 録 (roku) | 12 | **0x3C32A0** | 492 | 録 | 707, 708 |

*Glyph map maps 499 to 兵 but the actual R1272 tile shows 規.

**Records are NOT consecutive** (rec18, rec19, rec11, rec12).

---

## 4. Rendering Pipeline Analysis

### Confirmed: Sidebar goes through R38 MSG system

Disassembly of `chargen_render_A` at VA 0x2F1090 (file 0x1F1110) confirms:
- The function iterates a linked list of label descriptors
- Each descriptor has `{next_ptr, type, R38_msg_index, update_flag}` at offsets 0/4/6/8
- It loads the R38 MSG index via `lhu r5, 6(r17)` and calls `jal 0x00301E90`
- The generic text system then renders glyph IDs from R38 using R1272 font atlas

### Built R38 resource verification

The built R38 at `build/packdata_resources/0038_type01.raw` (offset table format:
4-byte entries with BE uint16 offset + 2 padding bytes, 47 entries) contains:

```
Original R38:                        Built R38:
MSG  8: 幸運度 (lck)           ->    [76,67,75]              = LCK       CORRECT
MSG  9: 名前 (name)            ->    [78,65,77,69]           = NAME      CORRECT
MSG 10: レベル (level)          ->    [76,69,86,69,76]        = LEVEL     CORRECT
MSG 11: 種族 (race)             ->    [82,65,67,69]           = RACE      CORRECT
MSG 12: 性別 (gender)           ->    [71,69,78,68,69,82]     = GENDER    CORRECT
MSG 13: 属性 (alignment)        ->    [65,76,73,71,78,...]    = ALIGNMENT CORRECT
MSG 14: 職業 (class)            ->    [67,76,65,83,83]        = CLASS     CORRECT
MSG 15: 性格 (personality)      ->    [80,69,82,83,79,...]    = PERSONALITY CORRECT
```

Note: the chargen_deep analysis document used FFFE-group numbering (where MSG 10=race),
while the R38 binary offset table uses sequential numbering (MSG 11=race). Both are
correct and consistent.

All translations use **uppercase ASCII glyph IDs** (A=65..Z=90) which map to
R1272 slots 65-90 containing lowercase letter bitmaps.

### Glyph ID mapping

| Range | Glyph Map | R1272 Atlas Slot | Visual |
|-------|-----------|-----------------|--------|
| 33-58 | a-z (lowercase) | Uppercase A-Z bitmaps | Shows uppercase |
| 65-90 | UNMAPPED | Lowercase a-z bitmaps | Shows lowercase |

### Why sidebar might still show Japanese in save states

Since the R38 translations are correct in the built resource, the remaining
possibilities are:

1. **Save states from older build**: The save states (May 30) may pre-date the
   latest R38 resource injection into the ISO
2. **R38 not injected into ISO**: The build pipeline may not be injecting the
   patched R38 into PACKDATA.DIG correctly
3. **The sidebar uses a different R38 MSG numbering**: The chargen code might
   request different MSG indices than expected for the sidebar labels
4. **Glyph IDs 65-90 not rendering**: The text system may reject UNMAPPED glyph
   IDs and fall back to showing the struct record tiles instead

---

## 5. Tile Reuse Conflict

**CRITICAL**: Glyph 511 (性, rec31, tiles 745-746) is shared across THREE labels:

- 性**別** (gender) -- 性 is the first kanji
- 属**性** (alignment) -- 性 is the second kanji  
- **性**格 (personality) -- 性 is the first kanji

If we modify R1272 tiles 745-746 to show English text, the same text will appear
in ALL three contexts. There is no way to show different text per context via
bitmap replacement alone.

---

## 6. Replacement Strategy

### Sidebar labels: ALREADY TRANSLATED via R38 (verify ISO injection)

The chargen sidebar labels go through the R38 MSG rendering path (confirmed by
disassembly). The built R38 resource contains correct English translations:

- MSG 11: RACE (for 種族)
- MSG 12: GENDER (for 性別)
- MSG 13: ALIGNMENT (for 属性)
- MSG 14: CLASS (for 職業)

**If the sidebar still shows Japanese**, the issue is one of:
1. R38 not injected into the ISO correctly
2. The chargen code uses different MSG indices for sidebar vs main area
3. Uppercase glyph IDs (65-90) not resolving to valid R1272 tiles at runtime

**Recommended action**: Test with the latest ISO build. If still Japanese, attach
PCSX2 debugger to trace which R38 MSG index the chargen code requests for the
sidebar labels.

### Banner (新規登録): NOT in R38 -- requires bitmap replacement

The 新規登録 banner text is **NOT in any MSG resource** (confirmed by searching
R37 and R38 for glyph sequence 498,499,491,492). The banner is rendered directly
from R1272 tile bitmaps referenced by the struct records.

**Required fix**: Replace R1272 bitmap tiles at these positions:

| Tile Slots | Current | Replace With |
|-----------|---------|-------------|
| 705, 706 | 登 bitmap | "re" or "reg" |
| 707, 708 | 録 bitmap | "ist" or "er" |
| 719, 720 | 新 bitmap | "ne" or "new" |
| 721, 722 | 規 bitmap | "w " or " re" |

**Problem**: These 4 tile pairs must spell out "New Registration" or similar across
8 tile slots (each 12x12 pixels). At 12px per tile, 8 tiles = 96px total, enough
for ~10-12 characters in a narrow font.

**Best approach**: Update `data/menu_labels.csv` rows 11, 12, 18, 19 to form a
coherent banner label when read left-to-right. The rendering order is determined
by the chargen code (which records it draws in which order).

### menu_labels.csv errors

The CSV has **incorrect Japanese labels** for many entries because it was written
treating each struct record as a 2-kanji label. Each record is actually ONE kanji.

| CSV Row | CSV Japanese | CSV English | Actual EXE Glyph | Correct Kanji |
|---------|-------------|-------------|-----------------|---------------|
| 11 | 現員 | party | gid=491 | 登 |
| 12 | 選択 | select | gid=492 | 録 |
| 18 | 幸運 | luck | gid=498 | 新 |
| 19 | 獲得 | obtain | gid=499 | 規 |
| 24 | 転職 | reclass | gid=504 | 職 |
| 31 | 探索 | search | gid=511 | 性 |
| 32 | 操作 | handle | gid=512 | 別 |
| 33 | 種族 | race | gid=513 | 種 |
| 34 | 器用 | dex | gid=514 | 族 |
| 35 | 条件 | cond | gid=515 | 属 |
| 36 | 性格 | align | gid=516 | 格 |
| 37 | 職業 | class | gid=517 | 業 |
| 38 | 性別 | gender | gid=518 | 男 |

NOTE: If the sidebar IS rendered through R38 MSGs (not the struct tile path),
then these CSV entries only matter for OTHER contexts where the same tiles appear
(e.g., the struct-based rendering in non-chargen menus). The CSV should still be
fixed to show correct English for those other contexts.

---

## 7. Complete R1272 Tile Map for Affected Records

| Tile ID | Record | Glyph | Used In | CSV English | Status |
|---------|--------|-------|---------|-------------|--------|
| 705, 706 | rec11 | 登 | Banner (登録) | "party" | WRONG CSV |
| 707, 708 | rec12 | 録 | Banner (登録) | "select" | WRONG CSV |
| 719, 720 | rec18 | 新 | Banner (新規) | "luck" | WRONG CSV |
| 721, 722 | rec19 | 規 | Banner (新規) | "obtain" | WRONG CSV |
| 731, 732 | rec24 | 職 | Sidebar (職業) | "reclass" | WRONG CSV |
| 745, 746 | rec31 | 性 | Sidebar (性別/属性/性格) | "search" | WRONG CSV |
| 747, 748 | rec32 | 別 | Sidebar (性別) | "handle" | WRONG CSV |
| 749, 750 | rec33 | 種 | Sidebar (種族) | "race" | Partially right |
| 751, 752 | rec34 | 族 | Sidebar (種族) | "dex" | WRONG CSV |
| 753, 754 | rec35 | 属 | Sidebar (属性) | "cond" | WRONG CSV |
| 755, 756 | rec36 | 格 | Sidebar (性格) | "align" | WRONG CSV |
| 757, 758 | rec37 | 業 | Sidebar (職業) | "class" | Partially right |

---

## 8. Recommended Next Steps

### Priority 1: Verify sidebar rendering with latest ISO
1. Build latest ISO with current R38 translations
2. Navigate to chargen screen in PCSX2
3. Check if sidebar labels now show English (RACE/GENDER/ALIGNMENT/CLASS)
4. If still Japanese: attach PCSX2 debugger to trace the R38 MSG index lookups

### Priority 2: Fix 新規登録 banner
1. Determine the rendering ORDER of banner records (新=rec18, 規=rec19, 登=rec11, 録=rec12)
2. Update `data/menu_labels.csv` rows 11, 12, 18, 19 with correct banner text fragments
3. Run font atlas build pipeline to render English text into R1272 tiles 705-722
4. Inject updated R1272 into ISO and verify

### Priority 3: Fix menu_labels.csv
1. Correct the wrong Japanese/English labels for rows 11, 12, 18, 19, 24, 31-38
2. Each row represents ONE kanji, not a 2-kanji label
3. Consider which menus (besides chargen) use these tiles for correct English text
4. For glyph 511 (性, tiles 745-746), note it appears in 3 sidebar labels
   (gender/alignment/personality) -- the R38 path renders different text per context,
   but the CSV tile replacement can only show one thing

### Priority 4: Address glyph ID range issue
1. R38 translations use uppercase ASCII IDs (65-90) -- verify these resolve to
   valid R1272 tiles at runtime
2. If the text system rejects unmapped glyph IDs, either:
   a. Add entries 65-90 to msg_glyph_map.json
   b. Change the translation pipeline to use lowercase IDs (33-58) instead
