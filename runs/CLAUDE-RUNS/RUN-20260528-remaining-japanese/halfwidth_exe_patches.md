# Half-Width EXE Patches: Complete Byte-Level Specification

## CRITICAL CORRECTION FROM PREVIOUS ANALYSIS

The previous analysis (`analysis_text_renderer.md`) **misidentified the +12 sites** at VA 0x303E70, 0x303EF4, and 0x305BF8 as "pixel advances." Disassembly with full context proves they are **12-byte glyph slot STRUCT STRIDES** -- they step through an array of 12-byte-per-glyph data structures. These must NOT be changed.

The actual glyph pixel width is **24 pixels** (not 12), computed via `index * 3 * 8` (sll by 1, addu, sll by 3). To halve the glyph advance to 12px, the final `sll by 3` must become `sll by 2`.

---

## Architecture Summary

```
Glyph Slot Array:  12 bytes per slot (struct stride, NEVER CHANGE)
  +0x00: resource handle (4 bytes)
  +0x04: attribute/Y data (2 bytes)
  +0x06: X scroll position (2 bytes) -- scroll-reveal counter, starts at 128
  +0x08: additional render data (4 bytes)

Screen X position: glyph_index * 24 pixels (computed as index * 3 << 3)
  For half-width: glyph_index * 12 pixels (computed as index * 3 << 2)

Centering formula (mode 3): X_offset = 224 - (char_count * 24)
  For half-width: X_offset = 224 - (char_count * 12)
```

---

## PATCH GROUP A: Pixel Advance (*24 -> *12)

These sites compute `glyph_index * 3 * 8` for screen X positioning. Change the final `sll $reg, $reg, 3` to `sll $reg, $reg, 2` to get `glyph_index * 3 * 4 = *12`.

MIPS encoding: `sll $rd, $rt, sa` = `000000 00000 ttttt ddddd sssss 000000`
- `sll by 3`: sa=3, bits 10-6 = 00011
- `sll by 2`: sa=2, bits 10-6 = 00010

The change is: byte at file_offset+1 changes from `C0` to `80` (shift amount field).
Wait -- let me verify this precisely.

### Encoding verification

`sll $a0, $a0, 3` = `000420C0`:
  - Byte 0: `C0` (func=0x00, sa bits 0-1 = 11 in bits 7-6)
  - Byte 1: `20` (sa bits 2-4 = 000, rd bits 0-2 = 100)
  - Byte 2: `04` (rd bits 3-4 = 00, rt = 00100)
  - Byte 3: `00` (opcode + rt upper)

`sll $a0, $a0, 2` = `00042080`:
  - Change byte 0 from `C0` to `80`
  - All other bytes unchanged

`sll $v0, $v0, 3` = `000210C0`:
  - `sll $v0, $v0, 2` = `00021080`
  - Change byte 0 from `C0` to `80`

`sll $v1, $a1, 3` = `000518C0`:
  - `sll $v1, $a1, 2` = `00051880`
  - Change byte 0 from `C0` to `80`

### Patch Sites

| # | VA | File Offset | Current Bytes | Patched Bytes | Instruction | Context |
|---|-----|------------|---------------|---------------|-------------|---------|
| A1 | 0x305990 | 0x205A10 | `C0 20 04 00` | `80 20 04 00` | `sll $a0,$a0,3` -> `sll $a0,$a0,2` | Mode-3 centering: `224 - count*24` -> `224 - count*12` |
| A2 | 0x3061BC | 0x20623C | `C0 10 02 00` | `80 10 02 00` | `sll $v0,$v0,3` -> `sll $v0,$v0,2` | Glyph X position calculation |
| A3 | 0x306EF4 | 0x206F74 | `C0 10 02 00` | `80 10 02 00` | `sll $v0,$v0,3` -> `sll $v0,$v0,2` | Glyph X position calculation (second render path) |
| A4 | 0x307C28 | 0x207CA8 | `C0 10 02 00` | `80 10 02 00` | `sll $v0,$v0,3` -> `sll $v0,$v0,2` | Glyph X position (scroll-reveal computation) |
| A5 | 0x30836C | 0x2083EC | `C0 20 04 00` | `80 20 04 00` | `sll $a0,$a0,3` -> `sll $a0,$a0,2` | Glyph X position (line layout) |
| A6 | 0x308974 | 0x2089F4 | `C0 10 02 00` | `80 10 02 00` | `sll $v0,$v0,3` -> `sll $v0,$v0,2` | Glyph X position (alternate path) |

