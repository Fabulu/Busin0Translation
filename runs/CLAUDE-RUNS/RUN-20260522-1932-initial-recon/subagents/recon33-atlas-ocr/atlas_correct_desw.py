import struct, os, sys
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image, ImageDraw

INPUT_FILE = r'C:/Programmieren/wizardrytranslation/extracted/packdata_resources/1272_type01.bin'
EXE_FILE = r'C:/Programmieren/wizardrytranslation/extracted/SLPM_653.78'
OUTPUT_DIR = r'C:/Programmieren/wizardrytranslation/dumps/font_renders/pages'
os.makedirs(OUTPUT_DIR, exist_ok=True)

with open(INPUT_FILE, 'rb') as f:
    data = f.read()

HEADER_SIZE = 192
PALETTE_SIZE = 64
pixel_data = data[HEADER_SIZE + PALETTE_SIZE:]

# ---- CORRECT PS2 GS PSMT4 unswizzle ----
# Reference: GS Users Manual, PCSX2 source code
# PSMT4 page = 128x128 pixels
# Each page = 32 blocks of 32x16 pixels
# Each block = 8 columns of 32x2 pixels = 2 sub-columns of 16x2
# The column interleaving within a block follows a specific pattern

# Block arrangement in page (block index -> x,y in blocks)
# Page is 4 blocks wide (128/32) x 8 blocks tall (128/16)
PSMT4_BLOCK_MAP = [
    [0, 2, 8, 10],
    [1, 3, 9, 11],
    [4, 6, 12, 14],
    [5, 7, 13, 15],
    [16, 18, 24, 26],
    [17, 19, 25, 27],
    [20, 22, 28, 30],
    [21, 23, 29, 31],
]

# Build reverse map: block_idx -> (bx, by)
block_pos = {}
for by_idx in range(8):
    for bx_idx in range(4):
        block_pos[PSMT4_BLOCK_MAP[by_idx][bx_idx]] = (bx_idx, by_idx)

# PSMT4 column table: maps linear column index to display column
# Within a 32x16 block, there are 8 "columns" each 32 pixels wide x 2 rows
# But the columns are interleaved
# PCSX2 uses this mapping for PSMT4:
# Even block rows: columns [0,1,4,5,8,9,12,13]
# Odd block rows:  columns [2,3,6,7,10,11,14,15]

# Each "column" is 32 nibbles wide x 2 rows = 64 nibbles = 32 bytes
# Within a column, the 32 nibbles per row are further interleaved:
# For PSMT4, every other pair of rows XORs the nibble index with 0x10

def unswizzle_psmt4_correct(raw_bytes, tw, th):
    # Extract all nibbles first
    nibbles = []
    for b in raw_bytes:
        nibbles.append(b & 0xF)
        nibbles.append((b >> 4) & 0xF)

    out = [0] * (tw * th)
    page_w, page_h = 128, 128
    block_w, block_h = 32, 16
    pages_x = tw // page_w
    pages_y = th // page_h

    page_size_nibs = page_w * page_h  # 16384 nibbles per page
    block_size_nibs = block_w * block_h  # 512 nibbles per block
    col_size_nibs = block_w * 2  # 64 nibbles per column (32 wide x 2 tall)

    for py in range(pages_y):
        for px in range(pages_x):
            page_idx = py * pages_x + px
            page_offset = page_idx * page_size_nibs

            for block_idx in range(32):
                if block_idx not in block_pos:
                    continue
                bx, by = block_pos[block_idx]
                block_offset = page_offset + block_idx * block_size_nibs

                for col_idx in range(8):  # 8 columns per block
                    col_offset = block_offset + col_idx * col_size_nibs

                    # Determine display column position
                    # Even block rows use even column indices, odd use odd
                    if by % 2 == 0:
                        display_col = [0, 1, 4, 5, 8, 9, 12, 13][col_idx]
                    else:
                        display_col = [2, 3, 6, 7, 10, 11, 14, 15][col_idx]

                    display_y_base = display_col * 2  # Each display column is 2 rows

                    for row in range(2):  # 2 rows per column
                        for nib in range(32):  # 32 nibbles per row
                            src_idx = col_offset + row * 32 + nib
                            if src_idx >= len(nibbles):
                                continue

                            # Apply nibble-level interleave
                            # In PSMT4, nibbles within a row may be reordered
                            # The standard interleave: XOR with 0x10 for odd column pairs
                            actual_nib = nib

                            dst_x = px * page_w + bx * block_w + actual_nib
                            dst_y = py * page_h + by * block_h + display_y_base + row

                            if dst_x < tw and dst_y < th:
                                out[dst_y * tw + dst_x] = nibbles[src_idx]

    return out

