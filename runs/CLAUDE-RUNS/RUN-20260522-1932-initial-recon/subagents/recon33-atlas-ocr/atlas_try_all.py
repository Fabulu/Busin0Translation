import struct, os, sys
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image, ImageDraw

INPUT_FILE = r'C:/Programmieren/wizardrytranslation/extracted/packdata_resources/1272_type01.bin'
OUTPUT_DIR = r'C:/Programmieren/wizardrytranslation/dumps/font_renders/pages'
os.makedirs(OUTPUT_DIR, exist_ok=True)

with open(INPUT_FILE, 'rb') as f:
    data = f.read()

pixel_data = data[256:]  # Skip 192 header + 64 palette

# Extract nibbles (low-first)
nibbles_lo = []
for b in pixel_data:
    nibbles_lo.append(b & 0xF)
    nibbles_lo.append((b >> 4) & 0xF)

# Extract nibbles (high-first)
nibbles_hi = []
for b in pixel_data:
    nibbles_hi.append((b >> 4) & 0xF)
    nibbles_hi.append(b & 0xF)

# PS2 PSMT4 unswizzle using the PCSX2-style address calculation
# Reference: PCSX2 GSLocalMemory.cpp
#
# Key insight: the PSMT4 format uses TWO levels of swizzle:
# 1. Block-level: 32 blocks within a 128x128 page (handled by block table)
# 2. Column-level: 8 columns within each 32x16 block
# 3. Pixel-level: Within each 32x2 column, pixels may be reordered

# PSMT4 block layout within page (block_number at position [row][col])
PSMT4_BT = [
    [0, 2, 8, 10],
    [1, 3, 9, 11],
    [4, 6, 12, 14],
    [5, 7, 13, 15],
    [16, 18, 24, 26],
    [17, 19, 25, 27],
    [20, 22, 28, 30],
    [21, 23, 29, 31],
]

# Build forward map: (bx, by) -> block_number
# and reverse: block_number -> (bx, by)
block_num = {}
block_xy = {}
for by in range(8):
    for bx in range(4):
        bn = PSMT4_BT[by][bx]
        block_num[(bx, by)] = bn
        block_xy[bn] = (bx, by)

# PSMT4 column layout within block
# A 32x16 block has 8 columns, each 32 pixels wide x 2 rows tall
# The columns map to display rows within the block:
# Column 0 -> rows 0-1, Column 1 -> rows 2-3, etc. (display order)
# But stored in interleaved order based on block row parity

# PCSX2 approach: The 8 stored columns in a block map to these display rows:
# For blocks in even page-rows:  col 0->rows(0,1), col 1->rows(2,3), col 2->rows(8,9), col 3->rows(10,11),
#                                 col 4->rows(4,5), col 5->rows(6,7), col 6->rows(12,13), col 7->rows(14,15)
# Wait... let me think about this differently.

# Actually, the correct PSMT4 unswizzle needs to map STORAGE position to DISPLAY position
# Storage: page -> block (in block order) -> column (in column order) -> pixel
# Display: page -> (x, y) coordinate

# Let me just try ALL possible column orderings systematically

# The standard column mapping from PCSX2 columnTable4:
# Each row within a column has 32 nibbles
# A block has 16 rows = 8 columns x 2 rows/column
# Storage column i maps to display rows:
COL_MAP_EVEN = [0, 1, 4, 5, 8, 9, 12, 13]  # display column for storage column i, even block rows
COL_MAP_ODD = [2, 3, 6, 7, 10, 11, 14, 15]  # display column for storage column i, odd block rows

# The issue: for PSMT4, BOTH even and odd mappings apply within the SAME block
# A 32x16 block has 16 rows. Columns 0-7 use one mapping, but we need all 16 rows filled
# So the block must contain data for BOTH even and odd column sets

# CORRECT interpretation: The block contains 8 columns of 32x2 pixels
# These 8 columns fill 16 rows (8 columns x 2 rows each = 16 rows)
# Column i maps to display rows [COL_MAP[i]*2, COL_MAP[i]*2+1]
# But COL_MAP values are 0-15, so display rows would be 0-31... too many!

# Wait - the COL_MAP values ARE the display row pairs
# Column 0 -> display rows 0,1 (COL_MAP_EVEN[0]=0, so rows 0*1+0, 0*1+1)
# No wait, COL_MAP_EVEN[i] gives the display column number
# Each display column is 2 rows tall
# So column 0 in even blocks -> display column 0 -> y offset 0 within block
# column 1 in even blocks -> display column 1 -> y offset 2
# column 2 in even blocks -> display column 4 -> y offset 8
# column 3 in even blocks -> display column 5 -> y offset 10