### Additional *24 Sites Requiring Analysis

| # | VA | File Offset | Current Bytes | Instruction | Context | Action |
|---|-----|------------|---------------|-------------|---------|--------|
| A7 | 0x303BC4 | 0x203C44 | `C0 18 05 00` | `sll $v1,$a1,3` | Layout engine: `$a1` was already *3, this makes *24. Used with FPU positioning. | PATCH to `sll $v1,$a1,2` -> `80 18 05 00` |
| A8 | 0x306188 | 0x206208 | `C0 10 02 00` | `sll $v0,$v0,3` | After *3 + multiply instruction. Render coordinate computation. | PATCH to `sll $v0,$v0,2` -> `80 10 02 00` |
| A9 | 0x306ED4 | 0x206F54 | `C0 10 02 00` | `sll $v0,$v0,3` | After *3 with FPU context. Second render coordinate path. | PATCH to `sll $v0,$v0,2` -> `80 10 02 00` |

### Sites NOT to Patch (Y-centering, not X)

| VA | File Offset | Instruction | Reason |
|-----|------------|-------------|--------|
| 0x305A00 | 0x205A80 | `sll $a0,$a0,3` | Mode-3 Y-centering: `192 - line_count*24`. This is LINE HEIGHT, not glyph width. Leave unchanged. |

---

## PATCH GROUP B: Constant -24 -> -12

The value -24 appears where a single character width is subtracted (e.g., adjusting for off-by-one in positioning).

| # | VA | File Offset | Current Bytes | Patched Bytes | Instruction | Context |
|---|-----|------------|---------------|---------------|-------------|---------|
| B1 | 0x303BC8 | 0x203C48 | `E8 FF 42 24` | `F4 FF 42 24` | `addiu $v0,$v0,-24` -> `addiu $v0,$v0,-12` | Layout engine: subtract one glyph width |
| B2 | 0x307D78 | 0x207DF8 | `E8 FF 42 24` | `F4 FF 42 24` | `addiu $v0,$v0,-24` -> `addiu $v0,$v0,-12` | Render: subtract one glyph width |

-12 in 16-bit signed = 0xFFF4

---

## PATCH GROUP C: Mode-2 Centering (*12 -> *6)

At VA 0x305CC4-0x305CD4, mode-2 centering computes `glyph_count * 12 - 184`:
```
  sll $v1, $a0, 1       ; v1 = count * 2
  addu $v1, $v1, $a0    ; v1 = count * 3
  sll $v1, $v1, 2       ; v1 = count * 12
  addiu $v1, $v1, -184  ; centering offset
```

For half-width (6px per glyph): need `count * 6 - 92`.
Change `sll $v1,$v1,2` to `sll $v1,$v1,1` and `-184` to `-92`.

| # | VA | File Offset | Current Bytes | Patched Bytes | Instruction | Context |
|---|-----|------------|---------------|---------------|-------------|---------|
| C1 | 0x305CCC | 0x205D4C | `80 18 03 00` | `40 18 03 00` | `sll $v1,$v1,2` -> `sll $v1,$v1,1` | *12 -> *6 centering multiply |
| C2 | 0x305CD0 | 0x205D50 | `48 FF 63 24` | `A4 FF 63 24` | `addiu $v1,$v1,-184` -> `addiu $v1,$v1,-92` | Centering constant halved |

-92 in 16-bit signed = 0xFFA4

---

## PATCH GROUP D: X-Position Scroll Clamp (NOT NEEDED for basic half-width)

The scroll clamp at VA 0x303E28 (`slti $at, $a0, 129`) limits the X scroll counter to 128. This is a scroll-reveal animation counter, NOT a pixel position. Each frame the counter decrements by 4 (or increments by 4), counting down from 128 to 0 as text scrolls into view.

**Since the struct stride remains 12 bytes and the scroll-reveal mechanism is independent of pixel width, this clamp does NOT need to change for the half-width patch.**

If you want text to scroll in faster (appropriate since half-width means more chars), you could reduce it, but it is NOT required for correctness.

