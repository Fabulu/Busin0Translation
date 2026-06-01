# Fix Banner: R39 Investigation and True Root Cause

**Date**: 2026-05-28

---

## 1. R39 Does NOT Contain the Banner

Searched the entire 26,624-byte R39 file (0039_type15.raw) for the glyph IDs
of the 4 banner kanji:

| Kanji | Glyph ID | Hex    | Found in R39? |
|-------|----------|--------|---------------|
| 新    | 498      | 0x01F2 | NO (4 false positives in non-glyph data) |
| 規    | 499      | 0x01F3 | NO |
| 登    | 491      | 0x01EB | NO |
| 録    | 492      | 0x01EC | NO (1 false positive) |

The glyph stream (bytes 632-2701) contains 97 FFFF-delimited messages,
none of which include these 4 glyph IDs. R39's data is spell/skill names
(katakana strings like スレイクラッシュ, ブレイクサイレンス), not menu labels.

Also searched for Shift-JIS and UTF-8 encodings of "新規登録" -- no match.

**Conclusion: R39 is irrelevant to the banner. The banner data is in the EXE.**

---

## 2. True Root Cause: EXE Patch 4 Patched the WRONG Field

### Record Structure (56 bytes each)

Each kanji label record in the EXE table at 0x3C3000-0x3C3FF8 has this layout:

```
Byte  0-1:  padding (0x0000)
Byte  2-3:  record ID (u16) -- groups related labels
Byte  4-7:  float f1 (always 1.0)
Byte  8-11: float f2 (position/size parameter)
Byte 12-15: float f3 (position/size parameter)
Byte 16-19: float f4
Byte 20-23: float f5 (always ~0.05)
Byte 24-47: R1272 tile ID references (6 pairs of u16) -- NOT used for banner
Byte 48-49: padding (0x0000)
Byte 50-51: GLYPH MAP ID (u16) -- THIS is what the banner renderer reads
Byte 52-53: sequential index (u16)
Byte 54-55: padding (0x0000)
```

### What Patch 4 Changed (WRONG)

Patch 4 replaced u16 values at **bytes 24-47** (R1272 tile IDs):

| Record | Offset   | Old Tiles | New Tiles    | Old Glyph@50 | New Glyph@50 |
|--------|----------|-----------|-------------|-------------|-------------|
| 新     | 0x3C33F0 | 719, 720  | 46(N), 69(e) | **498 (unchanged)** | **498 (unchanged)** |
| 規     | 0x3C3428 | 721, 722  | 87(w), 0(sp) | **499 (unchanged)** | **499 (unchanged)** |
| 登     | 0x3C3268 | 705, 706  | 50(R), 69(e) | **491 (unchanged)** | **491 (unchanged)** |
| 録     | 0x3C32A0 | 707, 708  | 71(g), 14(.) | **492 (unchanged)** | **492 (unchanged)** |

The banner renderer reads the **glyph map ID at byte 50**, NOT the R1272 tile IDs
at bytes 24-47. The tile IDs control a different rendering path (sidebar labels on
other screens). That's why the EXE patch is verified correct in RAM but the banner
still shows Japanese.

### Evidence

From check_banner_ram.md:
- Patched tile IDs (46, 69, 87, 71) are confirmed in RAM at correct VAs
- But Japanese atlas positions for those tile IDs are BLANK (0 non-white pixels)
- If banner read from tile IDs, it would show blank space, not kanji
- Banner shows full kanji -> it reads from glyph map ID field instead

---

## 3. The Fix: Patch Byte 50 (Glyph Map ID)

Replace the glyph map IDs at byte 50-51 in each banner record:

| Record | EXE Offset | Byte 50 Offset | Old Value | New Value | Displays |
|--------|-----------|----------------|-----------|-----------|----------|
| 新     | 0x3C33F0  | 0x3C3422       | 498 (新)  | 46 (n)    | n        |
| 規     | 0x3C3428  | 0x3C345A       | 499 (規)  | 37 (e)    | e        |
| 登     | 0x3C3268  | 0x3C329A       | 491 (登)  | 55 (w)    | w        |
| 録     | 0x3C32A0  | 0x3C32D2       | 492 (録)  | 0 (space) | (space)  |

Display order (based on record IDs and position floats):
- rec_id 624: 新 -> n
- rec_id 625: 規 -> e
- rec_id 618: 登 -> w
- rec_id 618: 録 -> (space)

