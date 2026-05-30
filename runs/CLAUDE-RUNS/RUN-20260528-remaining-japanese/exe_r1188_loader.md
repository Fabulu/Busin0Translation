# EXE Code Analysis: R1188 (Name Entry UI Texture) Loading

## Resource Identity
- Resource index: 1188 (0x04A4)
- File type: type01 (texture resource)
- File: `extracted/packdata_resources/1188_type01.bin` (527,360 bytes = 0x80C00)

## Key Finding: Texture Format

**PSM = 20 (PSMT4)** -- 4-bit indexed color, 1024x1024 pixels.

The PSM is NOT hardcoded in the EXE. It is embedded in the resource data itself,
inside pre-built GIF A+D register packets. The EXE's resource system loads these
packets, patches in runtime VRAM addresses (TBP0, CBP), and DMAs them to the GS.

### TEX0_1 Register Value (all 17 sub-textures identical)
```
Data:    0x20100006A9440000
TBP0:    0      (patched at runtime with allocated VRAM address)
TBW:     16     (buffer width = 16 * 64 = 1024 pixels)
PSM:     20     (PSMT4 = 4-bit indexed)
TW:      10     (2^10 = 1024 pixels wide)
TH:      10     (2^10 = 1024 pixels tall)
TCC:     1      (RGBA)
TFX:     0      (MODULATE)
CBP:     0      (patched at runtime)
CPSM:    2      (CLUT stored as PSMCT16)
CSM:     0      (CSM1)
CSA:     0
CLD:     1      (load CLUT on use)
```

## R1188 File Structure (type01 format)

| Offset | Size | Content |
|--------|------|---------|
| 0x0000 | 0x10 | Header: word0 = 17 (sub-texture count) |
| 0x0010 | 0x550 | 17 GIF setup packets (80 bytes each) |
| 0x0560 | 0x6A0 | Sprite UV tables + 17 CLUT palettes (16 colors x 2 bytes each) |
| 0x0C00 | 0x80000 | PSMT4 pixel data (1024x1024 / 2 = 524,288 bytes) |

### Per-entry GIF packet structure (80 bytes = 5 quadwords)
```
QW0: GIF tag      -- NLOOP=4, EOP=1, FLG=PACKED, NREG=1, REG=A+D
QW1: A+D write    -- CLAMP_1 = {WMS=1, WMT=1} (clamp)
QW2: A+D write    -- MIPTBP1_1
QW3: A+D write    -- TEX1_1 = {LCM=0, MXL=0, MMAG=0, MMIN=0}
QW4: A+D write    -- TEX0_1 = PSM=20(PSMT4), 1024x1024, CPSM=PSMCT16
```

## EXE Resource System Functions

### Resource ID encoding
Resource IDs are passed in the **upper 16 bits** of $a0. The lower 16 bits are
a sub-resource index. For R1188: `$a0 = 0x04A40000`.

The EXE extracts the resource ID via `srl $reg, $a0, 16`.

### Function table

| VA | Purpose | Signature |
|----|---------|-----------|
| 0x004924A0 | Acquire resource (start loading, inc refcount) | `acquire(resID << 16)` |
| 0x00492510 | Release resource (dec refcount, free if 0) | `release(resID << 16)` |
| 0x00492640 | Check if resource is loaded | `is_loaded(resID << 16) -> bool` |
| 0x00492700 | Get loaded resource data pointer | `get_data(resID<<16 \| subIdx) -> ptr` |
| 0x00492A70 | Combine resource ID with sub-index | `combine(resID<<16, subIdx) -> combined` |
| 0x00492050 | Internal: create resource node, start async load | `_create_node(resIdx)` |

### GP-relative resource system globals
- `$gp - 25256` (0x9D58): Head of loaded-resource linked list (for acquire path)
- `$gp - 25248` (0x9D60): Head of loaded-resource linked list (for release path)
- `$gp - 25244` (0x9D64): Tail of loaded-resource linked list
- `$gp - 25240` (0x9D68): Free resource node pool pointer
- `$gp - 25232` (0x9D70): Resource table base pointer (for sub-entry lookup)

### Resource node structure (loaded in memory)
```
+0x00: next_ptr (linked list)
+0x04: prev/alt_ptr
+0x08: resource_data_ptr (points to loaded PACKDATA content)
+0x0C: status (0=loading, 2=loaded, etc.)
+0x0E: resource_id (uint16)
+0x10: ref_count
+0x14: DMA transfer descriptor (for async I/O)
+0x16: flags
```

## Name Entry Screen R1188 Flow