### Values confirmed NOT to change:
| VA | File Offset | Instruction | Reason |
|-----|------------|-------------|--------|
| 0x303DD4 | 0x203E54 | `addiu $a1,$zero,128` | Scroll init value |
| 0x303E28 | 0x203EA8 | `slti $at,$a0,129` | Scroll clamp check |
| 0x303ECC | 0x203F4C | `addiu $a0,$zero,128` | Init loop clamp value |

---

## PATCH GROUP E: Display Box Width (OPTIONAL)

The 224-pixel box width at VA 0x305980 is used ONLY for mode-3 centering. Regular dialogue does not use this constant. With half-width glyphs, the centering formula `224 - count*12` will work correctly for strings up to 18 chars. For longer strings the offset goes negative, which may cause left-alignment (which is fine for dialogue).

**No change needed.** The 224px box width is a physical display area constraint, not a per-glyph parameter.

---

## SITES CONFIRMED NOT TO PATCH

### 12-byte Glyph Slot Struct Strides (3 sites)

These step through the 12-byte glyph slot array. The struct layout is fixed at 12 bytes regardless of pixel width.

| VA | File Offset | Encoding | Instruction | Context |
|-----|------------|----------|-------------|---------|
| 0x303E70 | 0x203EF0 | `2442000C` | `addiu $v0,$v0,12` | Scroll/animate loop: iterates glyph slots |
| 0x303EF4 | 0x203F74 | `24C6000C` | `addiu $a2,$a2,12` | Init loop: writes X=128 to each slot's +6 field |
| 0x305BF8 | 0x205C78 | `2484000C` | `addiu $a0,$a0,12` | Clear loop: zeros fields +2/+4/+6/+8/+10 of each slot |

### 12-byte Resource Table Strides (11 sites)

These iterate through resource handle arrays at VA 0x4CBC50/0x4CBC80, spaced 12 bytes apart.

| VA | File Offset | Encoding | Instruction |
|-----|------------|----------|-------------|
| 0x30CEFC | 0x20CF7C | `2610000C` | `addiu $s0,$s0,12` |
| 0x30CF2C | 0x20CFAC | `2631000C` | `addiu $s1,$s1,12` |
| 0x30CF9C | 0x20D01C | `2631000C` | `addiu $s1,$s1,12` |
| 0x30CFF4 | 0x20D074 | `2631000C` | `addiu $s1,$s1,12` |
| 0x30D0D8 | 0x20D158 | `2652000C` | `addiu $s2,$s2,12` |
| 0x30D0EC | 0x20D16C | `2631000C` | `addiu $s1,$s1,12` |
| 0x30D160 | 0x20D1E0 | `2652000C` | `addiu $s2,$s2,12` |
| 0x30D174 | 0x20D1F4 | `2631000C` | `addiu $s1,$s1,12` |
| 0x30DA50 | 0x20DAD0 | `2652000C` | `addiu $s2,$s2,12` |
| 0x30DA68 | 0x20DAE8 | `2631000C` | `addiu $s1,$s1,12` |
| 0x30DB1C | 0x20DB9C | `2610000C` | `addiu $s0,$s0,12` |

### Font Metrics Table Init (3 sites)

These pass the value 12 as $a3 to a font metrics computation function -- one of 13 size variants (8-20). Not a pixel advance.

| VA | File Offset | Encoding | Instruction |
|-----|------------|----------|-------------|
| 0x30ECA8 | 0x20ED28 | `2407000C` | `addiu $a3,$zero,12` |
| 0x30FC84 | 0x20FD04 | `2407000C` | `addiu $a3,$zero,12` |
| 0x30FEB4 | 0x20FF34 | `2407000C` | `addiu $a3,$zero,12` |

### *12 Glyph Slot Array Indexing (many sites)

Sites computing `index * 3 * 4 = index * 12` are byte offsets into the 12-byte glyph slot array. These are struct indexing, NOT pixel calculations. Examples: VA 0x3077D0, 0x30781C, 0x307920, 0x307FBC, 0x308314, 0x3083A8, 0x308464, 0x3084AC, etc.

### Y-Line Spacing (+24 increments)

Sites at VA 0x3079DC, 0x308040, 0x308CB0, 0x308D7C, 0x3097A4 add 24 to Y-position coordinates for line spacing. These are vertical, not horizontal. Do NOT change.

---

## COMPLETE PATCH SUMMARY

**Total patches: 13 bytes changed across 11 sites**

