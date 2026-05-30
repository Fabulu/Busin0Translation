# PS2 Graphics Synthesizer Register Reference

Quick reference for GS registers used in texture uploads via the GIF A+D pathway.
Derived from ps2tek, the GS Users Manual, and PCSX2 source.

---

## Pixel Storage Mode (PSM) Values

Used in BITBLTBUF (SPSM/DPSM), TEX0 (PSM), and FRAME (PSM) fields.

| Value | Name       | BPP | Page Size (px) | Block Size (px) | Notes                          |
|-------|------------|-----|----------------|-----------------|--------------------------------|
| 0x00  | PSMCT32    | 32  | 64 x 32        | 8 x 8           | Standard 32-bit RGBA           |
| 0x01  | PSMCT24    | 24  | 64 x 32        | 8 x 8           | 24-bit RGB (stored as 32-bit)  |
| 0x02  | PSMCT16    | 16  | 64 x 64        | 16 x 8          | 16-bit RGBA (1-5-5-5)          |
| 0x0A  | PSMCT16S   | 16  | 64 x 64        | 16 x 8          | 16-bit swizzled variant        |
| 0x13  | PSMT8      | 8   | 128 x 64       | 16 x 16         | 8-bit indexed (256 colors)     |
| 0x14  | PSMT4      | 4   | 128 x 128      | 32 x 16         | 4-bit indexed (16 colors)      |
| 0x1B  | PSMT8H     | 8   | 64 x 32        | 8 x 8           | 8-bit in upper 8 of 32-bit     |
| 0x24  | PSMT4HL    | 4   | 64 x 32        | 8 x 8           | 4-bit in bits 24-27 of 32-bit  |
| 0x2C  | PSMT4HH    | 4   | 64 x 32        | 8 x 8           | 4-bit in bits 28-31 of 32-bit  |
| 0x30  | PSMZ32     | 32  | 64 x 32        | 8 x 8           | 32-bit Z buffer                |
| 0x31  | PSMZ24     | 24  | 64 x 32        | 8 x 8           | 24-bit Z buffer                |
| 0x32  | PSMZ16     | 16  | 64 x 64        | 16 x 8          | 16-bit Z buffer                |
| 0x3A  | PSMZ16S    | 16  | 64 x 64        | 16 x 8          | 16-bit Z swizzled              |

All pages are 8 KiB (8192 bytes). Each page contains 32 blocks.

---

## TEX0 (Register 0x06 / 0x07 for Context 1/2) -- 64 bits

Controls texture sampling: base pointer, dimensions, format, CLUT info.

```
Bits    Field   Description
------  ------  --------------------------------------------------
 0-13   TBP0    Texture base pointer (address / 64), unit = 256 bytes
14-19   TBW     Texture buffer width (pixels / 64)
                  Actual buffer width = TBW * 64 pixels
                  Must be >= ceil(tex_width / 64)
                  TBW=0 is treated as TBW=1 for most formats
20-25   PSM     Pixel storage mode (see PSM table above)
26-29   TW      Texture width exponent: width = 2^TW  (max 1024)
30-33   TH      Texture height exponent: height = 2^TH (max 1024)
   34   TCC     Texture color component
                  0 = RGB (alpha forced to 0x80)
                  1 = RGBA (alpha from texture)
35-36   TFX     Texture function (color blending mode)
                  0 = Modulate
                  1 = Decal
                  2 = Highlight
                  3 = Highlight2
37-50   CBP     CLUT base pointer (address / 64)
51-54   CPSM    CLUT pixel storage mode
                  0x00 = PSMCT32
                  0x02 = PSMCT16
                  0x0A = PSMCT16S
   55   CSM     CLUT storage mode (0 = CSM1, 1 = CSM2)
56-60   CSA     CLUT entry offset / 16
                  For PSMCT32 CLUT: offset = CSA * 16
                  For PSMCT16 CLUT: offset = CSA * 16
                  Must be 0 in CSM2
61-63   CLD     CLUT cache control
                  0 = Do not reload
                  1 = Reload cache
                  2 = Reload + copy CBP to CBP0
                  3 = Reload + copy CBP to CBP1
                  4 = If CBP != CBP0, reload + copy to CBP0
                  5 = If CBP != CBP1, reload + copy to CBP1
```