### Acquire path (entering name entry screen)
```
VA 0x002ED2E8: lui $at, 0x0056
VA 0x002ED2EC: lui $a0, 0x04A4          ; R1188
VA 0x002ED2F0: jal 0x004924A0           ; acquire(0x04A40000)
VA 0x002ED2F4: sh  $s1, 0x4EE2($at)    ; store state flag
VA 0x002ED2F8: jal 0x004924A0           ; acquire R1189 (delay slot has lui $a0, 0x04A5)
VA 0x002ED2FC: lui $a0, 0x04A5          ; R1189
VA 0x002ED300: jal 0x004924A0           ; acquire 3rd resource from $s0
VA 0x002ED304: lw  $a0, 0($s0)
```

### Load-check path (waiting for resources)
```
VA 0x002ED318: jal 0x00492640           ; check R1188 loaded
VA 0x002ED31C: lui $a0, 0x04A4          ; (delay slot)
VA 0x002ED320: beq $v0, $zero, ...      ; if not loaded, bail
VA 0x002ED328: jal 0x00492640           ; check R1189 loaded
VA 0x002ED324: lui $a0, 0x04A5          ; (delay slot)
VA 0x002ED330: beq $v0, $zero, ...      ; if not loaded, bail
VA 0x002ED338: jal 0x00492640           ; check 3rd resource
```

### Data access path (R1188 loaded, getting texture pointer)
```
func_2ED5E0:   ; get_R1188_data() wrapper
VA 0x002ED5E0: addiu $sp, $sp, -16
VA 0x002ED5E4: lui $a0, 0x04A4          ; R1188
VA 0x002ED5E8: sd  $ra, 0($sp)
VA 0x002ED5EC: jal 0x00492A70           ; combine(0x04A40000, 0x04A40000) = just 0x04A40000
VA 0x002ED5F0: daddu $a1, $a0, $zero    ; delay slot: $a1 = $a0
VA 0x002ED5F4: jal 0x00492700           ; get_data(0x04A40000) -> $v0 = data ptr
VA 0x002ED5F8: daddu $a0, $v0, $zero    ; delay slot
VA 0x002ED5FC: ld  $ra, 0($sp)
VA 0x002ED600: jr  $ra
VA 0x002ED604: addiu $sp, $sp, 16
```

### Rendering path (using R1188 data)
```
VA 0x002F2548: jal 0x002ED5E0           ; get_R1188_data() -> $v0 = texture ptr
VA 0x002F2550: daddu $a1, $v0, $zero    ; $a1 = texture data ptr
VA 0x002F2554: daddu $a0, $s1, $zero    ; $a0 = context struct
VA 0x002F2558: jal 0x00309870           ; submit_render_command($a0, $a1, 200)
VA 0x002F255C: addiu $a2, $zero, 200    ; delay slot: $a2 = 200

func_309870 creates a deferred render command:
  - Allocates 16-byte command struct
  - Stores context_ptr, texture_data_ptr, command_type=22
  - Queues callback at VA 0x00307DA0
  - Callback processes sub-textures, handles sprite rendering
```

### Release path (exiting name entry screen)
```
VA 0x002ED088: jal 0x00492510           ; release(0x04A40000) = release R1188
VA 0x002ED08C: lui $a0, 0x04A4          ; delay slot
VA 0x002ED09C: jal 0x00492510           ; release(0x04A50000) = release R1189
VA 0x002ED0A0: lui $a0, 0x04A5          ; delay slot
```

## Texture lookup table
At runtime, loaded texture structs are stored in a table at VA 0x00565150
(BSS, 32 entries max). Function `func_3028E0` (VA 0x003028E0) looks up
entries by index (0-31).

## Comparison with R1272

R1272 (1272_type01.bin, 65,792 bytes) is also PSMT4 but 256x512:
```
TEX0_1: TBP0=0, TBW=4, PSM=20(PSMT4), 256x512, CPSM=0(PSMCT32), CSA=0
```
Note: R1272 uses PSMCT32 CLUT while R1188 uses PSMCT16 CLUT.

## Summary

The texture format for R1188 is determined entirely by the resource data, not
by EXE code. The resource contains pre-built GIF register packets with:
- **PSM 20 (PSMT4)**: 4-bit indexed, 16 colors per sub-texture
- **1024x1024 pixels**: single large texture atlas
- **17 sub-textures**: each with its own 16-color CLUT (PSMCT16 format)
- **CLUT size**: 16 colors * 2 bytes = 32 bytes per sub-texture

The EXE's resource system is generic -- it loads the raw data, manages refcounts
and async I/O, and the rendering subsystem uses the pre-built GIF packets directly.
TBP0 and CBP fields (both zero in the file) are patched at runtime with allocated
VRAM addresses.
