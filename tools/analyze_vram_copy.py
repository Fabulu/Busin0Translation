#!/usr/bin/env python3
"""
Analyze the local-to-local VRAM copy: SBP=0x1800 -> DBP=0x3000
covering ~0x380 blocks (229,376 bytes).

Steps:
1. Extract GS.bin from save state
2. Dump VRAM at SBP=0x1800 (source) and DBP=0x3000 (destination)
3. Compare them
4. Render as PSMCT32 images
5. Report findings
"""

import zipfile
import struct
import numpy as np
from PIL import Image
import os
import sys

OUT_DIR = r"C:\Programmieren\wizardrytranslation\dumps\vram_copy_analysis"

# Try multiple save states
SAVE_STATES = [
    (r"C:\Programmieren\wizardrytranslation\RAMdumps\charscreenv5.p2s", "charscreenv5"),
    (r"C:\Programmieren\wizardrytranslation\RAMdumps\32-1.p2s", "32-1"),
    (r"C:\Programmieren\wizardrytranslation\RAMdumps\fundamental.p2s", "fundamental"),
]

# VRAM copy parameters
SBP = 0x1800   # Source block pointer
DBP = 0x3000   # Destination block pointer (R1272's VRAM address)
BLOCK_COUNT = 0x380
BYTES_PER_BLOCK = 256
COPY_SIZE = BLOCK_COUNT * BYTES_PER_BLOCK  # 229,376 bytes

def extract_gs_vram(p2s_path):
    """Extract VRAM data from a PCSX2 save state."""
    with zipfile.ZipFile(p2s_path, 'r') as z:
        gs_data = z.read('GS.bin')

    # VRAM is the last 4MB of GS.bin
    vram_size = 4 * 1024 * 1024
    header_size = len(gs_data) - vram_size
    vram = gs_data[header_size:]

    print(f"  GS.bin: {len(gs_data)} bytes, header: {header_size}, VRAM: {len(vram)}")
    return gs_data, vram, header_size

def dump_region(vram, block_ptr, size, label):
    """Extract a region from VRAM given block pointer."""
    byte_offset = block_ptr * BYTES_PER_BLOCK
    end = byte_offset + size

    if end > len(vram):
        print(f"  WARNING: Region {label} extends beyond VRAM! offset={byte_offset}, end={end}, vram_size={len(vram)}")
        end = len(vram)

    data = vram[byte_offset:end]
    print(f"  {label}: block=0x{block_ptr:04X}, byte_offset=0x{byte_offset:X}, size={len(data)}")
    return data

def render_psmct32(data, width, label, out_prefix):
    """Render raw data as PSMCT32 (32-bit RGBA) image."""
    pixel_count = len(data) // 4
    height = pixel_count // width
    if height == 0:
        print(f"  Cannot render {label}: not enough data for width={width}")
        return

    usable = width * height * 4
    arr = np.frombuffer(data[:usable], dtype=np.uint8).reshape(height, width, 4)

    # PS2 uses RGBA with alpha 0x80 = fully opaque
    # Convert: RGB channels as-is, fix alpha (0x80->0xFF scale)
    rgb = arr[:, :, :3].copy()
    alpha = arr[:, :, 3].copy()
    alpha_scaled = np.minimum(alpha.astype(np.uint16) * 2, 255).astype(np.uint8)

    # Save RGB
    img_rgb = Image.fromarray(rgb, 'RGB')
    path_rgb = os.path.join(OUT_DIR, f"{out_prefix}_{label}_rgb.png")
    img_rgb.save(path_rgb)
    print(f"  Saved {path_rgb} ({width}x{height})")

    # Save RGBA
    rgba = np.dstack([rgb, alpha_scaled])
    img_rgba = Image.fromarray(rgba, 'RGBA')
    path_rgba = os.path.join(OUT_DIR, f"{out_prefix}_{label}_rgba.png")
    img_rgba.save(path_rgba)
    print(f"  Saved {path_rgba}")

    # Save alpha channel only
    img_alpha = Image.fromarray(alpha, 'L')
    path_alpha = os.path.join(OUT_DIR, f"{out_prefix}_{label}_alpha.png")
    img_alpha.save(path_alpha)
    print(f"  Saved {path_alpha}")

def render_psmt4(data, width, label, out_prefix):
    """Render raw data as PSMT4 (4-bit indexed, no palette) image."""
    # Each byte = 2 pixels (low nibble first)
    pixels = []
    for b in data:
        pixels.append(b & 0x0F)
        pixels.append((b >> 4) & 0x0F)

    pixel_count = len(pixels)
    height = pixel_count // width
    if height == 0:
        print(f"  Cannot render {label} as PSMT4: not enough data for width={width}")
        return

    usable = width * height
    arr = np.array(pixels[:usable], dtype=np.uint8).reshape(height, width)
    # Scale 0-15 to 0-255
    arr_scaled = (arr * 17).astype(np.uint8)

    img = Image.fromarray(arr_scaled, 'L')
    path = os.path.join(OUT_DIR, f"{out_prefix}_{label}_psmt4.png")
    img.save(path)
    print(f"  Saved {path} ({width}x{height})")

