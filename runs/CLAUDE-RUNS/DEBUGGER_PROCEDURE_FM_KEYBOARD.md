# Definitive PCSX2 Debugger Procedure: Why F and M Don't Render on the Keyboard

## Background Summary

F (glyph 38) and M (glyph 45) are blank on the name entry keyboard. All other letters work.
Both glyphs have valid cell data, valid font atlas entries, and valid R2100 sub0 content.
The original Japanese ISO renders F and M fine.

## Static Analysis Findings

### Cell Data Structure (EXE at `extracted/SLPM_653.78`)

The game uses a **Cell Data Page Table** at EXE file offset `0x3DB180` (VA `0x004DB100`).
Each entry is 8 bytes: `(desc_idx: u32, cell_data_ptr: u32_VA)`.

The game resolves a glyph ID to a cell entry like this:
```
page  = glyph_id >> 8      (sra at VA 0x00494300)
cell  = glyph_id & 0xFF    (andi at VA 0x00494380)
desc_idx = page_table[page].desc_idx     (lbu at VA 0x00494318)
cell_ptr = page_table[page].cell_data_ptr (lw at VA 0x00494398)
cell_entry = cell_ptr + cell * 8         (8 bytes: U, V, W, flag, vram_lo, vram_hi, gs_lo, gs_hi)
```

For keyboard glyphs (IDs 0-93), `page = 0` always. Page 0 has `desc_idx = 9`.

### Cell Data for Key Glyphs

All keyboard glyphs share the same structure. Comparison:

| Glyph | Char | Cell Data (hex)      | U | V  | W   | flag | VRAM   | gs     |
|-------|------|----------------------|---|----|----|------|--------|--------|
| 33    | A    | `013c640040a24f00`   | 1 | 60 | 100 | 0    | 0xA240 | 0x004F |
| 38    | F    | `0141640068a24f00`   | 1 | 65 | 100 | 0    | 0xA268 | 0x004F |
| 39    | G    | `0142640070a24f00`   | 1 | 66 | 100 | 0    | 0xA270 | 0x004F |
| 45    | M    | `003f640098a24f00`   | 0 | 63 | 100 | 0    | 0xA298 | 0x004F |
| 46    | N    | `003c6400a0a24f00`   | 0 | 60 | 100 | 0    | 0xA2A0 | 0x004F |

**There is NO structural difference** between F/M and working glyphs. Same desc_idx (9), same gs config (0x004F), same W (100). The only differences are the expected U, V, and VRAM block values.

### The BSS Descriptor Table (RUNTIME ONLY)

The desc_idx value (9 for keyboard) indexes into a runtime descriptor table at **VA `0x00575C10`** (28 bytes per entry). This table is in BSS -- it does NOT exist in the EXE file and is populated at runtime.

Descriptor 9 entry address: `0x575C10 + 9 * 28 = 0x575CFC`

This descriptor tells the GS renderer which texture in VRAM to sample from. Since ALL keyboard glyphs use desc_idx=9, the descriptor itself is not the problem (other letters work). The problem is at the VRAM block level.

### VRAM Block Collision Analysis

VRAM blocks are GS block addresses (256 bytes each). F uses VRAM 0xA268, M uses 0xA298.

Searching all 50 pages of cell data, only two OTHER glyphs share these VRAM values:
- **Glyph 534** (page 2, cell 22, desc_idx=0): VRAM 0xA268 -- same as F
- **Glyph 771** (page 3, cell 3, desc_idx=2): VRAM 0xA298 -- same as M

These are kanji glyphs. However, they use **different desc_idx** values (0 and 2 vs 9), which likely means different TBP0 base pointers. Different TBP0 means the same VRAM block number maps to different physical VRAM locations. So this may NOT be a true collision.

**The root cause is something that happens at runtime.** It cannot be determined from static analysis alone.

---

## PCSX2 Debugger Procedure

