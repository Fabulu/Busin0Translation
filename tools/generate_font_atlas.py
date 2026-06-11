import sys, io, os, json, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# Import psmt4_deswizzle first -- it wraps sys.stdout with UTF-8 TextIOWrapper,
# which is what we want anyway, so no need to wrap again afterward.
from psmt4_deswizzle import swizzle_psmt4  # noqa: F401 (kept for potential future use)
from PIL import Image, ImageFont, ImageDraw

# Config
ATLAS_W, ATLAS_H = 256, 512  # DO NOT extend — game crashes with taller atlas
CELL_W, CELL_H = 12, 12
COLS = 21
ROWS = ATLAS_H // CELL_H  # 42 rows -> 882 cells (IDs 0-881). Tiles 882+ won't fit.
ORIGINAL = "extracted/packdata_resources/1272_type01.bin"
OUTPUT_BIN = "build/english_font_atlas.bin"
OUTPUT_PNG = "build/english_font_atlas_preview.png"

os.makedirs("build", exist_ok=True)

# Load original header (192 bytes) and palette (last 64 bytes)
orig = open(ORIGINAL, "rb").read()
header = bytearray(orig[:192])
palette = orig[-64:]  # real palette at END of file (grayscale RGBA ramp)
print(f"Original: {len(orig)} bytes, header={len(header)}, palette={len(palette)}")

# Patch TEX0 TH field if atlas extends beyond 512 pixels
# TEX0_1 register is at header offset 0x50 (8-byte value)
# TH is bits 30-33; TH=9 means 2^9=512, TH=10 means 2^10=1024
if ATLAS_H > 512:
    tex0 = struct.unpack_from('<Q', header, 0x50)[0]
    old_th = (tex0 >> 30) & 0xF
    new_th = 10  # 2^10 = 1024, enough for 540 rows
    tex0 = (tex0 & ~(0xF << 30)) | (new_th << 30)
    struct.pack_into('<Q', header, 0x50, tex0)
    print(f"  Patched TEX0 TH: {old_th} -> {new_th} (2^{new_th}={2**new_th} pixels)")
header = bytes(header)

# Load glyph table
glyph_table = json.load(open("data/english_glyph_table.json", encoding="utf-8"))

# Reverse: glyph_slot -> character
slot_to_char = {v: k for k, v in glyph_table.items()}
print(f"Glyph table: {len(glyph_table)} chars, {len(slot_to_char)} unique slots")

# Find a good font
font = None
for fp in ["C:/Windows/Fonts/consola.ttf", "C:/Windows/Fonts/arial.ttf", 
           "C:/Windows/Fonts/cour.ttf", "C:/Windows/Fonts/lucon.ttf"]:
    if os.path.exists(fp):
        font = ImageFont.truetype(fp, 10)
        print(f"Using font: {fp}")
        break
if font is None:
    font = ImageFont.load_default()
    print("Using default font")

# Create atlas image (white = transparent, black = opaque in preview)
atlas = Image.new("L", (ATLAS_W, ATLAS_H), 0)  # black background
draw = ImageDraw.Draw(atlas)