def analyze_state(p2s_path, state_name):
    """Full analysis of one save state."""
    print(f"\n{'='*60}")
    print(f"Analyzing: {state_name} ({p2s_path})")
    print(f"{'='*60}")

    gs_data, vram, header_size = extract_gs_vram(p2s_path)

    # Step 2: Dump source (SBP=0x1800) and destination (DBP=0x3000)
    src_data = dump_region(vram, SBP, COPY_SIZE, "SRC (SBP=0x1800)")
    dst_data = dump_region(vram, DBP, COPY_SIZE, "DST (DBP=0x3000)")

    # Save raw dumps
    src_raw_path = os.path.join(OUT_DIR, f"{state_name}_src_0x1800.bin")
    dst_raw_path = os.path.join(OUT_DIR, f"{state_name}_dst_0x3000.bin")
    with open(src_raw_path, 'wb') as f:
        f.write(src_data)
    with open(dst_raw_path, 'wb') as f:
        f.write(dst_data)

    # Step 4: Compare
    if src_data == dst_data:
        print(f"\n  RESULT: SRC and DST are IDENTICAL ({len(src_data)} bytes)")
    else:
        diff_count = sum(1 for a, b in zip(src_data, dst_data) if a != b)
        print(f"\n  RESULT: SRC and DST DIFFER in {diff_count}/{len(src_data)} bytes ({100*diff_count/len(src_data):.1f}%)")

        # Find first difference
        for i, (a, b) in enumerate(zip(src_data, dst_data)):
            if a != b:
                print(f"  First difference at offset 0x{i:X}: src=0x{a:02X}, dst=0x{b:02X}")
                break

    # Step 5: Render as PSMCT32
    # 229,376 bytes / 4 bytes per pixel = 57,344 pixels
    # At width 512: height = 57344/512 = 112 rows
    # At width 256: height = 57344/256 = 224 rows
    # At width 1024: height = 57344/1024 = 56 rows

    for width in [64, 128, 256, 512, 1024]:
        render_psmct32(src_data, width, f"src_w{width}", state_name)

    for width in [256, 512]:
        render_psmct32(dst_data, width, f"dst_w{width}", state_name)

    # Also render as PSMT4 (since R1272 is PSMT4 256x512)
    # In PSMT4, each byte = 2 pixels, so 229376 bytes = 458752 pixels
    # At width 256: height = 458752/256 = 1792
    # At width 512: height = 458752/512 = 896
    for width in [256, 512]:
        render_psmt4(dst_data, width, f"dst_psmt4_w{width}", state_name)
        render_psmt4(src_data, width, f"src_psmt4_w{width}", state_name)

    # Also dump a wider view of VRAM for context
    # Full VRAM as PSMCT32 1024-wide
    full_height = len(vram) // (1024 * 4)
    full_arr = np.frombuffer(vram[:1024*full_height*4], dtype=np.uint8).reshape(full_height, 1024, 4)
    full_img = Image.fromarray(full_arr[:,:,:3], 'RGB')
    full_path = os.path.join(OUT_DIR, f"{state_name}_full_vram_1024.png")
    full_img.save(full_path)
    print(f"\n  Full VRAM: {full_path} ({1024}x{full_height})")

    # Extract screenshot too
    try:
        with zipfile.ZipFile(p2s_path, 'r') as z:
            ss = z.read('Screenshot.png')
            ss_path = os.path.join(OUT_DIR, f"{state_name}_screenshot.png")
            with open(ss_path, 'wb') as f:
                f.write(ss)
            print(f"  Screenshot: {ss_path}")
    except:
        print("  No screenshot in save state")

    # Also look at what's around DBP=0x3000 in broader context
    # R1272 is 256x512 PSMT4 at TBP0=0x3000
    # PSMT4 256x512: 256*512/2 = 65536 bytes = 0x10000 bytes = 0x100 blocks
    # But the copy is 0x380 blocks = much larger than R1272 alone
    print(f"\n  R1272 expected size: 256x512 PSMT4 = {256*512//2} bytes = 0x{256*512//2:X} bytes = 0x{256*512//2//256:X} blocks")
    print(f"  Copy covers: 0x{BLOCK_COUNT:X} blocks = {COPY_SIZE} bytes")
    print(f"  Copy is {COPY_SIZE / (256*512//2):.1f}x the size of R1272")

    return src_data, dst_data


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    for path, name in SAVE_STATES:
        if os.path.exists(path):
            try:
                analyze_state(path, name)
            except Exception as e:
                print(f"  ERROR: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"Skipping {name}: file not found")

if __name__ == '__main__':
    main()
