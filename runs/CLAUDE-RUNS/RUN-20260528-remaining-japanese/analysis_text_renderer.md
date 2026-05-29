# Text Renderer Reverse Engineering Analysis

## EXE Details
- File: `extracted/SLPM_653.78`, 4,185,776 bytes
- Renderer region: file 0x202000-0x210000 (VA 0x302000-0x310000)
- VA formula: VA = file_offset - 0x80 + 0x00100000

## Architecture Summary

The text system has three distinct layers:

1. **MSG Parser** (VA 0x302DB0, frame=176 bytes) -- parses glyph indices from MSG data
2. **Glyph Layout Engine** (VA 0x303C60, frame=160 bytes) -- positions glyphs in a slot array
3. **Render Dispatch** (VA 0x30CE90, frame=80 bytes) -- handles resource loading/animation states

---

## KEY FINDING 1: The "32 Lines Maximum" and Per-Line Width Array

At VA **0x302F58** in the MSG parser:
```
  0x302F48: spec_3c $v1, $zero, $s1  ; v1 = s1 = LINE counter
  0x302F4C: spec_3f $v1, $zero, $v1  ; sign-extend (EE-specific)
  ...
  0x302F58: slti  $v1, $v1, 32       ; check if line_number < 32
  0x302F5C: addu  $a0, $a1, $a0      ; combine s2 (char count) + s0 (width units)
  0x302F60: bne   $v1, $zero, continue
  0x302F64: sh    $a0, 64($s6)       ; store per-line width at offset +0x40
  0x302F68: [if >= 32: error/overflow handler]
```

Register tracking through the parser shows:
- `$s0` = width adjustment from control codes (0xFFD0-0xFFD9 add 1-10)
- `$s1` = LINE counter (incremented at 0x302F98 on newline)
- `$s2` = character index on current line
- `$s3` = total glyph counter
- `$s6` = display struct pointer, advanced by +2 per line (halfword per line)

The display structure has a **halfword array of 32 entries** at offset +0x40 (64 bytes total). Each ENTRY represents one LINE's cumulative width, not one glyph. The limit is **32 lines maximum**, which is generous.

**The per-glyph-per-line limit is NOT enforced in the parser** -- it is implicitly controlled by the glyph slot array size and the total glyph count in the MSG header.

---

## KEY FINDING 2: Fixed 12-Pixel Glyph Width (No Per-Glyph Width Table)

The glyph layout engine at VA 0x303C60 uses a **fixed 12-byte stride** per glyph slot:

```
  0x303DD8: [loop start: process glyph slot]
  0x303DE4: lw    $a0, 8($s5)      ; load glyph array base
  0x303DE8: addu  $a2, $a0, $v0    ; $v0 = byte offset into array
  0x303DEC: lh    $a0, 6($a2)      ; read field at +6 (X scroll position)
  0x303DF0: addiu $a0, $a0, -4     ; adjust scroll by -4 (or +4 in other branch)
  ...
  0x303E6C: bne   $a0, $zero, loop_start
  0x303E70: addiu $v0, $v0, 12     ; <<< ADVANCE TO NEXT GLYPH SLOT (+12 bytes)
```

The +12 advance appears in **multiple locations**:
- VA 0x303E70: `addiu $v0, $v0, 12` (scroll/animate loop)
- VA 0x303EF4: `addiu $a2, $a2, 12` (initialization loop)
- VA 0x305BF8: `addiu $a0, $a0, 12` (another render path)
- VA 0x30CEFC, 0x30CF2C, 0x30CF9C, etc.: `addiu $s0/$s1, +12` (state machine handlers)

**Each glyph occupies exactly 12 bytes in the slot array.** The renderer does NOT look up per-glyph widths from a table -- it uses a fixed 12-byte slot structure for all glyphs (both Japanese kanji and any ASCII substitutes).

The 12 bytes per slot likely contain:
- Bytes 0-1: glyph index (halfword)
- Bytes 2-3: flags/attributes
- Bytes 4-5: Y position or animation state
- Bytes 6-7: X position (the scroll field that gets +/-4 adjustment)
- Bytes 8-11: additional data (color? texture reference?)

---

## KEY FINDING 3: X-Position Clamp at 128