| Patch | File Offset | Byte Position | Old | New | Purpose |
|-------|-------------|---------------|-----|-----|---------|
| A1 | 0x205A10 | byte 0 | `C0` | `80` | sll 3->2: centering *24->*12 |
| A2 | 0x20623C | byte 0 | `C0` | `80` | sll 3->2: X position *24->*12 |
| A3 | 0x206F74 | byte 0 | `C0` | `80` | sll 3->2: X position *24->*12 |
| A4 | 0x207CA8 | byte 0 | `C0` | `80` | sll 3->2: X position *24->*12 |
| A5 | 0x2083EC | byte 0 | `C0` | `80` | sll 3->2: X position *24->*12 |
| A6 | 0x2089F4 | byte 0 | `C0` | `80` | sll 3->2: X position *24->*12 |
| A7 | 0x203C44 | byte 0 | `C0` | `80` | sll 3->2: layout *24->*12 |
| A8 | 0x206208 | byte 0 | `C0` | `80` | sll 3->2: render coord *24->*12 |
| A9 | 0x206F54 | byte 0 | `C0` | `80` | sll 3->2: render coord *24->*12 |
| B1 | 0x203C48 | byte 0 | `E8` | `F4` | -24 -> -12 (one glyph width) |
| B2 | 0x207DF8 | byte 0 | `E8` | `F4` | -24 -> -12 (one glyph width) |
| C1 | 0x205D4C | byte 0 | `80` | `40` | sll 2->1: mode-2 centering *12->*6 |
| C2 | 0x205D50 | byte 0 | `48` | `A4` | -184 -> -92 (centering constant) |

---

## RISK ASSESSMENT

**LOW RISK patches (Group A, B):** These are clearly pixel-position calculations. Changing the shift amount from 3 to 2 halves the X spacing. If the font atlas has 12px-wide glyphs rendered in 24px cells, this will produce correct spacing.

**MEDIUM RISK patches (Group C):** Mode-2 centering. The constants -184 and *12 are specific to a display mode. If mode-2 is used for Japanese-only text (like names), this could misalign. Verify by testing mode-2 displays.

**Prerequisites:**
1. Font atlas must contain half-width (12px or 6px) glyphs. If glyphs are still rendered at 24px width in the texture, they will overlap.
2. The font tile size in the GS texture upload must match. Currently each glyph tile is likely 24x24 or 12x24 pixels in VRAM.

---

## APPLY SCRIPT

```python
import struct

exe_path = "extracted/SLPM_653.78"
data = bytearray(open(exe_path, "rb").read())

patches = [
    # (file_offset, byte_index, old_value, new_value, description)
    (0x205A10, 0, 0xC0, 0x80, "A1: centering sll 3->2"),
    (0x20623C, 0, 0xC0, 0x80, "A2: X pos sll 3->2"),
    (0x206F74, 0, 0xC0, 0x80, "A3: X pos sll 3->2"),
    (0x207CA8, 0, 0xC0, 0x80, "A4: X pos sll 3->2"),
    (0x2083EC, 0, 0xC0, 0x80, "A5: X pos sll 3->2"),
    (0x2089F4, 0, 0xC0, 0x80, "A6: X pos sll 3->2"),
    (0x203C44, 0, 0xC0, 0x80, "A7: layout sll 3->2"),
    (0x206208, 0, 0xC0, 0x80, "A8: render coord sll 3->2"),
    (0x206F54, 0, 0xC0, 0x80, "A9: render coord sll 3->2"),
    (0x203C48, 0, 0xE8, 0xF4, "B1: -24 -> -12"),
    (0x207DF8, 0, 0xE8, 0xF4, "B2: -24 -> -12"),
    (0x205D4C, 0, 0x80, 0x40, "C1: mode-2 sll 2->1"),
    (0x205D50, 0, 0x48, 0xA4, "C2: -184 -> -92"),
]

for offset, byte_idx, old, new, desc in patches:
    actual = data[offset + byte_idx]
    assert actual == old, f"MISMATCH at 0x{offset:06X}+{byte_idx}: expected 0x{old:02X}, got 0x{actual:02X} ({desc})"
    data[offset + byte_idx] = new
    print(f"  Patched 0x{offset:06X}: 0x{old:02X} -> 0x{new:02X}  ({desc})")

open(exe_path + ".halfwidth", "wb").write(data)
print(f"\nWrote patched EXE to {exe_path}.halfwidth")
```