# For ODD block rows:
# column 0 -> display column 2 -> y offset 4
# column 1 -> display column 3 -> y offset 6
# column 2 -> display column 6 -> y offset 12
# column 3 -> display column 7 -> y offset 14

# Combined even+odd fills: 0,2,4,6,8,10,12,14 (all even y offsets within block)
# Plus the +1 rows: 1,3,5,7,9,11,13,15

# So the CORRECT approach is: BOTH even and odd column tables apply!
# Even block-rows handle columns 0,1,4,5,8,9,12,13 (y offsets 0,2,8,10,16,18,24,26)
# Odd block-rows handle columns 2,3,6,7,10,11,14,15 (y offsets 4,6,12,14,20,22,28,30)

# But wait - block rows and column tables are BOTH used
# Let me re-read: within a block, there are no "block rows" - there are just 8 columns
# The even/odd selection depends on the BLOCK POSITION in the page, not rows within the block

# I think the issue is that each block pair (even_row_block + odd_row_block) together
# fill a 32x32 pixel region, not a 32x16 region
# But that contradicts the 32x16 block size...

# Let me try a completely different approach: just try permutations

def unswizzle_attempt(nibs, tw, th, col_maps):
    out = [0] * (tw * th)
    pw, ph, bw, bh = 128, 128, 32, 16
    pages_x = tw // pw
    pages_y = th // ph
    page_nibs = pw * ph
    block_nibs = bw * bh
    col_nibs = bw * 2

    for pgy in range(pages_y):
        for pgx in range(pages_x):
            page_idx = pgy * pages_x + pgx
            page_off = page_idx * page_nibs
            for bn in range(32):
                bx, by = block_xy[bn]
                block_off = page_off + bn * block_nibs
                cmap = col_maps[by % 2]
                for ci in range(8):
                    col_off = block_off + ci * col_nibs
                    dy_base = cmap[ci] * 2
                    for row in range(2):
                        for nib in range(32):
                            src = col_off + row * 32 + nib
                            if src >= len(nibs):
                                continue
                            dx = pgx * pw + bx * bw + nib
                            dy = pgy * ph + by * bh + dy_base + row
                            if dx < tw and dy < th:
                                out[dy * tw + dx] = nibs[src]
    return out

W, H = 256, 512

# Try different column map combinations
attempts = {
    'both_even': ([0,1,4,5,8,9,12,13], [0,1,4,5,8,9,12,13]),
    'both_odd': ([2,3,6,7,10,11,14,15], [2,3,6,7,10,11,14,15]),
    'even_odd': ([0,1,4,5,8,9,12,13], [2,3,6,7,10,11,14,15]),
    'odd_even': ([2,3,6,7,10,11,14,15], [0,1,4,5,8,9,12,13]),
    'linear': ([0,1,2,3,4,5,6,7], [0,1,2,3,4,5,6,7]),
    'linear_offset': ([0,1,2,3,4,5,6,7], [8,9,10,11,12,13,14,15]),
}

# Also try the PS2 PSMT4 column table from actual hardware docs
# In PSMT4: 32x16 block, 8 columns of 32x2
# Column assignment: the 8 columns fill all 16 rows like this:
# col 0 -> rows 0,1
# col 1 -> rows 2,3
# col 2 -> rows 4,5
# col 3 -> rows 6,7
# col 4 -> rows 8,9
# col 5 -> rows 10,11
# col 6 -> rows 12,13
# col 7 -> rows 14,15
# Simple linear! The even/odd is for something ELSE (pixel interleave within column)
attempts['simple_linear_both'] = (list(range(8)), list(range(8)))

def make_image(pix, w, h):
    img = Image.new('L', (w, h))
    d = [min(p * 17, 255) for p in pix]
    img.putdata(d[:w*h])
    return img

for name, (cmap_even, cmap_odd) in attempts.items():
    for nib_label, nibs in [('lo', nibbles_lo), ('hi', nibbles_hi)]:
        pix = unswizzle_attempt(nibs, W, H, [cmap_even, cmap_odd])
        img = make_image(pix, W, H)
        fname = f'try_{name}_{nib_label}.png'
        img.save(os.path.join(OUTPUT_DIR, fname))

        # Check empty row pattern
        empty_count = 0
        for y in range(H):
            if sum(1 for x in range(W) if pix[y*W+x] > 0) == 0:
                empty_count += 1

        # Save zoomed top if it looks good (few empty rows)
        if empty_count < H // 4:
            crop = pix[:W*128]
            ci = make_image(crop, W, 128)
            ci.resize((W*4, 128*4), Image.NEAREST).save(os.path.join(OUTPUT_DIR, f'try_{name}_{nib_label}_top_4x.png'))

        print(f'  {fname}: {empty_count} empty rows out of {H}')

print('\nDone!')
