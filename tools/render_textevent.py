#!/usr/bin/env python3
"""Render TextEventImage texture data from R1192 and R2361 as images."""
import struct, os, sys
sys.stdout.reconfigure(encoding='utf-8')

try:
    from PIL import Image
    import numpy as np
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    print("WARNING: PIL not available, will only do hex analysis")

BASE = 'C:/Programmieren/wizardrytranslation'
OUT = f'{BASE}/dumps/textevent'
os.makedirs(OUT, exist_ok=True)

def analyze_gs_setup(s2):
    """Parse the GS register setup at the start of section 2."""
    # First 12-byte entry at offset 0x10 contains:
    #   bytes 0-3: some config (0x18 = 24 for R1192, 0x18 = 24 for R2361)
    #   bytes 4-7: BITBLTBUF-like value
    #   bytes 8-11: address (FB7C, 2694, etc.)

    # The value 0x34034000 at offset 0x20 repeats -- this is the GS register address
    # 0x34 = MIPTBP1_1, but more likely this is a custom game engine interpretation

    # Let's look at the BITBLTBUF-like values
    # For R1192: 0x0018F000 at offset 0x14
    #   DBP (dest base pointer): bits 0-13 = 0x000 = 0 -> VRAM page 0
    #   DBW (dest buffer width): bits 16-21 = 0x18 = 24 -> 24 * 64 = 1536 pixels? No...
    #   Actually GS BITBLTBUF format:
    #   SBP [13:0], SBW [21:16], SPSM [29:24] | DBP [45:32], DBW [53:48], DPSM [61:56]
    #
    # Let's try to extract the texture dimensions from the data pattern

    # For R1192, the GS setup has 13 entries (0x10 to 0xA8, 12 bytes each)
    # For R2361, it has 7 entries (0x10 to 0x88, 12 bytes each, but let's count)

    # Count entries by looking for the repeating 0x34034000 pattern
    entries = []
    i = 0x10
    while i + 12 <= len(s2) and i < 0x200:
        chunk = s2[i:i+12]
        # Check if this entry contains 0x34034000
        has_gs_reg = False
        for j in range(0, 8, 4):
            if struct.unpack_from('<I', chunk, j)[0] == 0x34034000:
                has_gs_reg = True
                break
        if has_gs_reg:
            entries.append((i, chunk))
            i += 12
        else:
            break

    return entries

for idx in [1192, 2361]:
    rawfile = f"{BASE}/extracted/packdata_raw/{idx}_type02.raw"
    data = open(rawfile, 'rb').read()
    s2o = struct.unpack_from('<I', data, 24)[0]
    s2t = struct.unpack_from('<I', data, 20)[0]
    s2 = data[s2o:s2o+s2t]
    count = struct.unpack_from('<H', s2, 6)[0]

    print(f"\n{'='*60}")
    print(f"=== R{idx}: {count} entries, S2 = {s2t} bytes ===")

    gs_entries = analyze_gs_setup(s2)
    print(f"GS setup entries: {len(gs_entries)}")

    # Find start of animation/offset table (after GS entries)
    table_start = 0x10 + len(gs_entries) * 12
    print(f"Table/data starts at: +{table_start:03X}")

    # For R1192: table_start = 0x10 + 13*12 = 0x10 + 0x9C = 0xAC
    # The next 4 bytes after GS entries seem to be a header:
    # R1192: 0C FC 00 02  60 02 8F 01  00 00 00 00  00 00 00 00
    #   0x0200FC0C could be the last GS entry continuation
    #   0x018F0260 = some size/config?
    #     0x0260 = 608, 0x018F = 399

    # Let's look at what the actual pixel data looks like
    # The data blocks we found start around offset 0x100 for R1192
    # and are separated by short zero gaps

    # Skip past table to find raw pixel data
    # For R1192, the animation table seems to go from ~0xB8 to ~0x630 (first dense block)
    # Actually the first data block starts at 0x100

    # Let's try rendering the entire section 2 data region as a texture
    # Common PS2 text texture: 8bpp (256 colors), with text in white/gray on black

    if HAS_PIL:
        # Try rendering as 8bpp, various widths
        # Skip the header (first ~0xB0 bytes for R1192, ~0x88 for R2361)
        pixel_start = table_start + 8  # skip the last GS entry continuation + config
        # Actually let's find the first non-table data

        # Look for first non-zero block after all the header
        pixel_start = 0xB8 if idx == 1192 else 0x94
        pixel_data = s2[pixel_start:]

        for width in [256, 384, 512, 128, 320, 640]:
            height = min(len(pixel_data) // width, 2048)
            if height < 16:
                continue
            arr = np.frombuffer(pixel_data[:width*height], dtype=np.uint8).reshape(height, width)
            img = Image.fromarray(arr, 'L')
            fname = f'{OUT}/R{idx}_8bpp_{width}x{height}.png'
            img.save(fname)
            print(f"  Saved {fname}")

        # Also try just the dense pixel blocks
        # For R1192, try offset 0x2DF0 (start of the large 4483-byte block)
        # which looked like actual texture data
        for block_offset, block_name in [(0x100, 'early'), (0x2DF0, 'mid'), (0x3F74, 'late')]:
            if block_offset < len(s2):
                pixel_data = s2[block_offset:]
                for width in [256, 384, 512]:
                    height = min(len(pixel_data) // width, 512)
                    if height < 16:
                        continue
                    arr = np.frombuffer(pixel_data[:width*height], dtype=np.uint8).reshape(height, width)
                    img = Image.fromarray(arr, 'L')
                    fname = f'{OUT}/R{idx}_block_{block_name}_{width}x{height}.png'
                    img.save(fname)
                    print(f"  Saved {fname}")

# Also check type-03 resources near R1192 for text textures
print(f"\n{'='*60}")
print("=== Checking type-03 (texture) resources near R1192 ===")
import json
manifest = json.load(open(f'{BASE}/extracted/packdata_resources/manifest.json'))
for r in manifest:
    ri = r.get('index', -1)
    tc = r.get('type_code', 0)
    if tc == 3 and 1180 <= ri <= 1200:
        rawfile = f"{BASE}/extracted/packdata_raw/{ri}_type{tc:02d}.raw"
        if os.path.exists(rawfile):
            d = open(rawfile, 'rb').read()
            print(f"R{ri}: type-03, {len(d)} bytes, first 16: {d[:16].hex()}")
            # Check for TIM2
            if b'TIM2' in d[:16]:
                print(f"  -> TIM2 texture!")

# Check FCD_event_font resource - this is the font used for event text
# Search for the FCD resource
print(f"\n{'='*60}")
print("=== Searching for FCD_event_font resource ===")
# FCD probably stands for "File Control Data" - a named resource lookup
# Search EXE for the resource ID associated with FCD_event_font
exe = open(f'{BASE}/extracted/SLPM_653.78', 'rb').read()
# The string FCD_event_font is at 0x3F34C8
# Look at nearby code for resource IDs (small integers)
context = exe[0x3F3480:0x3F3540]
print(f"Context around FCD_event_font:")
print(f"  {context.hex()}")
