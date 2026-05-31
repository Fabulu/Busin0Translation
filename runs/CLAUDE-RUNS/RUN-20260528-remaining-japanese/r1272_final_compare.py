#!/usr/bin/env python3
"""
Final comparison: render R1272 and English atlas at full size with 3x zoom.
Focus on determining which decode method shows readable glyphs.
"""
import sys, os, io
sys.path.insert(0, os.path.join("C:/Programmieren/wizardrytranslation", "tools"))
import importlib
_mod = importlib.import_module("psmt4_deswizzle")
deswizzle_psmt4 = _mod.deswizzle_psmt4
swizzle_psmt4 = _mod.swizzle_psmt4

from PIL import Image

BASE = "C:/Programmieren/wizardrytranslation"
OUT = os.path.join(BASE, "runs", "CLAUDE-RUNS", "RUN-20260528-remaining-japanese")
W, H = 256, 512

# ================================================================
# KEY TEST: Take the english_font_atlas preview, encode it to page-linear,
# then VRAM-swizzle it, and see what comes out.
# ================================================================
sys.stderr.write("=== KEY TEST: English atlas encode/decode round-trip ===\n")

# Load the preview (ground truth)
preview = Image.open(os.path.join(BASE, "build", "english_font_atlas_preview.png")).convert("L")
sys.stderr.write(f"  Preview: {preview.size}\n")

# The generate_font_atlas.py encodes in page-linear format.
# It then writes: header + pixel_data + palette
# The game reads it via PSMCT32 upload to VRAM, then PSMT4 read.
# So for the game to see correct glyphs, the page-linear data must
# equal what the PSMCT32 upload produces, or there must be a swizzle step.

# Let's check: take the english_font_atlas.bin pixel data and try
# VRAM deswizzle on it (treating it as PSMCT32 upload format)
eng = open(os.path.join(BASE, "build", "english_font_atlas.bin"), "rb").read()
eng_pixels = eng[256:]  # skip header+palette

# Method 1: VRAM deswizzle (PSMCT32 upload -> PSMT4 read)
sys.stderr.write("  VRAM deswizzle of english atlas...\n")
eng_deswizzled = deswizzle_psmt4(eng_pixels[:65536], 256, 512, bw_psmt4=256, dbw_ct32=256)

img_eng_vram = Image.new("L", (W, H), 255)
for y in range(H):
    for x in range(W):
        val = eng_deswizzled[y * W + x]
        # 0=opaque->black, 15=transparent->white
        img_eng_vram.putpixel((x, y), val * 17)

# Save 2x for visibility
img_eng_vram.resize((W*2, H*2), Image.NEAREST).save(os.path.join(OUT, "eng_vram_deswiz_2x.png"))
sys.stderr.write("  Saved eng_vram_deswiz_2x.png\n")

# ================================================================
# CRITICAL TEST: What if we SWIZZLE the english atlas data first,
# then inject it as the .raw file?
# The .raw file format expects PSMCT32 upload data.
# The .bin page-linear data needs to be swizzled to become .raw data.
# ================================================================
sys.stderr.write("\n=== SWIZZLE TEST ===\n")

# Reconstruct linear pixel indices from the page-linear .bin data
# generate_font_atlas.py stores page-linear indexed pixels
eng_linear_pixels = bytearray(W * H)
for y in range(H):
    for x in range(W):
        page_col = x // 128
        page_row = y // 128
        page_idx = page_row * 2 + page_col
        local_x = x % 128
        local_y = y % 128
        pix_offset = page_idx * 128 * 128 + local_y * 128 + local_x
        byte_idx = pix_offset // 2
        if byte_idx >= len(eng_pixels):
            continue
        b = eng_pixels[byte_idx]
        if pix_offset % 2 == 0:
            val = b & 0xF
        else:
            val = (b >> 4) & 0xF
        eng_linear_pixels[y * W + x] = val

