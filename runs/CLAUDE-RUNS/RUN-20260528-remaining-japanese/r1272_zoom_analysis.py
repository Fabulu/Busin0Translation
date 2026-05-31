#!/usr/bin/env python3
"""Zoom analysis of R1272 and English atlas with multiple decode methods."""
import sys, os, io, struct

# Avoid stdout issues from imported modules
sys.path.insert(0, os.path.join("C:/Programmieren/wizardrytranslation", "tools"))

# Capture the deswizzle function before stdout gets mangled
import importlib
_mod = importlib.import_module("psmt4_deswizzle")
deswizzle_psmt4 = _mod.deswizzle_psmt4

# Re-wrap stdout
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)

from PIL import Image

BASE = "C:/Programmieren/wizardrytranslation"
OUT = os.path.join(BASE, "runs", "CLAUDE-RUNS", "RUN-20260528-remaining-japanese")
W, H = 256, 512

# ================================================================
# R1272 .raw - VRAM sim (verified working)
# ================================================================
sys.stderr.write("=== R1272 .raw via verified VRAM sim ===\n")
raw = open(os.path.join(BASE, "extracted", "packdata_raw", "1272_type01.raw"), "rb").read()
pixels_raw = raw[1024:1024+65536]

deswizzled = deswizzle_psmt4(pixels_raw, 256, 512, bw_psmt4=256, dbw_ct32=256)

img_vram = Image.new("L", (W, H), 0)
for y in range(H):
    for x in range(W):
        val = deswizzled[y * W + x]
        img_vram.putpixel((x, y), val * 17)
img_vram_2x = img_vram.resize((W*2, H*2), Image.NEAREST)
img_vram_2x.save(os.path.join(OUT, "r1272_vram_2x.png"))

crop = img_vram.crop((0, 0, 128, 128))
crop_4x = crop.resize((512, 512), Image.NEAREST)
crop_4x.save(os.path.join(OUT, "r1272_vram_topleft_4x.png"))

# ================================================================
# R1272 .bin - page-linear and simple linear
# ================================================================
sys.stderr.write("=== R1272 .bin ===\n")
binf = open(os.path.join(BASE, "extracted", "packdata_resources", "1272_type01.bin"), "rb").read()
sys.stderr.write(f"  .bin file size: {len(binf)} bytes\n")
bin_pixels = binf[256:]  # 192 header + 64 palette
sys.stderr.write(f"  Pixel data: {len(bin_pixels)} bytes\n")

# Page-linear decode
img_bin_pl = Image.new("L", (W, H), 0)
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
        img_bin_pl.putpixel((x, y), val * 17)

img_bin_pl_2x = img_bin_pl.resize((W*2, H*2), Image.NEAREST)
img_bin_pl_2x.save(os.path.join(OUT, "r1272_bin_pagelinear_2x.png"))

crop_bin = img_bin_pl.crop((0, 0, 128, 128))
crop_bin_4x = crop_bin.resize((512, 512), Image.NEAREST)
crop_bin_4x.save(os.path.join(OUT, "r1272_bin_pagelinear_topleft_4x.png"))

# Simple linear on .bin
img_bin_lin = Image.new("L", (W, H), 0)
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
        img_bin_lin.putpixel((x, y), val * 17)

img_bin_lin_2x = img_bin_lin.resize((W*2, H*2), Image.NEAREST)
img_bin_lin_2x.save(os.path.join(OUT, "r1272_bin_linear_2x.png"))

crop_bin_lin = img_bin_lin.crop((0, 0, 128, 128))
crop_bin_lin_4x = crop_bin_lin.resize((512, 512), Image.NEAREST)
crop_bin_lin_4x.save(os.path.join(OUT, "r1272_bin_linear_topleft_4x.png"))

# ================================================================
# ENGLISH FONT ATLAS
# ================================================================
sys.stderr.write("=== ENGLISH FONT ATLAS ===\n")
eng = open(os.path.join(BASE, "build", "english_font_atlas.bin"), "rb").read()
eng_pixels = eng[256:]  # 192 header + 64 palette

# Page-linear
img_eng_pl = Image.new("L", (W, H), 0)
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
        img_eng_pl.putpixel((x, y), val * 17)

img_eng_pl_2x = img_eng_pl.resize((W*2, H*2), Image.NEAREST)
img_eng_pl_2x.save(os.path.join(OUT, "eng_pagelinear_2x.png"))

crop_eng = img_eng_pl.crop((0, 0, 128, 128))
crop_eng_4x = crop_eng.resize((512, 512), Image.NEAREST)
crop_eng_4x.save(os.path.join(OUT, "eng_pagelinear_topleft_4x.png"))

# Simple linear on english
img_eng_lin = Image.new("L", (W, H), 0)
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
        img_eng_lin.putpixel((x, y), val * 17)

img_eng_lin_2x = img_eng_lin.resize((W*2, H*2), Image.NEAREST)
img_eng_lin_2x.save(os.path.join(OUT, "eng_linear_2x.png"))

crop_eng_lin = img_eng_lin.crop((0, 0, 128, 128))
crop_eng_lin_4x = crop_eng_lin.resize((512, 512), Image.NEAREST)
crop_eng_lin_4x.save(os.path.join(OUT, "eng_linear_topleft_4x.png"))

# ================================================================
# BYTE COMPARISON
# ================================================================
sys.stderr.write("\n=== BYTE COMPARISON ===\n")
sys.stderr.write(f"  .raw pixel data (first 32 bytes): {pixels_raw[:32].hex()}\n")
sys.stderr.write(f"  .bin pixel data (first 32 bytes): {bin_pixels[:32].hex()}\n")
match = sum(1 for a, b in zip(pixels_raw, bin_pixels[:len(pixels_raw)]) if a == b)
sys.stderr.write(f"  Byte match: {match}/{min(len(pixels_raw), len(bin_pixels))} ({100*match/min(len(pixels_raw), len(bin_pixels)):.1f}%)\n")

# Also check eng atlas vs bin
eng_match = sum(1 for a, b in zip(eng_pixels, bin_pixels[:len(eng_pixels)]) if a == b)
sys.stderr.write(f"  eng_pixels vs bin_pixels match: {eng_match}/{min(len(eng_pixels), len(bin_pixels))} ({100*eng_match/min(len(eng_pixels), len(bin_pixels)):.1f}%)\n")

sys.stderr.write("\nDONE\n")
