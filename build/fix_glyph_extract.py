import sys, io, os, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import numpy as np
from PIL import Image

LOG = open("dumps/fix_glyph_extract_log.txt", "w", encoding="utf-8")
def log(msg):
    LOG.write(msg + "\n")
    LOG.flush()
    print(msg)

log("=== Fixing glyph extraction ===")

# Read font atlas
data = open("extracted/packdata_resources/1272_type01.bin", "rb").read()
header = data[:192]
pixel_data = data[192:192+65536]  # 65536 bytes of 4bpp pixel data
# palette is at end: data[192+65536:]

log(f"File: {len(data)} bytes, pixel data: {len(pixel_data)} bytes")

# Unpack 4bpp to pixels (low nibble first)
raw = []
for b in pixel_data:
    raw.append(b & 0x0F)
    raw.append((b >> 4) & 0x0F)
log(f"Unpacked {len(raw)} pixels")

# The atlas is 256x512 stored as 8 pages of 128x128
# Pages are arranged linearly in the file: page0, page1, page2, ..., page7
# Each page is 128*128 = 16384 pixels = 8192 bytes
PAGE_W = 128
PAGE_H = 128
PIXELS_PER_PAGE = PAGE_W * PAGE_H

# Build the full 256x512 image
# The question is: how are the 8 pages arranged?
# Option A: 2 columns x 4 rows (standard for 256x512 from 128x128 pages)
#   Page 0 = top-left, Page 1 = top-right
#   Page 2 = row1-left, Page 3 = row1-right, etc.
# Option B: Pages are stacked vertically (1 column x 8 rows = 128x1024)

# We know the atlas is 256 wide. So it must be 2 columns.
# Let's try Option A first.

ATLAS_W = 256
ATLAS_H = 512
atlas = np.zeros((ATLAS_H, ATLAS_W), dtype=np.uint8)

for page_idx in range(8):
    page_col = page_idx % 2  # 0 or 1
    page_row = page_idx // 2  # 0, 1, 2, 3
    
    page_start = page_idx * PIXELS_PER_PAGE
    page_pixels = raw[page_start:page_start + PIXELS_PER_PAGE]
    
    for py in range(PAGE_H):
        for px in range(PAGE_W):
            pixel_val = page_pixels[py * PAGE_W + px]
            atlas_x = page_col * PAGE_W + px
            atlas_y = page_row * PAGE_H + py
            atlas[atlas_y, atlas_x] = pixel_val * 17  # scale 0-15 to 0-255

# Save full atlas
img = Image.fromarray(255 - atlas)  # invert for visibility
img.save("dumps/font_renders/atlas_fixed_256x512.png")
log("Saved atlas_fixed_256x512.png")

# Now extract glyphs with correct coordinates
# Grid: 21 columns x 42 rows, 12x12 per cell
# glyph_index -> col = index % 21, row = index / 21
# pixel_x = col * 12, pixel_y = row * 12
CELL_W = 12
CELL_H = 12
COLS = 21
ROWS = 42
TOTAL_GLYPHS = COLS * ROWS  # 882

os.makedirs("dumps/glyphs_fixed", exist_ok=True)

for glyph_idx in range(TOTAL_GLYPHS):
    col = glyph_idx % COLS
    row = glyph_idx // COLS
    x = col * CELL_W
    y = row * CELL_H
    
    # Boundary check
    if x + CELL_W > ATLAS_W or y + CELL_H > ATLAS_H:
        continue
    
    cell = atlas[y:y+CELL_H, x:x+CELL_W]
    
    # Save at 4x scale
    cell_img = Image.fromarray(255 - cell)  # invert
    cell_img = cell_img.resize((CELL_W * 4, CELL_H * 4), Image.NEAREST)
    cell_img.save(f"dumps/glyphs_fixed/glyph_{glyph_idx:04d}.png")

log(f"Extracted {TOTAL_GLYPHS} glyphs to dumps/glyphs_fixed/")

# Save a composite grid
grid_img = Image.new("L", (COLS * CELL_W * 3, ROWS * CELL_H * 3), 255)
for glyph_idx in range(TOTAL_GLYPHS):
    col = glyph_idx % COLS
    row = glyph_idx // COLS
    
    cell_path = f"dumps/glyphs_fixed/glyph_{glyph_idx:04d}.png"
    if os.path.exists(cell_path):
        cell = Image.open(cell_path).resize((CELL_W * 3, CELL_H * 3), Image.NEAREST)
        grid_img.paste(cell, (col * CELL_W * 3, row * CELL_H * 3))

grid_img.save("dumps/glyphs_fixed/_grid_composite.png")
log("Saved _grid_composite.png")

# Quick sanity check: show first few glyphs
log("\nFirst 10 glyphs (non-blank pixel count):")
for i in range(10):
    cell_path = f"dumps/glyphs_fixed/glyph_{i:04d}.png"
    img = Image.open(cell_path).convert("L")
    arr = np.array(img)
    dark_pixels = np.sum(arr < 128)
    log(f"  glyph_{i:04d}: {dark_pixels} dark pixels")

log("\nGlyphs 90-100 (should be start of JP chars):")
for i in range(90, 100):
    cell_path = f"dumps/glyphs_fixed/glyph_{i:04d}.png"
    img = Image.open(cell_path).convert("L")
    arr = np.array(img)
    dark_pixels = np.sum(arr < 128)
    log(f"  glyph_{i:04d}: {dark_pixels} dark pixels")

log("\nDONE")
LOG.close()