### TBW vs Actual Texture Width

TBW defines the buffer stride in VRAM, not the visible texture width. The texture
width comes from `2^TW`. Key rules:

- TBW must be `>= ceil(texture_width / 64)` for all formats
- TBW is always in units of 64 *pixels* regardless of PSM
- For PSMT4 (4bpp): 64 pixels = 32 bytes; a page row is 128 pixels wide
- For PSMT8 (8bpp): 64 pixels = 64 bytes; a page row is 128 pixels wide
- For PSMCT32 (32bpp): 64 pixels = 256 bytes; a page row is 64 pixels wide
- Common: TBW=2 means 128px stride, TBW=4 means 256px stride, TBW=8 means 512px

---

## BITBLTBUF (Register 0x50) -- 64 bits

Configures source and destination for GIF<->VRAM and VRAM<->VRAM transfers.

```
Bits    Field   Description
------  ------  --------------------------------------------------
 0-13   SBP     Source base pointer (address / 64)
   15   --      Unused
16-21   SBW     Source buffer width (pixels / 64)
22-23   --      Unused
24-29   SPSM    Source pixel storage mode (see PSM table)
30-31   --      Unused
32-45   DBP     Destination base pointer (address / 64)
   47   --      Unused
48-53   DBW     Destination buffer width (pixels / 64)
54-55   --      Unused
56-61   DPSM    Destination pixel storage mode (see PSM table)
62-63   --      Unused
```

For GIF->VRAM uploads, only the destination fields (DBP, DBW, DPSM) matter.
For VRAM->GIF reads, only the source fields (SBP, SBW, SPSM) matter.
For VRAM->VRAM, both sets are used; source and dest must have same BPP.

### Base Pointer Addressing

The base pointer is in units of 256 bytes (64 words of 32 bits).
To get the VRAM byte address: `byte_addr = TBP0 * 256` or `SBP * 256`.

---

## TRXPOS (Register 0x51) -- 64 bits

Defines the top-left corner of source and destination rectangles.

```
Bits    Field   Description
------  ------  --------------------------------------------------
 0-10   SSAX    Source upper-left X (pixels)
11-15   --      Unused
16-26   SSAY    Source upper-left Y (pixels)
27-31   --      Unused
32-42   DSAX    Destination upper-left X (pixels)
43-47   --      Unused
48-58   DSAY    Destination upper-left Y (pixels)
59-60   DIR     Transmission order (VRAM->VRAM only)
                  0 = Upper-left -> lower-right
                  1 = Lower-left -> upper-right
                  2 = Upper-right -> lower-left
                  3 = Lower-right -> upper-left
61-63   --      Unused
```

Coordinates wrap at 2048: `X = (TRXPOS.X + offset) % 2048`.

---

## TRXREG (Register 0x52) -- 64 bits

Defines the width and height of the transfer rectangle.

```
Bits    Field   Description
------  ------  --------------------------------------------------
 0-11   RRW     Transfer width (pixels)
12-31   --      Unused
32-43   RRH     Transfer height (pixels)
44-63   --      Unused
```

Width and height are in pixel units of the format specified in BITBLTBUF.
For PSMT4: width is in 4-bit pixels (so 64 pixels = 32 bytes per row).

---

## TRXDIR (Register 0x53) -- 64 bits

Writing this register initiates the transfer.

```
Bits    Field   Description
------  ------  --------------------------------------------------
  0-1   XDIR    Transfer direction
                  0 = GIF -> VRAM (host-to-local)
                  1 = VRAM -> GIF (local-to-host)
                  2 = VRAM -> VRAM (local-to-local)
                  3 = Deactivated
 2-63   --      Unused
```