At VA 0x303E28:
```
  0x303E24: lh    $a0, 6($a0)      ; load X-position field from glyph slot
  0x303E28: slti  $at, $a0, 129    ; if X-position < 129...
  0x303E2C: bne   $at, $zero, skip ; ...skip the clamp
  0x303E30: nop
  0x303E34: sh    $a1, 0($a2)      ; clamp: store 128 (loaded at 0x303DD4)
```

The X-position field in each glyph slot is clamped to a maximum of **128 units**. Combined with the 12-byte stride, this means:
- Display area = 128 units wide at the glyph-position level
- This is NOT pixels directly; it's a scroll/reveal position counter

The value 128 appears 35 times in the renderer region as `addiu $rX, $zero, 128`, used for multiple purposes including this clamp.

---

## KEY FINDING 4: Line Count Limits

### 3 Lines Maximum (Dialogue Box)
At VA 0x30CEF4 (HANDLER_0 of the render state machine):
```
  0x30CED0: lui   $s0, 0x004D      ; load base of resource table
  0x30CED8: addiu $s0, $s0, -17328 ; -> VA 0x4CBC50 (file 0x3CBC D0)
  0x30CEE0: jal   0x4924A0         ; call resource loader
  0x30CEE4: lw    $a0, 0($s0)      ; load resource handle
  0x30CEE8: addiu $v0, $s1, 1      ; increment line counter
  0x30CEF4: slti  $v0, $s1, 3      ; <<< CHECK: line_counter < 3
  0x30CEF8: bne   $v0, $zero, loop ; continue if < 3
  0x30CEFC: addiu $s0, $s0, 12     ; advance resource pointer by 12
```

This processes **3 resource handles** spaced 12 bytes apart starting at VA 0x4CBC50. These are the 3 lines of the dialogue text box.

### 7 Items (Status/Menu)
Handlers at 0x30CF24 and 0x30CFEC use `slti $v0, $s0, 7` -- processing 7 items for menus/status displays, with resources at 0x4CBC80.

---

## KEY FINDING 5: Display Width 224 Pixels

At VA 0x305980:
```
  0x305974: addiu $v1, $zero, 3    ; check if mode == 3 (centered text?)
  0x305978: bne   $a0, $v1, skip
  0x305980: addiu $v1, $zero, 224  ; <<< DISPLAY BOX WIDTH = 224 pixels
  0x305988: sll   $a0, $a1, 1      ; a1 = char_count, multiply by 2
  0x30598C: addu  $a0, $a0, $a1    ; a0 = char_count * 3
  0x305990: sll   $a0, $a0, 3      ; a0 = char_count * 24 pixels
  0x305994: subu  $v1, $v1, $a0    ; centering_offset = 224 - (count * 24)
  0x305998: sh    $v1, 60($s5)     ; store as X-offset
```

This reveals the **text centering calculation**: the display box is 224 pixels wide, and each glyph takes 24 pixels (multiply count by 24, subtract from 224 to center). Wait -- 24 pixels = 2 * 12px glyph width? This suggests the glyphs are rendered at 2x scale or with spacing, making each character occupy 24px on screen.

---

## KEY FINDING 6: Y-Position Offsets (Line Spacing)

At VA 0x308DC0-0x308E14, there's a sequence of Y-position additions:
```
  0x308DCC: addiu $v0, $v0, 144    ; 24 * 6
  0x308DDC: addiu $v0, $v0, 168    ; 24 * 7
  0x308DEC: addiu $v0, $v0, 192    ; 24 * 8
  0x308DFC: addiu $v0, $v0, 216    ; 24 * 9  (NOT 12*18)
  0x308E0C: addiu $v0, $v0, 240    ; 24 * 10
```

These are Y-position offsets for positioning text lines, stored to sp+462 (the Y-coordinate halfword). The 24px line spacing confirms each text line is 24 pixels tall.

---

## KEY FINDING 7: Glyph Size Configuration Table

At VA 0x30ECA8-0x30ED90, there's a function that calls the same subroutine (0x3A2D10 via JAL 0x0E8B44) with $a3 set to sequential size values:
```
  $a3 = 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20
```

