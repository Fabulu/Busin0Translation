$script = @'
import sys, struct, os
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image, ImageDraw

FONT_FILE = r'C:/Programmieren/wizardrytranslation/extracted/packdata_resources/1272_type01.bin'
EXE_FILE = r'C:/Programmieren/wizardrytranslation/extracted/SLPM_653.78'
OUTDIR = r'C:/Programmieren/wizardrytranslation/dumps/font_renders/pages'
os.makedirs(OUTDIR, exist_ok=True)

data = open(FONT_FILE, 'rb').read()
pixels_raw = data[256:]

# Unpack 4bpp - try BOTH nibble orders
raw_pixels_lo = []  # low nibble first
raw_pixels_hi = []  # high nibble first
for b in pixels_raw:
    raw_pixels_lo.append(b & 0x0F)
    raw_pixels_lo.append((b >> 4) & 0x0F)
    raw_pixels_hi.append((b >> 4) & 0x0F)
    raw_pixels_hi.append(b & 0x0F)

# The key insight: metric is NOT a pixel coordinate
# It is the GS block/page address in PSMT4 format
# For PSMT4 at 128-pixel width: each page is 128x128
# Each block is 32x16 pixels
# Block layout within page uses the block table
# The metric byte encodes WHICH BLOCK within a page

# Let me try a completely new approach:
# Since row/col likely select which 128x128 page in VRAM,
# and metric likely identifies the glyph within that page,
# I need to understand the page-to-pixel mapping

# But wait - row goes up to 15, col up to 3
# That is 16 rows x 4 cols = 64 pages of 128x128
# But we only have 256x512 = 2x4 = 8 pages!
# So row/col are NOT page indices in the atlas

# NEW HYPOTHESIS: row/col are GS VRAM block coordinates
# The GS stores textures in a specific way in VRAM
# For PSMT4 (4bpp), the page is 128x128 pixels
# Pages are arranged in VRAM as a grid

# Actually, re-reading the struct: these are 105 entries for the ASCII glyphs
# The 858 glyphs for Japanese text are loaded from resources at runtime
# So these 105 entries only cover the EXE-defined glyphs

# Let me focus on RENDERING:
# The actual atlas is 256x512 in PSMT4 format
# That gives 131072 pixels (matches our data)
# At glyph size 16x16, that is 16*32 = 512 cells
# At glyph size 12x12, NOT even divisible

# Let me try rendering the raw data as a simple bitmap
# and manually look for glyph boundaries

# First: better deswizzle using PSMT4 column deswizzle
# PSMT4 has a specific intra-block column interleave pattern

BLOCK_TABLE = [
    (0,0),(1,0),(0,1),(1,1),(0,2),(1,2),(0,3),(1,3),
    (2,0),(3,0),(2,1),(3,1),(2,2),(3,2),(2,3),(3,3),
    (0,4),(1,4),(0,5),(1,5),(0,6),(1,6),(0,7),(1,7),
    (2,4),(3,4),(2,5),(3,5),(2,6),(3,6),(2,7),(3,7),
]

# PSMT4 column table - defines column reordering within each 32-column block
# Each row of 32 columns has a specific interleave pattern
PSMT4_COL_TABLE = []
for i in range(32):
    # PSMT4 column interleave: bit manipulation
    # The actual PS2 GS column layout for PSMT4
    col = i
    # Apply column XOR based on row parity
    PSMT4_COL_TABLE.append(col)

def deswizzle_psmt4_full(raw, w, h):
    out = [0] * (w * h)
    page_w, page_h = 128, 128
    block_w, block_h = 32, 16
    pages_x = w // page_w
    pages_y = h // page_h

    for py_idx in range(pages_y):
        for px_idx in range(pages_x):
            page_base = (py_idx * pages_x + px_idx) * page_w * page_h
            for block_idx in range(32):
                bx, by = BLOCK_TABLE[block_idx]
                block_base = page_base + block_idx * block_w * block_h
                for row in range(block_h):
                    for col in range(block_w):
                        # PSMT4 intra-block column deswizzle
                        # Columns are XORed based on row number
                        # For PSMT4: XOR with 0x10 when (row & 2) != 0
                        adj_col = col
                        if (row & 2) != 0:
                            adj_col = col ^ 0x10
                            if adj_col >= block_w:
                                adj_col = col  # keep original if out of range

                        src = block_base + row * block_w + adj_col
                        if src < len(raw):
                            dst_x = px_idx * page_w + bx * block_w + col
                            dst_y = py_idx * page_h + by * block_h + row
                            if dst_x < w and dst_y < h:
                                out[dst_y * w + dst_x] = raw[src]
    return out

W, H = 256, 512

