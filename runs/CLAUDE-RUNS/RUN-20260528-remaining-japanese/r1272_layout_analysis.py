#!/usr/bin/env python3
"""
R1272 page layout analysis: render using 4 methods to determine format.
Also renders english_font_atlas.bin with same 4 methods.
"""
import sys, os, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from PIL import Image

BASE = "C:/Programmieren/wizardrytranslation"
OUT = os.path.join(BASE, "runs", "CLAUDE-RUNS", "RUN-20260528-remaining-japanese")

# === PCSX2 TABLES (from psmt4_deswizzle.py) ===

BLOCK_TABLE_32 = [
    [ 0,  1,  4,  5, 16, 17, 20, 21],
    [ 2,  3,  6,  7, 18, 19, 22, 23],
    [ 8,  9, 12, 13, 24, 25, 28, 29],
    [10, 11, 14, 15, 26, 27, 30, 31],
]
COLUMN_TABLE_32 = [
    [ 0,  1,  4,  5,  8,  9, 12, 13],
    [ 2,  3,  6,  7, 10, 11, 14, 15],
    [16, 17, 20, 21, 24, 25, 28, 29],
    [18, 19, 22, 23, 26, 27, 30, 31],
    [32, 33, 36, 37, 40, 41, 44, 45],
    [34, 35, 38, 39, 42, 43, 46, 47],
    [48, 49, 52, 53, 56, 57, 60, 61],
    [50, 51, 54, 55, 58, 59, 62, 63],
]
BLOCK_TABLE_4 = [
    [ 0,  2,  8, 10],[ 1,  3,  9, 11],[ 4,  6, 12, 14],[ 5,  7, 13, 15],
    [16, 18, 24, 26],[17, 19, 25, 27],[20, 22, 28, 30],[21, 23, 29, 31],
]
COLUMN_TABLE_4 = [
    [  0,   8,  32,  40,  64,  72,  96, 104,   2,  10,  34,  42,  66,  74,  98, 106,   4,  12,  36,  44,  68,  76, 100, 108,   6,  14,  38,  46,  70,  78, 102, 110],
    [ 16,  24,  48,  56,  80,  88, 112, 120,  18,  26,  50,  58,  82,  90, 114, 122,  20,  28,  52,  60,  84,  92, 116, 124,  22,  30,  54,  62,  86,  94, 118, 126],
    [ 65,  73,  97, 105,   1,   9,  33,  41,  67,  75,  99, 107,   3,  11,  35,  43,  69,  77, 101, 109,   5,  13,  37,  45,  71,  79, 103, 111,   7,  15,  39,  47],
    [ 81,  89, 113, 121,  17,  25,  49,  57,  83,  91, 115, 123,  19,  27,  51,  59,  85,  93, 117, 125,  21,  29,  53,  61,  87,  95, 119, 127,  23,  31,  55,  63],
    [192, 200, 224, 232, 128, 136, 160, 168, 194, 202, 226, 234, 130, 138, 162, 170, 196, 204, 228, 236, 132, 140, 164, 172, 198, 206, 230, 238, 134, 142, 166, 174],
    [208, 216, 240, 248, 144, 152, 176, 184, 210, 218, 242, 250, 146, 154, 178, 186, 212, 220, 244, 252, 148, 156, 180, 188, 214, 222, 246, 254, 150, 158, 182, 190],
    [129, 137, 161, 169, 193, 201, 225, 233, 131, 139, 163, 171, 195, 203, 227, 235, 133, 141, 165, 173, 197, 205, 229, 237, 135, 143, 167, 175, 199, 207, 231, 239],
    [145, 153, 177, 185, 209, 217, 241, 249, 147, 155, 179, 187, 211, 219, 243, 251, 149, 157, 181, 189, 213, 221, 245, 253, 151, 159, 183, 191, 215, 223, 247, 255],
    [256, 264, 288, 296, 320, 328, 352, 360, 258, 266, 290, 298, 322, 330, 354, 362, 260, 268, 292, 300, 324, 332, 356, 364, 262, 270, 294, 302, 326, 334, 358, 366],
    [272, 280, 304, 312, 336, 344, 368, 376, 274, 282, 306, 314, 338, 346, 370, 378, 276, 284, 308, 316, 340, 348, 372, 380, 278, 286, 310, 318, 342, 350, 374, 382],
    [321, 329, 353, 361, 257, 265, 289, 297, 323, 331, 355, 363, 259, 267, 291, 299, 325, 333, 357, 365, 261, 269, 293, 301, 327, 335, 359, 367, 263, 271, 295, 303],
    [337, 345, 369, 377, 273, 281, 305, 313, 339, 347, 371, 379, 275, 283, 307, 315, 341, 349, 373, 381, 277, 285, 309, 317, 343, 351, 375, 383, 279, 287, 311, 319],
    [448, 456, 480, 488, 384, 392, 416, 424, 450, 458, 482, 490, 386, 394, 418, 426, 452, 460, 484, 492, 388, 396, 420, 428, 454, 462, 486, 494, 390, 398, 422, 430],
    [464, 472, 496, 504, 400, 408, 432, 440, 466, 474, 498, 506, 402, 410, 434, 442, 468, 476, 500, 508, 404, 412, 436, 444, 470, 478, 502, 510, 406, 414, 438, 446],
    [385, 393, 417, 425, 449, 457, 481, 489, 387, 395, 419, 427, 451, 459, 483, 491, 389, 397, 421, 429, 453, 461, 485, 493, 391, 399, 423, 431, 455, 463, 487, 495],
    [401, 409, 433, 441, 465, 473, 497, 505, 403, 411, 435, 443, 467, 475, 499, 507, 405, 413, 437, 445, 469, 477, 501, 509, 407, 415, 439, 447, 471, 479, 503, 511],
]