The results are stored as halfwords at sequential offsets (+0x0E, +0x10, +0x12, +0x14, +0x16, +0x18, +0x1A, +0x1C, ...). This is a **font metrics table** initialization, computing rendering parameters for glyph sizes 8 through 20 pixels. The key sizes used in the game:
- **12** (0x0C): Standard kanji width
- **14** (0x0E): Used in `addiu $a0, $zero, 14` at 0x302B3C, 0x3036A0, 0x30440C, 0x304458, 0x308A48
- **16** (0x10): Used heavily, possibly for menu/title text
- **18** (0x12): chars per line in original Japanese
- **20** (0x14): Used at 0x304D38, 0x30AD44

---

## TRUNCATION MECHANISM

Text gets truncated through a combination of:

1. **32 glyph slots per line** (hard limit at 0x302F58) -- the halfword display array can only hold 32 entries
2. **Fixed 12-byte glyph slot stride** -- no variable-width support; every glyph occupies the same slot size
3. **128-unit X-position clamp** (at 0x303E28) -- positions beyond 128 get clamped
4. **224px display box width** (at 0x305980) -- the centering calculation assumes 224px total

For Japanese text: 224px / 12px per kanji = ~18 characters per line (matches expected behavior).

For English text at 6px per character: 224px / 6px = ~37 characters would fit pixel-wise, BUT the 32-slot hard limit caps it at 32 characters per line.

---

## PATCH TARGETS (Priority Order)

### Patch 1: Glyph Slot Stride 12 bytes -> 6 bytes (HIGHEST IMPACT)
The fixed 12-byte stride per glyph is the primary reason English text gets truncated. At 12px per glyph, only 18 characters fit in a 224px line. With 6px half-width glyphs, the slot stride must also be halved.

**Locations** (all `addiu $rX, $rY, 12` -> `addiu $rX, $rY, 6`):
| VA | File Offset | Instruction | Context |
|-----|------------|-------------|---------|
| 0x303E70 | 0x203EF0 | `2442000C` | Main scroll/animate loop |
| 0x303EF4 | 0x203F74 | `24C6000C` | Init loop |
| 0x305BF8 | 0x205C78 | `2484000C` | Alternate render path |
| 0x30CEFC | 0x20CF7C | `2610000C` | State machine handler 0 (3-line) |
| 0x30CF2C | 0x20CFAC | `2631000C` | State machine handler 0 (7-item) |
| 0x30CF9C | 0x20D01C | `2631000C` | State machine handler 1 |
| 0x30CFF4 | 0x20D074 | `2631000C` | State machine handler 2 |
| 0x30D0D8 | 0x20D158 | `2652000C` | State machine handler 4 (resource load) |
| 0x30D0EC | 0x20D16C | `2631000C` | State machine handler 4 |
| 0x30D160 | 0x20D1E0 | `2652000C` | State machine handler 4 (second pass) |
| 0x30D174 | 0x20D1F4 | `2631000C` | State machine handler 4 |
| 0x30DA50 | 0x20DAD0 | `2652000C` | Additional render loop |
| 0x30DA68 | 0x20DAE8 | `2631000C` | Additional render loop |
| 0x30DB1C | 0x20DB9C | `2610000C` | Table lookup loop |

**Patch**: Change last byte of each instruction from `0C` to `06`
**Difficulty**: MEDIUM -- must change ALL 14 sites consistently
**Risk**: Only works if font atlas has half-width (6px) glyphs. The glyph slot DATA STRUCTURE is 12 bytes but the PIXEL ADVANCE is what matters for display width. Need to verify whether the +12 is pixel advance or struct stride.

**CRITICAL CAVEAT**: Some of these +12 values are struct strides through a 12-byte-per-entry resource table (e.g., at 0x4CBC50), NOT pixel advances. The state machine handlers at 0x30CED0-0x30D200 iterate through resource handle arrays with 12-byte spacing -- changing those would break resource loading. Only the display-side +12 values (0x303E70, 0x303EF4, 0x305BF8) should be changed.

### Patch 2: X-Position Clamp 128 -> 256 (REQUIRED with Patch 1)
- **Location**: VA 0x303E28 (file 0x203EA8)
- **Current**: `28810081` = `slti $at, $a0, 129`
- **Patch to**: `28810101` = `slti $at, $a0, 257`
- **Also**: VA 0x303DD4 (file 0x203E54): `24050080` -> `24050100` (clamp value)
- **Also**: VA 0x303ECC (file 0x203F4C): `24040080` -> `24040100`
- **Difficulty**: LOW -- simple constant changes

