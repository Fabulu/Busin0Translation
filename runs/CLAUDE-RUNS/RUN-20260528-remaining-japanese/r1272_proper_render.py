#!/usr/bin/env python3
"""
Proper R1272 render with correct palette interpretation.
Game: 0=opaque (darkest), 15=transparent (lightest/background).
We render: 0->black, 15->white.
"""
import sys, os, io
sys.path.insert(0, os.path.join("C:/Programmieren/wizardrytranslation", "tools"))
import importlib
_mod = importlib.import_module("psmt4_deswizzle")
deswizzle_psmt4 = _mod.deswizzle_psmt4
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)

from PIL import Image

BASE = "C:/Programmieren/wizardrytranslation"
OUT = os.path.join(BASE, "runs", "CLAUDE-RUNS", "RUN-20260528-remaining-japanese")
W, H = 256, 512

def val_to_gray(val):
    """Game palette: 0=opaque(black), 15=transparent(white)."""
    return val * 17  # 0->0, 15->255

def val_to_gray_inv(val):
    """Inverted: 0=white(bg), 15=black(text) - for visibility."""
    return (15 - val) * 17

# ================================================================
# R1272 .raw - VRAM sim (the verified correct decode)
# ================================================================
sys.stderr.write("=== R1272 .raw VRAM sim ===\n")
raw = open(os.path.join(BASE, "extracted", "packdata_raw", "1272_type01.raw"), "rb").read()
pixels_raw = raw[1024:1024+65536]
deswizzled = deswizzle_psmt4(pixels_raw, 256, 512, bw_psmt4=256, dbw_ct32=256)

# Render with inverted palette for visibility (text=black on white bg)
img = Image.new("L", (W, H), 255)
for y in range(H):
    for x in range(W):
        val = deswizzled[y * W + x]
        img.putpixel((x, y), val_to_gray(val))

# 2x full image
img.resize((W*2, H*2), Image.NEAREST).save(os.path.join(OUT, "r1272_vram_proper_2x.png"))

# 4x crops of interesting regions
for (name, x0, y0, cw, ch) in [
    ("topleft", 0, 0, 128, 64),
    ("mid", 0, 128, 256, 64),
    ("y256", 0, 256, 256, 64),
]:
    crop = img.crop((x0, y0, x0+cw, y0+ch))
    crop.resize((cw*4, ch*4), Image.NEAREST).save(os.path.join(OUT, f"r1272_vram_{name}_4x.png"))

sys.stderr.write("  Saved r1272_vram renders\n")

# ================================================================
# R1272 .bin - page-linear
# ================================================================
sys.stderr.write("=== R1272 .bin page-linear ===\n")
binf = open(os.path.join(BASE, "extracted", "packdata_resources", "1272_type01.bin"), "rb").read()
bin_pixels = binf[256:]

img_bin = Image.new("L", (W, H), 255)
for y in range(H):
    for x in range(W):
        page_col = x // 128
        page_row = y // 128
        page_idx = page_row * 2 + page_col
        local_x = x % 128
        local_y = y % 128
        pix_offset = page_idx * 128 * 128 + local_y * 128 + local_x
        byte_idx = pix_offset // 2
        if byte_idx >= len(bin_pixels):
            continue
        b = bin_pixels[byte_idx]
        if pix_offset % 2 == 0:
            val = b & 0xF
        else:
            val = (b >> 4) & 0xF
        img_bin.putpixel((x, y), val_to_gray(val))

img_bin.resize((W*2, H*2), Image.NEAREST).save(os.path.join(OUT, "r1272_bin_pl_proper_2x.png"))
for (name, x0, y0, cw, ch) in [
    ("topleft", 0, 0, 128, 64),
    ("mid", 0, 128, 256, 64),
]:
    crop = img_bin.crop((x0, y0, x0+cw, y0+ch))
    crop.resize((cw*4, ch*4), Image.NEAREST).save(os.path.join(OUT, f"r1272_bin_pl_{name}_4x.png"))