Expected banner: **"new "** (lowercase, 4 characters)

### ASCII Glyph IDs Available

Only lowercase a-z is available in the glyph map (IDs 33-58):

| Char | ID  | Char | ID  | Char | ID  |
|------|-----|------|-----|------|-----|
| a    | 33  | j    | 42  | s    | 51  |
| b    | 34  | k    | 43  | t    | 52  |
| c    | 35  | l    | 44  | u    | 53  |
| d    | 36  | m    | 45  | v    | 54  |
| e    | 37  | n    | 46  | w    | 55  |
| f    | 38  | o    | 47  | x    | 56  |
| g    | 39  | p    | 48  | y    | 57  |
| h    | 40  | q    | 49  | z    | 58  |
| i    | 41  | r    | 50  | (sp) | 0   |

### Alternative Texts (4 chars max)

| Text | Glyph IDs         | Notes |
|------|--------------------|-------|
| new  | 46, 37, 55, 0     | Best option -- clear meaning |
| reg  | 50, 37, 39, 0     | Abbreviation of "register" |
| join | 42, 47, 41, 46    | Alternative meaning |
| make | 45, 33, 43, 37    | "make character" |

---

## 4. Implementation

Add to `build/patch_exe.py` as **PATCH 5** (or modify Patch 4):

```python
# PATCH 5: Banner Glyph Map IDs (byte 50 of each record)
# The banner renderer reads glyph map ID at byte 50, NOT R1272 tiles.
banner_glyph_patches = [
    (0x3C33F0, 498, 46, "新 -> n"),  # record offset, old_glyph, new_glyph, label
    (0x3C3428, 499, 37, "規 -> e"),
    (0x3C3268, 491, 55, "登 -> w"),
    (0x3C32A0, 492,  0, "録 -> (space)"),
]

for rec_off, old_glyph, new_glyph, label in banner_glyph_patches:
    off = rec_off + 50  # byte 50 in the 56-byte record
    val = struct.unpack_from("<H", data, off)[0]
    if val == old_glyph:
        struct.pack_into("<H", data, off, new_glyph)
        print(f"  OK   0x{off:06X}: {label}")
        patched_count += 1
    elif val == new_glyph:
        print(f"  SKIP 0x{off:06X}: {label} (already patched)")
    else:
        print(f"  WARN 0x{off:06X}: {label} (expected {old_glyph}, got {val})")
```

---

## 5. Risks and Considerations

1. **Display order uncertainty**: The 4 characters may not render in the order
   新->規->登->録 (left to right). The actual order depends on the game's
   rendering code which uses rec_id grouping and float parameters. If the order
   is wrong, the letters will appear scrambled (e.g., "wen " instead of "new ").
   **Mitigation**: Test in-game after patching.

2. **Character size**: Each glyph occupies a full kanji cell (~24x24 in R1188).
   Latin letters will look very large compared to normal game text. The banner
   may look odd with oversized lowercase letters.
   **Mitigation**: This is the same approach used by the original game for all
   its kanji labels -- the scaling float (f2, f3) should handle sizing.

3. **Shared glyph IDs**: Glyph IDs 491-499 are used in other records in the same
   table (e.g., 登 appears in record 0x3C3268 for one screen, but also appears
   as a kanji in message text throughout the game). Changing byte 50 ONLY affects
   this specific record, not the glyph map globally.

4. **PCSX2 texture replacement still works**: The existing PCSX2 overlay
   (`a2d3fce36c8c719d-e786e0650b284c64-r120x24-00002214.png` = "New Character")
   will override whatever the patched EXE renders. For emulator users, the banner
   will show "New Character" regardless. The byte-50 patch is for non-emulator
   (real hardware / other emulators without texture replacement).

---

## 6. Summary

| Question | Answer |
|----------|--------|
| Is the banner in R39? | **NO** -- R39 has spell/skill names only |
| Is the banner in R37/R38? | **NO** -- confirmed by glyph ID search |
| Is the banner in R1188? | **Indirectly** -- R1188 has the kanji glyphs, game composes them |
| What controls the banner? | **EXE byte 50** of records at 0x3C3268/32A0/33F0/3428 |
| Why did Patch 4 fail? | Patched bytes 24-47 (R1272 tiles), not byte 50 (glyph map ID) |
| Fix? | Change byte 50 from kanji glyph IDs to ASCII glyph IDs |
