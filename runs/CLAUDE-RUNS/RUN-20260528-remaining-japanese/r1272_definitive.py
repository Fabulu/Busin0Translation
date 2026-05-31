#!/usr/bin/env python3
"""
Definitive R1272 format test: correct header offset, all decode methods.
"""
import sys, os, io
sys.path.insert(0, os.path.join("C:/Programmieren/wizardrytranslation", "tools"))
import importlib
_mod = importlib.import_module("psmt4_deswizzle")
deswizzle_psmt4 = _mod.deswizzle_psmt4

from PIL import Image

BASE = "C:/Programmieren/wizardrytranslation"
OUT = os.path.join(BASE, "runs", "CLAUDE-RUNS", "RUN-20260528-remaining-japanese")

# Load R1272 payload (skip 16-byte sub-header)
raw = open(os.path.join(BASE, "extracted", "packdata_raw", "1272_type01.raw"), "rb").read()
payload = raw[16:]  # = .bin content

# Header is 192 bytes (160 GS registers + 32 zero padding)
# "Palette" is payload[192:256] but actually first 64 bytes of pixel data (all 0xFF)
# Pixel data: payload[192:] (65536 bytes from 192 to 65728, plus remaining padding)
# But generate_font_atlas treats 192:256 as palette and 256: as pixel data

HEADER_SIZE = 192
PIXEL_OFFSET = 192  # pixel data actually starts here in the payload
# But there's the question: does the game treat the whole 65536 bytes from offset 192
# or from some other offset?

# The file has 65792 bytes of payload
# 65792 - 192 = 65600 bytes from offset 192 to end
# But we need 65536 bytes for 256x512 PSMT4
# So pixel data is payload[192:192+65536] = payload[192:65728]
# With payload[65728:65792] being trailing data (64 bytes, possibly real palette)

W, H = 256, 512
pixel_data = payload[192:192+65536]

# Check: what's in the trailing 64 bytes?
trailing = payload[65728:65792]
sys.stderr.write(f"Trailing 64 bytes (palette?): {trailing[:32].hex()}\n")
sys.stderr.write(f"  all 0xFF: {all(b == 0xFF for b in trailing)}\n")
sys.stderr.write(f"  all 0x00: {all(b == 0x00 for b in trailing)}\n")

# Method 1: VRAM deswizzle with CORRECT offset
sys.stderr.write("\n=== Method C: VRAM deswizzle (correct offset) ===\n")
deswizzled = deswizzle_psmt4(pixel_data, W, H, bw_psmt4=W, dbw_ct32=W)

img = Image.new("L", (W, H), 255)
for y in range(H):
    for x in range(W):
        val = deswizzled[y * W + x]
        img.putpixel((x, y), val * 17)

img.resize((W*2, H*2), Image.NEAREST).save(os.path.join(OUT, "r1272_correct_vram_2x.png"))

# Crop top area for detail
crop = img.crop((0, 0, 256, 128))
crop.resize((256*3, 128*3), Image.NEAREST).save(os.path.join(OUT, "r1272_correct_vram_top_3x.png"))

# Crop middle area where more glyphs should be
crop2 = img.crop((0, 128, 256, 256))
crop2.resize((256*3, 128*3), Image.NEAREST).save(os.path.join(OUT, "r1272_correct_vram_mid_3x.png"))

sys.stderr.write("  Saved r1272_correct_vram renders\n")

# Method 2: Simple linear (no swizzle at all)
sys.stderr.write("=== Method A: Simple linear ===\n")
img_lin = Image.new("L", (W, H), 255)
for y in range(H):
    for x in range(W):
        pix_idx = y * W + x
        byte_idx = pix_idx // 2
        if byte_idx >= len(pixel_data):
            break
        b = pixel_data[byte_idx]
        if pix_idx % 2 == 0:
            val = b & 0xF
        else:
            val = (b >> 4) & 0xF
        img_lin.putpixel((x, y), val * 17)

img_lin.resize((W*2, H*2), Image.NEAREST).save(os.path.join(OUT, "r1272_correct_linear_2x.png"))
crop_lin = img_lin.crop((0, 0, 256, 128))
crop_lin.resize((256*3, 128*3), Image.NEAREST).save(os.path.join(OUT, "r1272_correct_linear_top_3x.png"))
sys.stderr.write("  Saved r1272_correct_linear renders\n")