After writing TRXDIR=0, send pixel data via HWREG (register 0x54)
or use GIFtag IMAGE mode.

---

## GIFtag Format (128 bits)

The header preceding all GIF data packets.

```
Bits     Field     Description
-------  --------  --------------------------------------------------
  0-14   NLOOP     Number of loop iterations
    15   EOP       End of packet flag
 16-45   --        Unused
    46   PRE       Enable PRIM field
 47-57   PRIM      Data for PRIM register (if PRE=1)
 58-59   FLG       Data format
                     0 = PACKED (16 bytes per register)
                     1 = REGLIST (8 bytes per register)
                     2 = IMAGE (raw pixel data)
                     3 = IMAGE (same)
 60-63   NREGS     Number of register descriptors (0 = 16)
 64-127  REGS      Register descriptor list (4 bits each)
```

### A+D Register Descriptor (reg = 0x0E)

In PACKED format, register descriptor 0x0E sends 64 bits of data
to an arbitrary GS register:

```
Bits     Field     Description
-------  --------  --------------------------------------------------
  0-63   DATA      64-bit value to write
 64-71   ADDR      GS register address (e.g., 0x50 = BITBLTBUF)
 72-127  --        Unused
```

---

## Typical Texture Upload Sequence (GIF A+D)

A standard EE->VRAM texture upload sends these registers in order:

1. **BITBLTBUF** (0x50) -- Set destination base, width, format
2. **TRXPOS** (0x51) -- Set destination X,Y (usually 0,0)
3. **TRXREG** (0x52) -- Set transfer width and height
4. **TRXDIR** (0x53) -- Write 0 to start GIF->VRAM transfer
5. *GIFtag with FLG=IMAGE* -- Raw pixel data follows
6. **TEXFLUSH** (0x3F) -- Invalidate texture cache
7. **TEX0** (0x06) -- Configure texture for rendering

### Data packing in IMAGE mode

- PSMCT32: 2 pixels per quadword (each 32 bits)
- PSMCT16: 4 pixels per quadword (each 16 bits, but swizzled in VRAM)
- PSMT8: 16 pixels per quadword (each 8 bits)
- PSMT4: 32 pixels per quadword (each 4 bits, low nibble first)

---

## VRAM Memory Layout

VRAM is 4 MiB (4,194,304 bytes), addressed as 1,048,576 x 32-bit words.

### Page / Block / Column Hierarchy

| PSM      | Page (px)   | Blocks/Page | Block (px) | Bytes/Page |
|----------|-------------|-------------|------------|------------|
| PSMCT32  | 64 x 32     | 32          | 8 x 8      | 8192       |
| PSMCT16  | 64 x 64     | 32          | 16 x 8     | 8192       |
| PSMT8    | 128 x 64    | 32          | 16 x 16    | 8192       |
| PSMT4    | 128 x 128   | 32          | 32 x 16    | 8192       |

Blocks within a page are arranged in a Z-order (Morton) swizzle pattern.
Pixels within a block are also swizzled. The swizzle is transparent to
software -- you send linear pixel data and the GS hardware stores it
in swizzled order in VRAM. Reading back requires de-swizzle.

### CLUT (Color Look-Up Table) Layout

- PSMT8 uses 256-entry CLUT (either 32-bit or 16-bit entries)
- PSMT4 uses 16-entry CLUT
- CSM1: CLUT entries are stored in a swizzled order within a single block
- CSM2: CLUT entries are loaded 16 at a time using CSA offset

For PSMCT32 CLUTs with CSM1, the 256 entries occupy 1024 bytes = 1 page.
The entries are NOT stored linearly; the GS reads them in a specific
interleaved order (indices 0-7, 16-23, 8-15, 24-31, ...).

---

## Python: Decoding A+D Register Pairs

