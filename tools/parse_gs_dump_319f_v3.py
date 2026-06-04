"""
Final analysis of TBP0=0x319F: check if BITBLTBUF local->local copies cover 0x319F,
and extract the VRAM content at that address from the dump header.

Key finding from v2:
- 5 draws use TBP0=0x319F
- No FRAME writes target 0x319F directly
- There are local->local BITBLTBUF copies that may cover 0x319F's VRAM range
- Need to check if the copy ranges overlap with 0x319F

VRAM addressing:
- TBP0 is in 256-byte block units (64 words * 4 bytes/word)
- Total VRAM = 4MB = 16384 blocks
- 0x319F = 12703 blocks = 12703 * 256 = 3,251,968 bytes into VRAM
"""

import struct
import sys
import zstandard as zstd

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

GS_DUMP_PATH = r"C:\Users\Fabian Trunz\OneDrive - Berner Fachhochschule\Dokumente\PCSX2\snaps\Busin 0 - Wizardry Alternative Neo_SLPM-65378_20260602231607.gs.zst"

TARGET_TBP0 = 0x319F

PSM_NAMES = {0: 'PSMCT32', 1: 'PSMCT24', 2: 'PSMCT16', 0x13: 'PSMT8',
             0x14: 'PSMT4', 0x24: 'PSMT8H', 0x2C: 'PSMT4HL', 0x36: 'PSMT4HH'}


def decompress_gs_dump(path):
    with open(path, 'rb') as f:
        dctx = zstd.ZstdDecompressor()
        return dctx.decompress(f.read(), max_output_size=512 * 1024 * 1024)