# Try multiple deswizzle approaches
desw_basic = deswizzle_psmt4_full(raw_pixels_lo, W, H)
desw_hi = deswizzle_psmt4_full(raw_pixels_hi, W, H)

def make_image(pixels, w, h, invert=False):
    img = Image.new('L', (w, h))
    if invert:
        pix = [255 - min(p * 17, 255) for p in pixels]
    else:
        pix = [min(p * 17, 255) for p in pixels]
    img.putdata(pix[:w*h])
    return img

# Save improved deswizzle attempts
for label, pix_data in [('desw_colxor_lo', desw_basic), ('desw_colxor_hi', desw_hi)]:
    img = make_image(pix_data, W, H, invert=True)
    img.save(os.path.join(OUTDIR, f'{label}_256x512.png'))
    # Also 2x zoom
    img2 = img.resize((W*2, H*2), Image.NEAREST)
    img2.save(os.path.join(OUTDIR, f'{label}_256x512_2x.png'))
    print(f'Saved {label}')

# Now try a DIFFERENT approach: direct PSMT4 to linear conversion
# using the known GS2 PSMT4 address formula
def psmt4_addr_to_linear(raw, w, h):
    out = [0] * (w * h)
    # PSMT4: each pixel is 4 bits
    # Page: 128x128 pixels
    # Block: 32x16 pixels
    # Column: 32x2 pixels (64 nibbles)
    page_w = 128
    page_h = 128
    block_w = 32
    block_h = 16

    pages_x = w // page_w
    pages_y = h // page_h

    for dst_y in range(h):
        for dst_x in range(w):
            # Which page
            px = dst_x // page_w
            py = dst_y // page_h
            # Position within page
            lx = dst_x % page_w
            ly = dst_y % page_h

            # Which block within page
            bx = lx // block_w
            by = ly // block_h
            # Block index from table
            block_idx = None
            for bi, (tbx, tby) in enumerate(BLOCK_TABLE):
                if tbx == bx and tby == by:
                    block_idx = bi
                    break
            if block_idx is None:
                continue

            # Position within block
            cx = lx % block_w
            cy = ly % block_h

            # Column reorder within block for PSMT4
            # Apply XOR for every other pair of rows
            if (cy & 2) != 0:
                cx_adj = cx ^ 0x10
                if cx_adj >= block_w:
                    cx_adj = cx
            else:
                cx_adj = cx

            # Source address
            page_base = (py * pages_x + px) * page_w * page_h
            src = page_base + block_idx * block_w * block_h + cy * block_w + cx_adj

            if src < len(raw):
                out[dst_y * w + dst_x] = raw[src]
    return out

print('Running reverse deswizzle (may take a moment)...')
rev_desw = psmt4_addr_to_linear(raw_pixels_lo, W, H)
img_rev = make_image(rev_desw, W, H, invert=True)
img_rev.save(os.path.join(OUTDIR, 'reverse_desw_256x512.png'))
img_rev2 = img_rev.resize((W*2, H*2), Image.NEAREST)
img_rev2.save(os.path.join(OUTDIR, 'reverse_desw_256x512_2x.png'))
print('Saved reverse_desw')

# Also try with nibble swap
rev_desw_hi = psmt4_addr_to_linear(raw_pixels_hi, W, H)
img_rev_hi = make_image(rev_desw_hi, W, H, invert=True)
img_rev_hi.save(os.path.join(OUTDIR, 'reverse_desw_hi_256x512.png'))
print('Saved reverse_desw_hi')

# Now overlay grids on the best results
for glyph_size in [12, 14, 16]:
    for label, base_img in [('reverse_desw', img_rev), ('reverse_desw_hi', img_rev_hi)]:
        img_rgb = base_img.copy().convert('RGB').resize((W*2, H*2), Image.NEAREST)
        draw = ImageDraw.Draw(img_rgb)
        cc = W // glyph_size
        rc = H // glyph_size
        for c in range(cc + 1):
            draw.line([(c * glyph_size * 2, 0), (c * glyph_size * 2, H*2)], fill=(255, 0, 0), width=1)
        for r in range(rc + 1):
            draw.line([(0, r * glyph_size * 2), (W*2, r * glyph_size * 2)], fill=(255, 0, 0), width=1)
        img_rgb.save(os.path.join(OUTDIR, f'{label}_grid{glyph_size}.png'))
    print(f'Saved grids for size {glyph_size}')

print('Done!')
'@
Set-Content -Path 'C:/Programmieren/wizardrytranslation/runs/CLAUDE-RUNS/RUN-20260522-1932-initial-recon/subagents/recon33-atlas-ocr/atlas_better_desw.py' -Value $script -Encoding UTF8
Write-Host "Script written OK"
