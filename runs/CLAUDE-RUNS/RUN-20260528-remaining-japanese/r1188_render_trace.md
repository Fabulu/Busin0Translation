# R1188 Name Entry Tab Label Rendering Trace

## Summary

The game uses a **cell data table** system, NOT computed UV coordinates.
Each glyph ID maps to an 8-byte cell descriptor containing explicit UV tile
coordinates and width. Redirecting tabs to English labels requires patching
the cell data bytes at known file offsets.

---

## Call Chain: Glyph ID to Screen Pixels

```
Name entry code (0x2FB040)
  |
  |  Loads glyph ID from table at 0x4C9D20 (file 0x3C9DA0)
  |  table[page*176 + cell_slot*4] => glyph_id (e.g., 0x1900)
  |
  v
0x494350 - "render_glyph_sprite"
  |
  |  1. Calls 0x494300 to check if font page is loaded
  |     (checks descriptor_array[desc_idx].type == 5)
  |
  |  2. Splits glyph_id: page = id >> 8, cell = id & 0xFF
  |
  |  3. Reads from page table at VA 0x4DB100 (file 0x3DB180):
  |     word0 = table[page*8+0] => descriptor_index (low byte)
  |     word4 = table[page*8+4] => pointer to cell_data_array
  |
  |  4. Reads from cell_data_array[cell*8]:
  |     byte0 = U tile coordinate
  |     byte1 = V tile coordinate
  |     byte2 = width (pixels)
  |
  |  5. Packs: $a0 = byte0 | (byte1 << 8) | (desc_idx << 16)
  |            $a1 = byte2 (width)
  |
  v
0x474D30 - "submit_sprite_packet"
  |
  |  Unpacks $a0 into:
  |    sp+0x20 = desc_idx (bits 16-23) => selects texture page in VRAM
  |    sp+0x28 = V_tile (bits 8-15)    => row in atlas
  |    sp+0x2C = U_tile (bits 0-7)     => column in atlas
  |    sp+0x34 = width ($a1)           => sprite width
  |    sp+0x58 = 0x10003               => GIF tag (3 regs, 1 prim)
  |
  v
0x474580 - "send_gs_packet"
  |  Copies 64 bytes of GS packet to GS FIFO via DMA
  v
GS hardware renders textured sprite
```

---

## Page 0x19 Cell Data (Glyphs 0x1900-0x190C = Tab Labels)

Cell data array: **VA 0x4D9B10, file offset 0x3D9B90**

| Glyph | ID     | File Offset | U | V  | W   | b3 | b4  | b5  |
|-------|--------|-------------|---|----|-----|----|-----|-----|
| 0x00  | 0x1900 | 0x3D9B90    | 0 | 60 | 100 | 0  | 48  | 180 |
| 0x01  | 0x1901 | 0x3D9B98    | 0 | 61 | 100 | 0  | 56  | 180 |
| 0x02  | 0x1902 | 0x3D9BA0    | 0 | 62 | 100 | 0  | 64  | 180 |
| 0x03  | 0x1903 | 0x3D9BA8    | 0 | 63 | 100 | 0  | 72  | 180 |
| 0x04  | 0x1904 | 0x3D9BB0    | 0 | 64 | 100 | 0  | 80  | 180 |
| 0x05  | 0x1905 | 0x3D9BB8    | 0 | 65 | 100 | 0  | 88  | 180 |
| 0x06  | 0x1906 | 0x3D9BC0    | 0 | 66 | 100 | 0  | 96  | 180 |
| 0x07  | 0x1907 | 0x3D9BC8    | 0 | 67 | 100 | 1  | 104 | 180 |
| 0x08  | 0x1908 | 0x3D9BD0    | 0 | 68 | 100 | 1  | 112 | 180 |
| 0x09  | 0x1909 | 0x3D9BD8    | 0 | 69 | 100 | 1  | 120 | 180 |
| 0x0A  | 0x190A | 0x3D9BE0    | 0 | 70 | 100 | 0  | 128 | 180 |
| 0x0B  | 0x190B | 0x3D9BE8    | 0 | 71 | 100 | 1  | 136 | 180 |
| 0x0C  | 0x190C | 0x3D9BF0    | 0 | 72 | 100 | 0  | 144 | 180 |

- **U** (byte0): Column tile index in atlas. Always 0 for these glyphs.
- **V** (byte1): Row tile index in atlas. Sequential 60-72.
- **W** (byte2): Sprite width in pixels. Always 100.
- **b3** (byte3): Flag read by 0x4942C0 - likely "two-cell-wide" indicator.
- **b4:b5**: GS VRAM block address (little-endian 16-bit), used for texture source.

---

## Page Table Entry for 0x19

Location: VA 0x4DB100 + 25*8 = 0x4DB1C8, file offset 0x3DB248

- **word0** = 0x00000000 => descriptor_index = 0
- **word4** = 0x004D9B10 => pointer to cell data array above

Descriptor 0 is shared by many pages (0x01, 0x02, 0x09-0x0C, 0x19-0x31).
It represents the main font atlas texture (R1188).

---

## How to Redirect UV Coordinates

### Option A: Patch Cell Data (simplest)

Modify bytes 0-2 at file offsets 0x3D9B90-0x3D9BF7 to point to English
label glyphs. For example, if English tab labels are placed in R1188 at
row 2-3 of the atlas:

```python
# Change V value (byte1) for each glyph to point at English row
# e.g., V=2 instead of V=60 for the first tab label
```

The W (width) byte can also be changed if English labels need different widths.

### Option B: Patch Glyph ID Table

Modify the glyph IDs at VA 0x4C9D20 (file 0x3C9DA0) to point to
different cell indices within the same or different page.

### Option C: Code Hook

Intercept at 0x494350 (render_glyph_sprite) and substitute the packed
UV value before it reaches 0x474D30.

---

## Key Addresses

| What | VA | File Offset |
|------|-----|-------------|
| Name entry glyph table (Table 2E) | 0x4C9D20 | 0x3C9DA0 |
| Page table (desc_idx + cell_ptr) | 0x4DB100 | 0x3DB180 |
| Page 0x19 cell data array | 0x4D9B10 | 0x3D9B90 |
| render_glyph_sprite function | 0x494350 | 0x3943D0 |
| submit_sprite_packet function | 0x474D30 | 0x374DB0 |
| Font descriptor array (BSS) | 0x575C10 | (runtime) |
| Font page registration | 0x493FB0 | 0x394030 |

---

## Open Questions

1. **Cell pixel size**: How do U_tile and V_tile translate to pixel UV?
   The tile size is not explicit in the cell data. It may be fixed (e.g., 8x8
   or 16x16) or defined in the runtime descriptor at 0x575C10[0].
   With V going up to 88 in page 0x0B, and a 1024px atlas, max tile_h
   would be 1024/88 = ~11.6px, suggesting tiles may be 8px or variable.

2. **Atlas mapping**: Descriptor 0 serves many pages. The per-cell b4:b5
   VRAM block address may override the texture base for each individual
   cell, meaning each cell can source from a different part of VRAM
   regardless of the shared descriptor.