# Alternative: try the simplest possible approach
# Just read nibbles linearly and place them using GS address formula
def gs_psmt4_addr(x, y, tw):
    # GS PSMT4 address calculation
    page_w, page_h = 128, 128
    block_w, block_h = 32, 16

    px = x // page_w
    py = y // page_h
    pages_x = tw // page_w
    page_idx = py * pages_x + px

    lx = x % page_w
    ly = y % page_h

    bx = lx // block_w
    by = ly // block_h

    # Find block index from position
    block_idx = PSMT4_BLOCK_MAP[by][bx]

    cx = lx % block_w
    cy = ly % block_h

    # Column within block
    col_in_block = cy // 2
    row_in_col = cy % 2

    # Column interleave
    if by % 2 == 0:
        col_table = [0, 1, 4, 5, 8, 9, 12, 13]
    else:
        col_table = [2, 3, 6, 7, 10, 11, 14, 15]

    # Reverse lookup: find which storage column index maps to this display column
    try:
        storage_col = col_table.index(col_in_block)
    except ValueError:
        # This display column is not in this block row group
        return -1

    page_size = page_w * page_h
    block_size = block_w * block_h
    col_size = block_w * 2

    addr = page_idx * page_size + block_idx * block_size + storage_col * col_size + row_in_col * 32 + cx
    return addr

W, H = 256, 512
print('Method 1: unswizzle_psmt4_correct...')
pix1 = unswizzle_psmt4_correct(pixel_data, W, H)

def make_image(pix, w, h):
    img = Image.new('L', (w, h))
    d = [min(p * 17, 255) for p in pix]
    img.putdata(d[:w*h])
    return img

img1 = make_image(pix1, W, H)
img1.save(os.path.join(OUTPUT_DIR, 'unswiz_method1.png'))
print('  Saved unswiz_method1.png')

# Save top portion zoomed
crop_h = 128
crop = pix1[:W*crop_h]
crop_img = make_image(crop, W, crop_h)
crop_img.resize((W*4, crop_h*4), Image.NEAREST).save(os.path.join(OUTPUT_DIR, 'unswiz_method1_top128_4x.png'))
print('  Saved unswiz_method1_top128_4x.png')

# Method 2: use gs address formula to read pixels
print('Method 2: GS address formula...')
pix2 = [0] * (W * H)

# Extract nibbles
nibbles = []
for b in pixel_data:
    nibbles.append(b & 0xF)
    nibbles.append((b >> 4) & 0xF)

for y in range(H):
    for x in range(W):
        addr = gs_psmt4_addr(x, y, W)
        if 0 <= addr < len(nibbles):
            pix2[y * W + x] = nibbles[addr]

img2 = make_image(pix2, W, H)
img2.save(os.path.join(OUTPUT_DIR, 'unswiz_method2.png'))
print('  Saved unswiz_method2.png')

crop2 = pix2[:W*crop_h]
crop_img2 = make_image(crop2, W, crop_h)
crop_img2.resize((W*4, crop_h*4), Image.NEAREST).save(os.path.join(OUTPUT_DIR, 'unswiz_method2_top128_4x.png'))
print('  Saved unswiz_method2_top128_4x.png')

# Method 3: try nibble-swapped version of method 2
print('Method 3: GS address formula with nibble swap...')
nibbles_sw = []
for b in pixel_data:
    nibbles_sw.append((b >> 4) & 0xF)
    nibbles_sw.append(b & 0xF)

pix3 = [0] * (W * H)
for y in range(H):
    for x in range(W):
        addr = gs_psmt4_addr(x, y, W)
        if 0 <= addr < len(nibbles_sw):
            pix3[y * W + x] = nibbles_sw[addr]

img3 = make_image(pix3, W, H)
img3.save(os.path.join(OUTPUT_DIR, 'unswiz_method3.png'))
crop3 = pix3[:W*crop_h]
crop_img3 = make_image(crop3, W, crop_h)
crop_img3.resize((W*4, crop_h*4), Image.NEAREST).save(os.path.join(OUTPUT_DIR, 'unswiz_method3_top128_4x.png'))
print('  Saved unswiz_method3.png')

# Analyze empty rows for method 2
print('\n=== Row analysis for method 2 ===')
for y in range(min(32, H)):
    count = sum(1 for x in range(W) if pix2[y * W + x] > 0)
    if count > 0 or y < 20:
        print(f'  y={y:3d}: {count} non-zero pixels')

# Find vertical gaps
print('\nEmpty row ranges:')
in_gap = True
gap_start = 0
for y in range(H):
    count = sum(1 for x in range(W) if pix2[y * W + x] > 0)
    if count == 0:
        if not in_gap:
            gap_start = y
            in_gap = True
    else:
        if in_gap:
            if y > gap_start:
                print(f'  Empty: y={gap_start}-{y-1} ({y-gap_start} rows)')
            in_gap = False
if in_gap and gap_start < H:
    print(f'  Empty: y={gap_start}-{H-1} ({H-gap_start} rows)')

print('\nDone!')