# Render each character in its glyph slot
for slot, char in slot_to_char.items():
    col = slot % COLS
    row = slot // COLS
    x = col * CELL_W
    y = row * CELL_H
    
    if x + CELL_W > ATLAS_W or y + CELL_H > ATLAS_H:
        continue
    
    # Render character centered in cell
    try:
        bbox = font.getbbox(char)
        if bbox:
            cw = bbox[2] - bbox[0]
            ch = bbox[3] - bbox[1]
            ox = x + max(0, (CELL_W - cw) // 2) - bbox[0]
            oy = y + max(0, (CELL_H - ch) // 2) - bbox[1]
            draw.text((ox, oy), char, fill=255, font=font)
    except:
        pass

# ---- DUPLICATE UPPERCASE A-Z AT SLOTS 121-146 ----
# R37 name groups (21-125) use remapped glyph IDs 121-146 for uppercase letters
# to avoid polluting the keyboard font metrics table (which uses 33-58).
# Render identical uppercase bitmaps at both 33-58 and 121-146.
#
# IMPORTANT: Do NOT use slots 95-120 — those share columns with lowercase letters
# (j-~ at slots 74-94), and the game renderer overreads glyph cells by ~4 rows,
# causing visible artifacts: subscript 'I' serif below 'r', 'P' curve below 'y',
# and 'B' stroke above 'V'. Slots 121-146 have empty neighbors on all sides.
dup_count = 0
for i in range(26):
    src_slot = 33 + i   # original A-Z
    dst_slot = 121 + i  # duplicate for names (moved from 95 to 121)
    char = chr(ord('A') + i)
    col = dst_slot % COLS
    row = dst_slot // COLS
    x = col * CELL_W
    y = row * CELL_H
    if x + CELL_W > ATLAS_W or y + CELL_H > ATLAS_H:
        continue
    try:
        bbox = font.getbbox(char)
        if bbox:
            cw = bbox[2] - bbox[0]
            ch = bbox[3] - bbox[1]
            ox = x + max(0, (CELL_W - cw) // 2) - bbox[0]
            oy = y + max(0, (CELL_H - ch) // 2) - bbox[1]
            draw.text((ox, oy), char, fill=255, font=font)
            dup_count += 1
    except:
        pass
print(f"  Duplicated {dup_count} uppercase glyphs at slots 121-146")

# ---- MENU TILE INJECTION ----
# Render English menu labels into glyph slots 683-931
try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from render_menu_tiles import load_menu_tiles
    menu_tiles = load_menu_tiles()
    for glyph_id, tile_pixels in menu_tiles.items():
        col = glyph_id % COLS
        row = glyph_id // COLS
        x0 = col * CELL_W
        y0 = row * CELL_H
        if x0 + CELL_W > ATLAS_W or y0 + CELL_H > ATLAS_H:
            continue
        # Write grayscale pixels into the atlas image
        # tile_pixels are 0-255 (0=black/bg, 255=white/text) -- same as atlas convention
        for dy in range(CELL_H):
            for dx in range(CELL_W):
                val = tile_pixels[dy * CELL_W + dx]
                atlas.putpixel((x0 + dx, y0 + dy), val)
    print(f"  Injected {len(menu_tiles)} menu tiles into atlas")
except ImportError as e:
    print(f"  WARNING: render_menu_tiles not found ({e}), skipping menu tiles")
except Exception as e:
    print(f"  WARNING: menu tile injection failed: {e}")
# ---- END MENU TILE INJECTION ----

# Save preview
atlas.save(OUTPUT_PNG)
print(f"Preview saved: {OUTPUT_PNG}")

# Convert to game's 4bpp format: LINEAR nibble-packed PSMT4
# Game format: 15 = transparent (background), 0 = fully opaque
# Our atlas: 0 = background (black), 255 = character (white)
# So invert and quantize to 4 bits.
#
# IMPORTANT: R1272 is stored on-disc as LINEAR nibble-packed PSMT4.
# The game reads it directly without a PSMCT32 deswizzle step.
# Confirmed by comparing original R1272 disc data against kanji pixel positions
# using direct nibble reads — glyphs appear at expected (x,y) positions.
# DO NOT apply swizzle_psmt4() here — that was an incorrect earlier assumption.

atlas_pixels = list(atlas.getdata())

# Build nibble-packed linear pixel array: ATLAS_W*ATLAS_H pixels, 2 pixels per byte
# Pixel (x, y) -> byte = (y*ATLAS_W + x)//2, nibble = (y*ATLAS_W + x) % 2
# low nibble = nibble 0 (even pixel), high nibble = nibble 1 (odd pixel)
pixel_data = bytearray(ATLAS_W * ATLAS_H // 2)
# Fill with transparent (0xFF = two transparent nibbles each = 0xF)
for i in range(len(pixel_data)):
    pixel_data[i] = 0xFF

for y in range(ATLAS_H):
    for x in range(ATLAS_W):
        val = atlas_pixels[y * ATLAS_W + x]
        # Convert: 255 (white/character) -> 0 (opaque), 0 (black/bg) -> 15 (transparent)
        game_val = 15 - min(val * 15 // 255, 15)
        nibble_idx = y * ATLAS_W + x
        byte_idx = nibble_idx // 2
        if nibble_idx % 2 == 0:
            pixel_data[byte_idx] = (pixel_data[byte_idx] & 0xF0) | (game_val & 0x0F)
        else:
            pixel_data[byte_idx] = (pixel_data[byte_idx] & 0x0F) | ((game_val & 0x0F) << 4)

print(f"Linear nibble-packed pixel data: {len(pixel_data)} bytes")

# Ensure we keep at least the original 65536 bytes for compatibility
min_size = 65536  # original 256x512 size
actual_size = max(min_size, len(pixel_data))
if len(pixel_data) < actual_size:
    pixel_data = pixel_data + bytearray(actual_size - len(pixel_data))

# Assemble: header + pixel data + palette
output = header + bytes(pixel_data[:actual_size]) + palette
print(f"Font atlas size: {len(output)} bytes (header={len(header)}, pixels={actual_size}, palette={len(palette)})")

with open(OUTPUT_BIN, "wb") as f:
    f.write(output)
print(f"Font atlas binary: {OUTPUT_BIN} ({len(output)} bytes)")
print("DONE!")