### Patch 3: Display Box Width 224px (CENTERING FIX)
- **Location**: VA 0x305980 (file offset 0x205A00)
- **Current**: `240300E0` = `addiu $v1, $zero, 224`
- **Note**: This is a special mode-3 centering calculation. For normal dialogue, the box width may be implicitly defined by the GS (Graphics Synthesizer) texture coordinates, not a simple constant. The centering formula uses `char_count * 24`, so at half-width it should use `char_count * 12`.
- **Difficulty**: MEDIUM

### Patch 4: 32-Line Limit (PROBABLY FINE)
- **Location**: VA 0x302F58 (file offset 0x202FD8)
- **Current**: `28630020` = `slti $v1, $v1, 32`
- **Status**: 32 lines is already generous for dialogue boxes (only 3 visible at a time). NO CHANGE NEEDED.

---

## RECOMMENDED APPROACH

### Option A: Half-Width Font (Simpler)

1. **Create half-width (6px) ASCII glyphs** in the font atlas, each occupying half a 12px cell
2. **Patch the display-side `addiu +12` to `addiu +6`** (ONLY the 3 render-loop sites, NOT the resource table strides)
3. **Patch the 128 clamp to 256** to allow wider X positions
4. **Keep the 32-line limit and existing glyph array structure**

Math: At 6px/char with the MSG glyph count unchanged, you get ~36 chars in a 224px line. The MSG parser already stores glyphs as 2-byte indices without per-line caps, so the only limit becomes the total glyph count field in the MSG header and the glyph slot array allocation.

### Option B: Proportional Width (Better Quality, Harder)

1. **Build a per-glyph width table** (e.g., 679 entries, 1 byte each) at a free EXE region
2. **Hook the glyph advance** code at 0x303E70 to load width from table[glyph_index] instead of fixed 12
3. **Patch the 128 clamp** accordingly
4. Requires **code injection** (overwrite unused EXE area or expand BSS)

### Option C: Software Line-Breaking (Easiest, No EXE Patches)

1. **Pre-wrap English text** at the MSG build stage to fit within 18 characters per line
2. Insert `0xFFFE` (newline) codes every 18 chars in the translation pipeline
3. Use existing 3-line dialogue box -- each screen shows 3 lines of 18 chars = 54 chars
4. Longer messages split across multiple pages with `0xFFFD` (page break)
5. **NO EXE PATCHES NEEDED** -- purely a translation toolchain change

Option C is recommended as the first step since it requires zero binary patching and solves most truncation issues immediately.

---

## Data Structure Summary

### Display Structure (at $s5)
| Offset | Size | Purpose |
|--------|------|---------|
| +0x00  | 4    | pointer to state data |
| +0x04  | 4    | pointer to msg text data |
| +0x08  | 4    | pointer to glyph slot array |
| +0x18  | 4    | line count / max lines |
| +0x1C  | 4    | total glyph count |
| +0x20  | 4    | current glyph count |
| +0x30  | 2    | display mode halfword |
| +0x32  | 2    | timer/counter |
| +0x36  | 2    | delay counter |
| +0x38  | 2    | scroll timer |
| +0x3A  | 2    | resource ID |
| +0x3C  | 2    | X offset (centering) |
| +0x40  | 64   | glyph position array (32 x halfword) |
| +0x80  | 32   | glyph attribute flags (32 x byte) |
| +0xA0  | 1    | completion counter |
| +0xA1  | 1    | current line number |
| +0xA5  | 1    | color/style byte |
| +0xA6  | 1    | mode byte (1=special, 2=simple) |
| +0xA7  | 1    | animation flag |

### Glyph Slot (12 bytes)
| Offset | Size | Purpose |
|--------|------|---------|
| +0x00  | 4    | resource handle / glyph data |
| +0x04  | 2    | attribute / Y data |
| +0x06  | 2    | X scroll position (clamped to 128) |
| +0x08  | 4    | additional render data |

### Resource Table at VA 0x4CBC50 (file 0x3CBCD0)
- 3 entries of 12 bytes each for the 3 dialogue text lines
- 7 entries at VA 0x4CBC80 for menu/status items