### Prerequisites
- PCSX2 with debugger enabled (Debug > Open Debugger Window or press Ctrl+D in nightly builds)
- Boot the patched ISO FRESH (no save states)
- Navigate to the name entry screen (character creation)

### Phase 1: Verify Cell Data Is Intact in RAM

Once at the name entry keyboard screen:

1. **Open Memory View** (Debug > Memory)
2. Go to address **`0x004D8DC0`** (F's cell entry)
   - Expected bytes: `01 41 64 00 68 A2 4F 00`
   - If different, something is corrupting the cell data in RAM
3. Go to address **`0x004D8DF8`** (M's cell entry)  
   - Expected bytes: `00 3F 64 00 98 A2 4F 00`
4. Compare with A (working) at **`0x004D8D98`**:
   - Expected bytes: `01 3C 64 00 40 A2 4F 00`

**If cell data is corrupted**: set a write breakpoint (Hardware breakpoint, Write, at `0x004D8DC0`, size 8) and reboot to find what overwrites it.

**If cell data is intact**: proceed to Phase 2.

### Phase 2: Inspect the Runtime Descriptor Table

1. Go to address **`0x00575CFC`** (descriptor 9, used by ALL keyboard glyphs)
2. Read 28 bytes. Record them. This is the texture descriptor.
3. Also read descriptor 0 at `0x00575C10` (28 bytes) and descriptor 2 at `0x575C10 + 2*28 = 0x575C48` (28 bytes).
4. Key question: **Does descriptor 9 contain a valid texture pointer?**
   - If all zeros: the keyboard texture was never loaded
   - Look for a TBP0-like value in the first few words -- this tells where the texture sits in VRAM

**Record the full 28 bytes of descriptor 9. This is critical data we cannot determine statically.**

### Phase 3: Set Breakpoints on the Cell Lookup Function

Set execution breakpoints at these addresses:

| Address     | Purpose                                          |
|-------------|--------------------------------------------------|
| `0x00494300` | Entry: `sra v0, a0, 8` -- page = glyph_id >> 8  |
| `0x00494318` | `lbu a2, 0(a1)` -- reads desc_idx from page table |
| `0x00494380` | `andi v0, a3, 0xFF` -- cell = glyph_id & 0xFF   |
| `0x00494398` | `lw v1, 0(v1)` -- loads cell_ptr from page table |

Then trigger the keyboard to render (navigate cursor, or just wait for the render cycle).

When the breakpoint hits:
1. Check register `a0` (or `a3`) -- this is the glyph_id
2. If `a0 = 38` (F) or `a0 = 45` (M):
   - Step through the function
   - At `0x00494318`: check `a1` points to `0x004DB100 + 0*8 = 0x004DB100` and `a2` = 9
   - At `0x00494398`: check `v1` gets `0x004D8C90` (page 0 cell_ptr)
   - Continue stepping to see how the VRAM block (0xA268/0xA298) is used

### Phase 4: Trace the GS Texture Upload

The critical question: **what texture data is at VRAM blocks 0xA268 and 0xA298 when the keyboard tries to render F and M?**

Method A -- GS Dump:
1. While on the name entry screen, use **Debug > GS > Dump** (or GSdx hardware debugging)
2. In the GS dump, look for TEXFLUSH and IMAGE primitives that target the VRAM range around 0xA268 * 256 = byte offset 0x29A680 (about 2.7MB into VRAM)
3. Check if any texture upload (GS IMAGE transfer) overwrites this area AFTER the keyboard texture is loaded

Method B -- BITBLTBUF monitoring:
1. GS register `BITBLTBUF` (address 0x50) controls texture uploads to VRAM
2. The DBP field (bits 0-13) specifies the destination block pointer
3. Set a conditional breakpoint in the GS path (if PCSX2 supports it) for DBP values near 0xA268

### Phase 5: Compare VRAM Content Between Working and Broken Glyphs

Use PCSX2's **GS Memory View** (if available in your build):

1. Examine VRAM at block 0xA240 (A - working). There should be pixel data of the letter A.
2. Examine VRAM at block 0xA268 (F - broken). Is there pixel data or is it empty/wrong?
3. Examine VRAM at block 0xA298 (M - broken). Same check.
4. If 0xA268 and 0xA298 are empty/zeroed: something cleared them after the keyboard texture upload.
5. If they contain wrong data: something overwrote them.

### Phase 6: Check for Texture Reload Race Condition

If F and M fail because their VRAM blocks are overwritten:

1. Identify WHAT writes to those VRAM blocks. The chargen screen loads multiple textures:
   - R2100 (kanji font atlas, 4 sub-blocks)
   - R1272 (dialogue font atlas)
   - R1188 (name entry font)  
   - Background/UI textures (R1370, etc.)

2. Set a **hardware write breakpoint** on GS VRAM address 0xA268 * 256 (if PCSX2 supports GS memory breakpoints). This is the most direct way to catch the culprit.

3. Alternative: use the **GS Register Log** to find all BITBLTBUF writes where DBP is in the range 0xA240-0xA2A0. Then check which writes happen after the keyboard texture upload.

### Phase 7: Nuclear Option -- Swap F and A in Cell Data

If the above doesn't reveal the cause, try this experiment:

1. In a hex editor, swap the VRAM block bytes of F and A in the EXE:
   - At file offset `0x3D8E40` (F): change bytes 4-5 from `68 A2` to `40 A2` (A's VRAM)
   - At file offset `0x3D8E18` (A): change bytes 4-5 from `40 A2` to `68 A2` (F's VRAM)
2. Rebuild ISO and test.
3. If now A disappears and F works: the problem is specifically with VRAM block 0xA268 being overwritten.
4. If F still disappears: the problem is not VRAM-block-specific, but glyph-specific in the rendering code.

---

## Critical Addresses Quick Reference

```
Cell data (page 0 start):  VA 0x004D8C90  (file 0x3D8D10)
Page table:                 VA 0x004DB100  (file 0x3DB180)
Runtime desc table:         VA 0x00575C10  (BSS, runtime only)
Desc[9] (keyboard):         VA 0x00575CFC  (BSS)

F cell entry:               VA 0x004D8DC0  (file 0x3D8E40)
M cell entry:               VA 0x004D8DF8  (file 0x3D8E78)
A cell entry:               VA 0x004D8D98  (file 0x3D8E18)
G cell entry:               VA 0x004D8DC8  (file 0x3D8E48)

Page lookup func:           VA 0x00494300
Cell lookup func:           VA 0x00494380
Desc load:                  VA 0x00494318
Cell ptr load:              VA 0x00494398
Game state query:           VA 0x0023C740

F VRAM block:               0xA268 (byte addr: 0xA268 * 256 = 0x29A680)
M VRAM block:               0xA298 (byte addr: 0xA298 * 256 = 0x29A980)
A VRAM block:               0xA240 (byte addr: 0x29A400) -- works
G VRAM block:               0xA270 (byte addr: 0x29A700) -- works
```

## Expected Outcomes

The most likely root cause is one of:

1. **VRAM overwrite**: Some texture upload (R2100 sub-block, or another resource) writes to VRAM blocks 0xA268 and 0xA298 after the keyboard texture is loaded, blanking F and M. Phase 5 and 6 will confirm this.

2. **Rendering skip**: The rendering code has a special case that skips certain glyph IDs or VRAM blocks. Phase 3 breakpoints will reveal this.

3. **Descriptor corruption**: Descriptor 9's texture parameters get modified between frames, causing the renderer to sample from the wrong VRAM location for specific U/V coordinates. Phase 2 will reveal this.

The VRAM swap experiment (Phase 7) is the quickest way to distinguish between cause 1 and causes 2/3.