sys.stderr.write("  Saved r1272 .bin page-linear renders\n")

# Also simple linear on .bin
img_bin_lin = Image.new("L", (W, H), 255)
for y in range(H):
    for x in range(W):
        pix_idx = y * W + x
        byte_idx = pix_idx // 2
        if byte_idx >= len(bin_pixels):
            break
        b = bin_pixels[byte_idx]
        if pix_idx % 2 == 0:
            val = b & 0xF
        else:
            val = (b >> 4) & 0xF
        img_bin_lin.putpixel((x, y), val_to_gray(val))

img_bin_lin.resize((W*2, H*2), Image.NEAREST).save(os.path.join(OUT, "r1272_bin_lin_proper_2x.png"))
for (name, x0, y0, cw, ch) in [("topleft", 0, 0, 128, 64)]:
    crop = img_bin_lin.crop((x0, y0, x0+cw, y0+ch))
    crop.resize((cw*4, ch*4), Image.NEAREST).save(os.path.join(OUT, f"r1272_bin_lin_{name}_4x.png"))

sys.stderr.write("  Saved r1272 .bin linear renders\n")

# ================================================================
# ENGLISH FONT ATLAS
# ================================================================
sys.stderr.write("=== ENGLISH FONT ATLAS ===\n")
eng = open(os.path.join(BASE, "build", "english_font_atlas.bin"), "rb").read()
eng_pixels = eng[256:]

# Page-linear
img_eng = Image.new("L", (W, H), 255)
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
        img_eng.putpixel((x, y), val_to_gray(val))

img_eng.resize((W*2, H*2), Image.NEAREST).save(os.path.join(OUT, "eng_pl_proper_2x.png"))
for (name, x0, y0, cw, ch) in [
    ("topleft", 0, 0, 128, 64),
    ("mid", 0, 128, 256, 64),
]:
    crop = img_eng.crop((x0, y0, x0+cw, y0+ch))
    crop.resize((cw*4, ch*4), Image.NEAREST).save(os.path.join(OUT, f"eng_pl_{name}_4x.png"))

sys.stderr.write("  Saved eng page-linear renders\n")

# Simple linear on english
img_eng_lin = Image.new("L", (W, H), 255)
for y in range(H):
    for x in range(W):
        pix_idx = y * W + x
        byte_idx = pix_idx // 2
        if byte_idx >= len(eng_pixels):
            break
        b = eng_pixels[byte_idx]
        if pix_idx % 2 == 0:
            val = b & 0xF
        else:
            val = (b >> 4) & 0xF
        img_eng_lin.putpixel((x, y), val_to_gray(val))

img_eng_lin.resize((W*2, H*2), Image.NEAREST).save(os.path.join(OUT, "eng_lin_proper_2x.png"))
for (name, x0, y0, cw, ch) in [("topleft", 0, 0, 128, 64)]:
    crop = img_eng_lin.crop((x0, y0, x0+cw, y0+ch))
    crop.resize((cw*4, ch*4), Image.NEAREST).save(os.path.join(OUT, f"eng_lin_{name}_4x.png"))

sys.stderr.write("  Saved eng linear renders\n")

# Check existing preview for reference
sys.stderr.write("\n=== REFERENCE: existing english_font_atlas_preview.png ===\n")
preview = Image.open(os.path.join(BASE, "build", "english_font_atlas_preview.png"))
sys.stderr.write(f"  Preview size: {preview.size}, mode: {preview.mode}\n")
# Crop top-left corner
preview_crop = preview.crop((0, 0, 128, 64))
preview_crop.resize((512, 256), Image.NEAREST).save(os.path.join(OUT, "eng_preview_topleft_4x.png"))
sys.stderr.write("  Saved eng_preview_topleft_4x.png\n")

sys.stderr.write("\nDONE\n")