```python
def decode_ad_pair(data: int, addr: int) -> dict:
    """Decode a 64-bit value written to a GS register via A+D."""
    
    PSM_NAMES = {
        0x00: "PSMCT32", 0x01: "PSMCT24", 0x02: "PSMCT16", 0x0A: "PSMCT16S",
        0x13: "PSMT8",   0x14: "PSMT4",   0x1B: "PSMT8H",
        0x24: "PSMT4HL", 0x2C: "PSMT4HH",
        0x30: "PSMZ32",  0x31: "PSMZ24",  0x32: "PSMZ16",  0x3A: "PSMZ16S",
    }
    
    if addr == 0x50:  # BITBLTBUF
        return {
            "reg": "BITBLTBUF",
            "SBP":  (data >>  0) & 0x3FFF,
            "SBW":  (data >> 16) & 0x3F,
            "SPSM": PSM_NAMES.get((data >> 24) & 0x3F, "?"),
            "DBP":  (data >> 32) & 0x3FFF,
            "DBW":  (data >> 48) & 0x3F,
            "DPSM": PSM_NAMES.get((data >> 56) & 0x3F, "?"),
        }
    
    elif addr == 0x51:  # TRXPOS
        return {
            "reg": "TRXPOS",
            "SSAX": (data >>  0) & 0x7FF,
            "SSAY": (data >> 16) & 0x7FF,
            "DSAX": (data >> 32) & 0x7FF,
            "DSAY": (data >> 48) & 0x7FF,
            "DIR":  (data >> 59) & 0x3,
        }
    
    elif addr == 0x52:  # TRXREG
        return {
            "reg": "TRXREG",
            "RRW": (data >>  0) & 0xFFF,
            "RRH": (data >> 32) & 0xFFF,
        }
    
    elif addr == 0x53:  # TRXDIR
        dirs = {0: "GIF->VRAM", 1: "VRAM->GIF", 2: "VRAM->VRAM", 3: "Off"}
        return {
            "reg": "TRXDIR",
            "XDIR": dirs.get(data & 3, "?"),
        }
    
    elif addr in (0x06, 0x07):  # TEX0_1 / TEX0_2
        tw = (data >> 26) & 0xF
        th = (data >> 30) & 0xF
        return {
            "reg": f"TEX0_{addr - 5}",
            "TBP0": (data >>  0) & 0x3FFF,
            "TBW":  (data >> 14) & 0x3F,
            "PSM":  PSM_NAMES.get((data >> 20) & 0x3F, "?"),
            "TW":   tw, "width":  min(1 << tw, 1024),
            "TH":   th, "height": min(1 << th, 1024),
            "TCC":  (data >> 34) & 1,
            "TFX":  (data >> 35) & 3,
            "CBP":  (data >> 37) & 0x3FFF,
            "CPSM": PSM_NAMES.get((data >> 51) & 0xF, "?"),
            "CSM":  (data >> 55) & 1,
            "CSA":  (data >> 56) & 0x1F,
            "CLD":  (data >> 61) & 7,
        }
    
    return {"reg": f"0x{addr:02X}", "raw": f"0x{data:016X}"}
```

---

## Sources

- ps2tek (PSI-Rockin): https://psi-rockin.github.io/ps2tek/
- GS Users Manual: https://usermanual.wiki/Pdf/GSUsersManual.1012076781/html
- PCSX2 GS source: https://github.com/PCSX2/pcsx2/blob/master/pcsx2/GS/GSState.cpp
- Linux kernel PS2 GS structures: https://lore.kernel.org/linux-mips/25b6c975d334c0678ab3963d6c76584ed9471c35.1567326213.git.noring@nocrew.org/
- PS2 texture swizzling: http://ps2linux.no-ip.info/playstation2-linux.com/download/ezswizzle/TextureSwizzling.pdf
- GS Memory Swizzle Visualizer: https://gist.github.com/TellowKrinkle/bd6c6e1735cf5e03110ec57ddeea43a9
- Fobes GS palette article: https://fobes.dev/gs/2024/01/20/palette-shifting-with-the-gs.html
- Maister GS emulation: https://themaister.net/blog/2024/07/03/playstation-2-gs-emulation-the-final-frontier-of-vulkan-compute-emulation/