def psmct32_word_addr(x, y, bw):
    PAGE_W, PAGE_H = 64, 32
    ppr = max(1, bw // PAGE_W)
    pid = (y // PAGE_H) * ppr + (x // PAGE_W)
    bid = BLOCK_TABLE_32[(y % PAGE_H) // 8][(x % PAGE_W) // 8]
    wib = COLUMN_TABLE_32[y % 8][x % 8]
    return pid * 2048 + bid * 64 + wib

def psmt4_nibble_addr(x, y, bw):
    PAGE_W, PAGE_H = 128, 128
    ppr = max(1, bw // PAGE_W)
    pid = (y // PAGE_H) * ppr + (x // PAGE_W)
    bid = BLOCK_TABLE_4[(y % PAGE_H) // 16][(x % PAGE_W) // 32]
    nib = COLUMN_TABLE_4[y % 16][x % 32]
    return pid * 16384 + bid * 512 + nib

def render_linear(data, w, h):
    """Method A: treat raw bytes as linear 4bpp, no swizzle."""
    img = Image.new("L", (w, h), 0)
    for y in range(h):
        for x in range(w):
            pix_idx = y * w + x
            byte_idx = pix_idx // 2
            if byte_idx >= len(data):
                break
            b = data[byte_idx]
            if pix_idx % 2 == 0:
                val = b & 0xF
            else:
                val = (b >> 4) & 0xF
            gray = (15 - val) * 17
            img.putpixel((x, y), gray)
    return img

def render_psmt4_native(data, w, h, bw=None):
    """Method B: PSMT4 native deswizzle (read data as if stored in PSMT4 VRAM format)."""
    if bw is None:
        bw = w
    img = Image.new("L", (w, h), 0)
    for y in range(h):
        for x in range(w):
            nib_addr = psmt4_nibble_addr(x, y, bw)
            byte_addr = nib_addr // 2
            if byte_addr >= len(data):
                continue
            b = data[byte_addr]
            if nib_addr & 1:
                val = (b >> 4) & 0xF
            else:
                val = b & 0xF
            gray = (15 - val) * 17
            img.putpixel((x, y), gray)
    return img

def render_vram_sim(data, w, h, bw_psmt4=None, dbw_ct32=None):
    """Method C: PSMCT32 upload -> PSMT4 read (full VRAM simulation)."""
    if bw_psmt4 is None:
        bw_psmt4 = w
    if dbw_ct32 is None:
        dbw_ct32 = w

    upload_w = dbw_ct32
    upload_h = len(data) // (upload_w * 4)

    vram_size = max(w * h // 2, len(data)) + 16384
    vram = bytearray(vram_size)

    for y in range(upload_h):
        for x in range(upload_w):
            host_off = (y * upload_w + x) * 4
            if host_off + 4 > len(data):
                break
            vw = psmct32_word_addr(x, y, upload_w)
            vb = vw * 4
            if vb + 4 <= len(vram):
                vram[vb:vb+4] = data[host_off:host_off+4]

    img = Image.new("L", (w, h), 0)
    for y in range(h):
        for x in range(w):
            nib_addr = psmt4_nibble_addr(x, y, bw_psmt4)
            byte_addr = nib_addr // 2
            if byte_addr >= len(vram):
                continue
            b = vram[byte_addr]
            if nib_addr & 1:
                val = (b >> 4) & 0xF
            else:
                val = b & 0xF
            gray = (15 - val) * 17
            img.putpixel((x, y), gray)
    return img

def render_page_linear(data, w, h):
    """Method D: page-linear (128x128 pages, 2 columns)."""
    img = Image.new("L", (w, h), 0)
    for y in range(h):
        for x in range(w):
            page_col = x // 128
            page_row = y // 128
            page_idx = page_row * 2 + page_col
            local_x = x % 128
            local_y = y % 128
            pix_offset = page_idx * 128 * 128 + local_y * 128 + local_x
            byte_idx = pix_offset // 2
            if byte_idx >= len(data):
                continue
            b = data[byte_idx]
            if pix_offset % 2 == 0:
                val = b & 0xF
            else:
                val = (b >> 4) & 0xF
            gray = (15 - val) * 17
            img.putpixel((x, y), gray)
    return img

def check_structure(img, label):
    """Check how many non-zero, non-max pixels exist (antialiased glyph content)."""
    pixels = list(img.getdata())
    total = len(pixels)
    zero = sum(1 for p in pixels if p == 0)
    full = sum(1 for p in pixels if p == 255)
    mid = total - zero - full
    w, h = img.size
    content_rows = 0
    for y in range(h):
        s = sum(pixels[y*w:(y+1)*w])
        if s > 0:
            content_rows += 1
    print(f"  {label}: zero={zero} full={full} mid={mid} content_rows={content_rows}/{h}")
    return mid, content_rows

# ================================================================
# R1272 ORIGINAL
# ================================================================
print("=== R1272 ORIGINAL (1272_type01.raw) ===")
raw_path = os.path.join(BASE, "extracted", "packdata_raw", "1272_type01.raw")
raw = open(raw_path, "rb").read()
print(f"  File size: {len(raw)} bytes")

r1272_header = 1024
r1272_pixels = raw[r1272_header:r1272_header+65536]
print(f"  Pixel data: {len(r1272_pixels)} bytes (offset {r1272_header})")

W, H = 256, 512

print("  Method A: LINEAR...")
img_a = render_linear(r1272_pixels, W, H)
img_a.save(os.path.join(OUT, "r1272_linear.png"))

print("  Method B: PSMT4 native deswizzle...")
img_b = render_psmt4_native(r1272_pixels, W, H)
img_b.save(os.path.join(OUT, "r1272_psmt4.png"))

print("  Method C: PSMCT32->PSMT4 VRAM simulation...")
img_c = render_vram_sim(r1272_pixels, W, H, bw_psmt4=W, dbw_ct32=W)
img_c.save(os.path.join(OUT, "r1272_vram.png"))

print("  Method D: Page-linear (128x128 pages)...")
img_d = render_page_linear(r1272_pixels, W, H)
img_d.save(os.path.join(OUT, "r1272_pagelinear.png"))

# ================================================================
# ENGLISH FONT ATLAS
# ================================================================
print("\n=== ENGLISH FONT ATLAS ===")
eng_path = os.path.join(BASE, "build", "english_font_atlas.bin")
eng = open(eng_path, "rb").read()
print(f"  File size: {len(eng)} bytes")

eng_header_size = 192
eng_palette_size = 64
eng_pixels = eng[eng_header_size + eng_palette_size:]
print(f"  Pixel data: {len(eng_pixels)} bytes (offset {eng_header_size + eng_palette_size})")

EW = 256
EH = 512

print("  Method A: LINEAR...")
img_ea = render_linear(eng_pixels, EW, EH)
img_ea.save(os.path.join(OUT, "eng_linear.png"))

print("  Method B: PSMT4 native deswizzle...")
img_eb = render_psmt4_native(eng_pixels, EW, EH)
img_eb.save(os.path.join(OUT, "eng_psmt4.png"))

print("  Method C: PSMCT32->PSMT4 VRAM simulation...")
img_ec = render_vram_sim(eng_pixels, EW, EH, bw_psmt4=EW, dbw_ct32=EW)
img_ec.save(os.path.join(OUT, "eng_vram.png"))

print("  Method D: Page-linear (128x128 pages)...")
img_ed = render_page_linear(eng_pixels, EW, EH)
img_ed.save(os.path.join(OUT, "eng_pagelinear.png"))

# ================================================================
# STRUCTURE CHECK
# ================================================================
print("\n=== ENTROPY/STRUCTURE CHECK ===")
print("R1272 (original Japanese):")
for label, img in [("LINEAR", img_a), ("PSMT4-native", img_b),
                    ("VRAM-sim", img_c), ("page-linear", img_d)]:
    check_structure(img, f"R1272 {label}")

print("\nEnglish font atlas:")
for label, img in [("LINEAR", img_ea), ("PSMT4-native", img_eb),
                    ("VRAM-sim", img_ec), ("page-linear", img_ed)]:
    check_structure(img, f"ENG {label}")

print("\nDONE")