# Now swizzle these linear pixels into PSMCT32 upload format
sys.stderr.write("  Swizzling english atlas linear->PSMCT32...\n")
eng_swizzled = swizzle_psmt4(eng_linear_pixels, 256, 512, bw_psmt4=256, dbw_ct32=256)
sys.stderr.write(f"  Swizzled size: {len(eng_swizzled)} bytes\n")

# Round-trip: deswizzle the swizzled data
eng_roundtrip = deswizzle_psmt4(eng_swizzled, 256, 512, bw_psmt4=256, dbw_ct32=256)

img_eng_rt = Image.new("L", (W, H), 255)
for y in range(H):
    for x in range(W):
        val = eng_roundtrip[y * W + x]
        img_eng_rt.putpixel((x, y), val * 17)

img_eng_rt.resize((W*2, H*2), Image.NEAREST).save(os.path.join(OUT, "eng_roundtrip_2x.png"))
sys.stderr.write("  Saved eng_roundtrip_2x.png\n")

# ================================================================
# R1272 .raw VRAM deswizzle (verified correct)
# ================================================================
sys.stderr.write("\n=== R1272 .raw VRAM deswizzle ===\n")
raw = open(os.path.join(BASE, "extracted", "packdata_raw", "1272_type01.raw"), "rb").read()
pixels_raw = raw[1024:1024+65536]
r1272_deswizzled = deswizzle_psmt4(pixels_raw, 256, 512, bw_psmt4=256, dbw_ct32=256)

img_r1272 = Image.new("L", (W, H), 255)
for y in range(H):
    for x in range(W):
        val = r1272_deswizzled[y * W + x]
        img_r1272.putpixel((x, y), val * 17)

img_r1272.resize((W*2, H*2), Image.NEAREST).save(os.path.join(OUT, "r1272_vram_deswiz_proper_2x.png"))
sys.stderr.write("  Saved r1272_vram_deswiz_proper_2x.png\n")

# Crop a middle section showing kanji
crop = img_r1272.crop((0, 200, 256, 300))
crop.resize((256*3, 100*3), Image.NEAREST).save(os.path.join(OUT, "r1272_kanji_crop_3x.png"))
sys.stderr.write("  Saved r1272_kanji_crop_3x.png\n")

# ================================================================
# FORMAT COMPARISON SUMMARY
# ================================================================
sys.stderr.write("\n=== FORMAT SUMMARY ===\n")
sys.stderr.write(f"  R1272 .raw: 1024-byte header + 65536 pixel data + 1024 CLUT\n")
sys.stderr.write(f"  R1272 .raw pixel format: PSMCT32 upload data (needs VRAM sim to decode)\n")
sys.stderr.write(f"  English .bin: 192-byte header + 64 palette + {len(eng_pixels)} pixel data\n")
sys.stderr.write(f"  English .bin pixel format: page-linear (128x128 pages, 2 columns)\n")

# Check if round-trip matches original
match = sum(1 for a, b in zip(eng_linear_pixels, eng_roundtrip) if a == b)
sys.stderr.write(f"  English round-trip match: {match}/{len(eng_linear_pixels)} ({100*match/len(eng_linear_pixels):.1f}%)\n")

# Compare the .raw format (PSMCT32) with the .bin page-linear format
sys.stderr.write(f"\n  .raw pixel data (PSMCT32 format) != .bin pixel data (page-linear format)\n")
sys.stderr.write(f"  These are TWO DIFFERENT encodings of the same image.\n")
sys.stderr.write(f"  .raw is what the game uploads to VRAM via GS IMAGE transfer (DMA)\n")
sys.stderr.write(f"  .bin is a tool-friendly intermediate format\n")
sys.stderr.write(f"\n  CRITICAL: english_font_atlas.bin uses page-linear format\n")
sys.stderr.write(f"  but the game expects PSMCT32 upload format in PACKDATA!\n")
sys.stderr.write(f"  The build pipeline must convert page-linear -> PSMCT32 before injection.\n")

sys.stderr.write("\nDONE\n")