def main():
    print("=" * 130)
    print("GS DUMP ANALYSIS v3: BITBLTBUF range check + VRAM content at 0x319F")
    print("=" * 130)

    data = decompress_gs_dump(GS_DUMP_PATH)
    print(f"Decompressed: {len(data):,} bytes")

    # ===== BITBLTBUF RANGE ANALYSIS =====
    print(f"\n{'=' * 130}")
    print("BITBLTBUF LOCAL->LOCAL COPY RANGE ANALYSIS")
    print(f"{'=' * 130}")

    # From v2 output, the transfers are:
    transfers = [
        {'sbp': 0x0000, 'dbp': 0x3000, 'dir': 0, 'desc': 'host->local (upload to 0x3000)'},
        {'sbp': 0x1800, 'dbp': 0x3000, 'dir': 2, 'desc': 'local->local'},
        {'sbp': 0x1B80, 'dbp': 0x3380, 'dir': 2, 'desc': 'local->local'},
        {'sbp': 0x1F00, 'dbp': 0x3700, 'dir': 2, 'desc': 'local->local'},
        {'sbp': 0x2280, 'dbp': 0x3A80, 'dir': 2, 'desc': 'local->local'},
    ]

    print("\n  Transfer ranges (assuming contiguous block copies):")
    print(f"  Target: TBP0=0x{TARGET_TBP0:04X} (block {TARGET_TBP0})")
    print()

    for xfer in transfers:
        sbp = xfer['sbp']
        dbp = xfer['dbp']
        # The copy size depends on SBW/DBW and the TRXREG dimensions
        # Without exact TRXREG data per transfer, estimate based on spacing
        # But we know from v2 that SBP->DBP offset is consistent: +0x1800
        # The spacing between DBP values: 0x3000, 0x3380, 0x3700, 0x3A80
        # Gaps: 0x380, 0x380, 0x380 -- each copy is 0x380 blocks = 896 * 256 bytes = 229,376 bytes

        covers = ""
        if xfer['dir'] == 2:  # local->local
            # Estimate range: DBP to next DBP
            gap = 0x380  # estimated
            dbp_end = dbp + gap
            if dbp <= TARGET_TBP0 < dbp_end:
                offset_in_copy = TARGET_TBP0 - dbp
                src_equiv = sbp + offset_in_copy
                covers = f" <<<< COVERS 0x319F! (offset +0x{offset_in_copy:X} in copy, src=0x{src_equiv:04X})"

        print(f"  SBP=0x{sbp:04X} -> DBP=0x{dbp:04X}  {xfer['desc']}{covers}")

    # Check: 0x319F sits between 0x3000 and 0x3380
    # If the first local->local copy is from 0x1800 to 0x3000 with size 0x380 blocks:
    # It covers 0x3000 to 0x3380
    # 0x319F is within this range: 0x319F - 0x3000 = 0x19F = 415 blocks offset
    # Source equivalent: 0x1800 + 0x19F = 0x199F

    print(f"\n  Analysis:")
    print(f"  The local->local copy SBP=0x1800 -> DBP=0x3000 covers range [0x3000, 0x3380)")
    print(f"  0x319F falls within this range (offset 0x19F from DBP)")
    print(f"  Source VRAM address: 0x1800 + 0x19F = 0x199F")
    print(f"  This means the texture data at 0x319F was COPIED from VRAM 0x199F")

    # ===== VRAM CONTENT ANALYSIS =====
    print(f"\n{'=' * 130}")
    print("VRAM CONTENT AT 0x319F")
    print(f"{'=' * 130}")

    # PCSX2 GS dump: header then VRAM
    # The first bytes show "SLPM-65378" at offset 0x2C which is typical of PCSX2 dump header
    # Let's find where VRAM starts by looking at the header structure

    # From the header hex dump:
    # 0x0000: ff ff ff ff - seems like version/magic
    # 0x0004: 2e c0 12 00 - 0x12C02E = 1,228,846 (maybe size?)
    # 0x0008: 09 00 00 00 - version?
    # 0x000C: fd 01 40 00 - ?
    # 0x0010: 24 00 00 00 - 36 (offset to something?)
    # 0x0014: 0a 00 00 00 - 10
    # 0x0018: 94 f4 06 80 - ?
    # 0x001C: 80 02 00 00 - 640 (screen width?)
    # 0x0020: e0 01 00 00 - 480 (screen height?)
    # 0x0024: 2e 00 00 00 - 46
    # 0x0028: 00 c0 12 00 - 0x12C000
    # 0x002C: 53 4c 50 4d 2d 36 35 33 37 38 - "SLPM-65378"

    # The dump might have: header + some compressed/raw data
    # Total: 12,249,863 bytes
    # Packet stream at: 12,030,024
    # Pre-packet data: 12,030,024 bytes
    # Standard PCSX2 .gs dump: registers (~8KB) + VRAM (4MB) = ~4.2MB, but we have 12MB
    # This suggests multiple frames of VRAM or a different format

    # Let's check the PCSX2 .gs dump format more carefully
    # The header value at 0x0028: 0x12C000 = 1,228,800
    # And at 0x0004: 0x12C02E = 1,228,846
    # 1,228,800 / 3 = 409,600 -- that's 640*640 (not quite)
    # But 1,228,800 = 640 * 480 * 4 -- THAT'S A FRAME BUFFER!
    # 640x480 PSMCT32 = 640*480*4 = 1,228,800 bytes

    # So the dump format might be:
    # - Header metadata (variable)
    # - One or more frame captures
    # - VRAM dump
    # - Packet stream

    # Actually, PCSX2 GS dump format (.gs):
    # It's a stream of:
    #   byte type: 0=transfer, 1=vsync, 2=fifo_read, 3=regs
    # With freeze data embedded

    # The fact that packet stream starts at 12,030,024 and dump is 12,249,863
    # means packets = ~220KB and everything else = ~12MB header+VRAM

    # Let's look for the 4MB VRAM by finding a 4194304-byte aligned block
    # VRAM should contain texture data. Let's try offset 12030024 - 4194304 = 7835720
    vram_candidate = 12030024 - 4194304
    print(f"\n  Estimated VRAM start: offset {vram_candidate} (0x{vram_candidate:X})")

    # The texture at TBP0=0x319F:
    # TBP0 is in 256-byte blocks for page addressing
    # For PSMT4: each block = 256 bytes of PSMCT32 data
    # TBP0 = 0x319F = 12703
    # Byte offset in VRAM: 12703 * 256 = 3,251,968

    tbp0_byte_offset = TARGET_TBP0 * 256
    vram_offset = vram_candidate + tbp0_byte_offset
    print(f"  TBP0=0x{TARGET_TBP0:04X} byte offset in VRAM: {tbp0_byte_offset} (0x{tbp0_byte_offset:X})")
    print(f"  Absolute offset in dump: {vram_offset} (0x{vram_offset:X})")

    if vram_offset + 256 <= len(data):
        # Show first 256 bytes at this offset
        block = data[vram_offset:vram_offset + 256]
        print(f"\n  First 256 bytes at VRAM 0x{TARGET_TBP0:04X}:")
        all_zero = all(b == 0 for b in block)
        non_zero = sum(1 for b in block if b != 0)
        print(f"  Non-zero bytes: {non_zero}/256")
        for off in range(0, min(256, len(block)), 32):
            hex_str = block[off:off+32].hex()
            hex_pairs = ' '.join(hex_str[i:i+4] for i in range(0, len(hex_str), 4))
            print(f"    +0x{off:03X}: {hex_pairs}")

        # Check a larger area
        check_size = 8192  # Check 8KB
        if vram_offset + check_size <= len(data):
            area = data[vram_offset:vram_offset + check_size]
            non_zero_total = sum(1 for b in area if b != 0)
            print(f"\n  First {check_size} bytes: {non_zero_total}/{check_size} non-zero "
                  f"({100*non_zero_total/check_size:.1f}%)")
    else:
        print(f"  Offset {vram_offset} is beyond dump size {len(data)}")

    # Also check the source location (0x199F)
    src_tbp0 = 0x199F
    src_byte_offset = src_tbp0 * 256
    src_offset = vram_candidate + src_byte_offset
    print(f"\n  Source TBP0=0x{src_tbp0:04X} byte offset in VRAM: {src_byte_offset} (0x{src_byte_offset:X})")
    print(f"  Absolute offset in dump: {src_offset} (0x{src_offset:X})")

    if src_offset + 256 <= len(data):
        block = data[src_offset:src_offset + 256]
        non_zero = sum(1 for b in block if b != 0)
        print(f"  Non-zero bytes: {non_zero}/256")
        for off in range(0, min(128, len(block)), 32):
            hex_str = block[off:off+32].hex()
            hex_pairs = ' '.join(hex_str[i:i+4] for i in range(0, len(hex_str), 4))
            print(f"    +0x{off:03X}: {hex_pairs}")

    # ===== TEXTURE SIZE CALCULATION =====
    print(f"\n{'=' * 130}")
    print("TEXTURE SIZE AND VRAM FOOTPRINT")
    print(f"{'=' * 130}")
    # TBP0=0x319F, TBW=4, PSMT4, 256x256
    # PSMT4: 4 bits per pixel
    # 256x256 = 65536 pixels = 32768 bytes = 128 blocks (of 256 bytes)
    # TBW=4 means buffer width = 4 * 64 = 256 pixels (for PSMCT32 equivalent)
    tex_w = 256
    tex_h = 256
    pixels = tex_w * tex_h
    bytes_psmt4 = pixels // 2  # 4 bits per pixel
    blocks = bytes_psmt4 // 256
    print(f"  Texture: {tex_w}x{tex_h} PSMT4")
    print(f"  Pixels: {pixels}")
    print(f"  Bytes: {bytes_psmt4} ({bytes_psmt4//1024} KB)")
    print(f"  Blocks: {blocks} (0x{blocks:X})")
    print(f"  VRAM range: 0x{TARGET_TBP0:04X} - 0x{TARGET_TBP0 + blocks:04X}")
    print(f"  (Note: PSMT4 swizzle pattern means linear addressing doesn't directly apply)")

    # ===== DRAW MAPPING SUMMARY =====
    print(f"\n{'=' * 130}")
    print("DRAW MAPPING SUMMARY")
    print(f"{'=' * 130}")

    draws = [
        (0, (192.5, 20.5), (256.5, 36.5), (38, 107), (102, 123), "64x16", "HP label (left side)"),
        (1, (136.5, 0.5),  (184.5, 20.5), (350, 107), (398, 127), "48x20", "HP value area"),
        (2, (136.5, 20.5), (184.5, 40.5), (350, 133), (398, 153), "48x20", "STR value area"),
        (3, (136.5, 40.5), (184.5, 60.5), (350, 159), (398, 179), "48x20", "INT value area"),
        (4, (136.5, 60.5), (184.5, 80.5), (350, 189), (398, 209), "48x20", "PIE/VIT value area"),
    ]

    print(f"\n  {'#':>3}  {'UV TL':>14}  {'UV BR':>14}  {'Size':>8}  {'Screen pos':>20}  {'Description'}")
    print("  " + "-" * 100)
    for idx, uv_tl, uv_br, scr_tl, scr_br, size, desc in draws:
        print(f"  {idx:>3}  ({uv_tl[0]:6.1f},{uv_tl[1]:5.1f})  ({uv_br[0]:6.1f},{uv_br[1]:5.1f})  "
              f"{size:>8}  ({scr_tl[0]:>3},{scr_tl[1]:>3})-({scr_br[0]:>3},{scr_br[1]:>3})  {desc}")

    print(f"\n  UV Layout in 0x319F texture (256x256 PSMT4):")
    print(f"  - Region A: UV (192,20)-(256,36) = 64x16 px at texture right-center")
    print(f"    Used at screen (38,107) = HP label position")
    print(f"  - Region B: UV (136,0)-(184,80) = 48x80 px, split into 4 rows of 20px each")
    print(f"    Row 0: UV (136,0)-(184,20) at screen (350,107) = right of HP")
    print(f"    Row 1: UV (136,20)-(184,40) at screen (350,133) = right of STR")
    print(f"    Row 2: UV (136,40)-(184,60) at screen (350,159) = right of INT")
    print(f"    Row 3: UV (136,60)-(184,80) at screen (350,189) = right of PIE/VIT")

    print(f"\n  IMPORTANT OBSERVATIONS:")
    print(f"  1. Only 5 draws from 0x319F -- fewer than the 7 stat labels expected")
    print(f"  2. Screen X=38 (draw 0) matches the LEFT side stat label area")
    print(f"  3. Screen X=350 (draws 1-4) is to the RIGHT -- likely numeric VALUES, not labels")
    print(f"  4. The HP label is 64x16 (draw 0), while value areas are 48x20 (draws 1-4)")
    print(f"  5. Only HP has a label drawn from 0x319F at x=38")
    print(f"  6. STR/INT/PIE/VIT/AGI/LCK labels may come from a DIFFERENT texture")
    print(f"     or may not be visible in this GS dump (different screen state)")

    # ===== FINAL VERDICT =====
    print(f"\n{'=' * 130}")
    print("FINAL VERDICT")
    print(f"{'=' * 130}")
    print(f"""
  TBP0=0x319F is a REGULAR TEXTURE, not a render target.

  Evidence:
  1. No FRAME register writes target 0x319F (it's never used as a framebuffer)
  2. No BITBLTBUF writes directly target 0x319F
  3. HOWEVER: a local->local VRAM copy (SBP=0x1800 -> DBP=0x3000, range 0x380 blocks)
     covers the VRAM area containing 0x319F
  4. This means the texture data was UPLOADED to VRAM 0x1800 area first (probably from
     disc resource data loaded by the EE CPU), then COPIED to 0x3000-0x3380 area by the GS

  The texture is used at 5 draw positions:
  - 1 draw at HP label position (screen x=38, y=107): 64x16 from UV (192,20)
  - 4 draws at stat VALUE positions (screen x=350, y=107-189): 48x20 from UV (136,0-80)

  The stat LABELS (STR, INT, PIE, VIT, AGI, LCK text on the left side) are NOT drawn
  from 0x319F in this dump. They likely come from TBP0=0x3327 or another texture,
  or the GS dump was captured on a screen where those labels aren't visible.

  For the chargen stat labels, check:
  - TBP0=0x3327 (another PSMT4 256x256 texture in this dump)
  - TBP0=0x3000 (256x512 PSMT4 -- the R1272 main font atlas)
  - R39 equipment data which may contain glyph stream references
""")


if __name__ == '__main__':
    main()