# Method 3: Page-linear (128x128 pages)
sys.stderr.write("=== Method D: Page-linear ===\n")
img_pl = Image.new("L", (W, H), 255)
for y in range(H):
    for x in range(W):
        page_col = x // 128
        page_row = y // 128
        page_idx = page_row * 2 + page_col
        local_x = x % 128
        local_y = y % 128
        pix_offset = page_idx * 128 * 128 + local_y * 128 + local_x
        byte_idx = pix_offset // 2
        if byte_idx >= len(pixel_data):
            continue
        b = pixel_data[byte_idx]
        if pix_offset % 2 == 0:
            val = b & 0xF
        else:
            val = (b >> 4) & 0xF
        img_pl.putpixel((x, y), val * 17)

img_pl.resize((W*2, H*2), Image.NEAREST).save(os.path.join(OUT, "r1272_correct_pagelinear_2x.png"))
crop_pl = img_pl.crop((0, 0, 256, 128))
crop_pl.resize((256*3, 128*3), Image.NEAREST).save(os.path.join(OUT, "r1272_correct_pagelinear_top_3x.png"))
sys.stderr.write("  Saved r1272_correct_pagelinear renders\n")

# ================================================================
# ENGLISH ATLAS: same 3 methods from correct offset
# ================================================================
eng = open(os.path.join(BASE, "build", "english_font_atlas.bin"), "rb").read()
eng_pixel = eng[256:]  # generate_font_atlas says offset 256 (192 header + 64 palette)

sys.stderr.write("\n=== ENGLISH ATLAS: 3 methods ===\n")

# VRAM deswizzle
eng_desw = deswizzle_psmt4(eng_pixel[:65536], W, H, bw_psmt4=W, dbw_ct32=W)
img_eng_v = Image.new("L", (W, H), 255)
for y in range(H):
    for x in range(W):
        val = eng_desw[y * W + x]
        img_eng_v.putpixel((x, y), val * 17)
img_eng_v.resize((W*2, H*2), Image.NEAREST).save(os.path.join(OUT, "eng_correct_vram_2x.png"))
crop_eng_v = img_eng_v.crop((0, 0, 256, 128))
crop_eng_v.resize((256*3, 128*3), Image.NEAREST).save(os.path.join(OUT, "eng_correct_vram_top_3x.png"))

# Simple linear
img_eng_l = Image.new("L", (W, H), 255)
for y in range(H):
    for x in range(W):
        pix_idx = y * W + x
        byte_idx = pix_idx // 2
        if byte_idx >= len(eng_pixel):
            break
        b = eng_pixel[byte_idx]
        if pix_idx % 2 == 0:
            val = b & 0xF
        else:
            val = (b >> 4) & 0xF
        img_eng_l.putpixel((x, y), val * 17)
img_eng_l.resize((W*2, H*2), Image.NEAREST).save(os.path.join(OUT, "eng_correct_linear_2x.png"))
crop_eng_l = img_eng_l.crop((0, 0, 256, 128))
crop_eng_l.resize((256*3, 128*3), Image.NEAREST).save(os.path.join(OUT, "eng_correct_linear_top_3x.png"))

# Page-linear
img_eng_p = Image.new("L", (W, H), 255)
for y in range(H):
    for x in range(W):
        page_col = x // 128
        page_row = y // 128
        page_idx = page_row * 2 + page_col
        local_x = x % 128
        local_y = y % 128
        pix_offset = page_idx * 128 * 128 + local_y * 128 + local_x
        byte_idx = pix_offset // 2
        if byte_idx >= len(eng_pixel):
            continue
        b = eng_pixel[byte_idx]
        if pix_offset % 2 == 0:
            val = b & 0xF
        else:
            val = (b >> 4) & 0xF
        img_eng_p.putpixel((x, y), val * 17)
img_eng_p.resize((W*2, H*2), Image.NEAREST).save(os.path.join(OUT, "eng_correct_pagelinear_2x.png"))
crop_eng_p = img_eng_p.crop((0, 0, 256, 128))
crop_eng_p.resize((256*3, 128*3), Image.NEAREST).save(os.path.join(OUT, "eng_correct_pagelinear_top_3x.png"))

sys.stderr.write("  Saved all english atlas renders\n")
sys.stderr.write("\nDONE\n")
