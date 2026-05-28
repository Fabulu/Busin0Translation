$script = @'
import struct, os, sys
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image, ImageDraw, ImageFont

INPUT_FILE = r'C:/Programmieren/wizardrytranslation/extracted/packdata_resources/1272_type01.bin'
EXE_FILE = r'C:/Programmieren/wizardrytranslation/extracted/SLPM_653.78'
OUTPUT_DIR = r'C:/Programmieren/wizardrytranslation/dumps/font_renders/pages'
os.makedirs(OUTPUT_DIR, exist_ok=True)

with open(INPUT_FILE, 'rb') as f:
    data = f.read()

HEADER_SIZE = 192
PALETTE_SIZE = 64
pixel_data = data[HEADER_SIZE + PALETTE_SIZE:]

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

COL_TABLE_EVEN = [0, 1, 4, 5, 8, 9, 12, 13]
COL_TABLE_ODD = [2, 3, 6, 7, 10, 11, 14, 15]

def psmt4_full_deswizzle(raw, tw, th, ns=False):
    pixels = [0] * (tw * th)
    pw, ph, bw, bh = 128, 128, 32, 16
    col_w, col_h = 32, 2
    pxc = (tw + pw - 1) // pw
    pyc = (th + ph - 1) // ph
    col_size = (col_w * col_h) // 2
    bs = (bw * bh) // 2
    ps = 32 * bs
    for pgy in range(pyc):
        for pgx in range(pxc):
            pi = pgy * pxc + pgx
            po = pi * ps
            for br in range(8):
                for bc in range(4):
                    bn = PSMT4_BT[br][bc]
                    bo = po + bn * bs
                    bx = pgx * pw + bc * bw
                    by = pgy * ph + br * bh
                    for col_idx in range(8):
                        col_off = bo + col_idx * col_size
                        if br % 2 == 0:
                            src_col = COL_TABLE_EVEN[col_idx]
                        else:
                            src_col = COL_TABLE_ODD[col_idx]
                        col_y = src_col * 2
                        for py2 in range(col_h):
                            for px2 in range(col_w):
                                pidx = py2 * col_w + px2
                                bi = col_off + pidx // 2
                                if bi >= len(raw):
                                    continue
                                bv = raw[bi]
                                if ns:
                                    ci = ((bv >> 4) & 0xF) if pidx % 2 == 0 else (bv & 0xF)
                                else:
                                    ci = (bv & 0xF) if pidx % 2 == 0 else ((bv >> 4) & 0xF)
                                dx = bx + px2
                                dy = by + col_y + py2
                                if dx < tw and dy < th:
                                    pixels[dy * tw + dx] = ci
    return pixels

W, H = 256, 512
print('Deswizzling...')
pixels = psmt4_full_deswizzle(pixel_data, W, H, ns=True)

# Load EXE data for glyph properties
exe = open(EXE_FILE, 'rb').read()
BASE = 0x3C0E78
f240 = struct.pack('<ff', 240.0, 240.0)
n = 0
while exe[BASE+n*28:BASE+n*28+8] == f240 and n < 2000:
    n += 1

glyph_props = []
for i in range(n):
    o = BASE + i * 28
    metric = exe[o+9]
    atlas_row = exe[o+17]
    atlas_col = exe[o+18]
    glyph_props.append((i, metric, atlas_row, atlas_col))

# ASCII glyph table
T = 0x3C0870
ascii_map = []
for j in range(84):
    o = T + j * 2
    v = struct.unpack_from('<H', exe, o)[0]
    ascii_char = chr(0x20 + j) if 0x20 + j < 127 else '?'
    ascii_map.append((0x20 + j, ascii_char, v))

# Now the key analysis: look at the metric byte as a GS address
# In GS PSMT4 format:
# The page (128x128) is divided into 32 blocks (32x16 each)
# Blocks are indexed using the PSMT4_BT table
# Each block has 8 columns of 32x2 pixels each
# The column interleaving is defined by COL_TABLE_EVEN/ODD

# The metric byte might encode the block + column within a page
# Let me try: metric bits as [block_row:3][block_col:2][column:3]
# or [column:3][block_col:2][block_row:3]

# Actually, given the patterns we see, let me try interpreting metric
# as a direct Y pixel coordinate within a texture page
# row,col select the page in VRAM

# Key: for row=1,col=3: metrics=[7,22,37,52,67,82,97,112] spaced by 15
# 15 is suspicious - what if the glyph height is 15 pixels?
# And the page height is 128, so 128/15 = 8.5, not exact
# But 8 glyphs * 15 = 120, leaving 8 pixels margin

# Or if glyph height is 16: 128/16 = 8, and metrics are 0-indexed Y coords?
# Then metric=7 means y=7*... something
# But the range 7-112 with step 15 suggests metric IS the Y pixel position
# 7, 22, 37, 52, 67, 82, 97, 112 -> 8 values, last is 112
# If each glyph is 16px tall: 112 + 16 = 128 = page height!

# But for row=0,col=0: metrics=[15,30,90,150,180,240]
# 240 + 16 = 256 -- which is the page height for 256x256 textures!
# And the spacing is NOT uniform (15,60,60,30,60)

# Wait -- the font descriptor says tex_dim = 256x256
# So row/col might NOT be page indices in the atlas
# They might be something else entirely

# Let me just look at where the visible glyphs are in the deswizzled image
# and try to match them to known characters

# Extract glyph cells at various sizes and dump pixel patterns
print('\n=== Extracting glyph cells ===')

# Look for non-zero pixel clusters to find glyph boundaries
# Scan each row for the first and last non-zero pixel
print('\nRow-by-row first/last non-zero pixel:')
for y in range(min(128, H)):
    first_x = -1
    last_x = -1
    count = 0
    for x in range(W):
        if pixels[y * W + x] > 0:
            if first_x == -1:
                first_x = x
            last_x = x
            count += 1
    if count > 0:
        print(f'  y={y:3d}: first_x={first_x:3d} last_x={last_x:3d} count={count:3d}')

# Look for vertical gaps (empty rows between glyph rows)
print('\n=== Vertical gap analysis (first 256 rows) ===')
empty_rows = []
for y in range(min(256, H)):
    total = sum(1 for x in range(W) if pixels[y * W + x] > 0)
    if total == 0:
        empty_rows.append(y)
print(f'Empty rows in first 256: {empty_rows[:50]}')

# Find clusters of non-empty rows
print('\n=== Non-empty row clusters ===')
in_cluster = False
cluster_start = -1
clusters = []
for y in range(H):
    total = sum(1 for x in range(W) if pixels[y * W + x] > 0)
    if total > 0:
        if not in_cluster:
            cluster_start = y
            in_cluster = True
    else:
        if in_cluster:
            clusters.append((cluster_start, y - 1, y - cluster_start))
            in_cluster = False
if in_cluster:
    clusters.append((cluster_start, H-1, H - cluster_start))

print(f'Total clusters: {len(clusters)}')
for c in clusters[:30]:
    print(f'  y={c[0]:3d}-{c[1]:3d} height={c[2]:3d}')

# Look for vertical gaps in columns to find cell boundaries
print('\n=== Column gap analysis (first 256 cols, rows 0-32) ===')
empty_cols = []
for x in range(W):
    total = sum(1 for y in range(min(64, H)) if pixels[y * W + x] > 0)
    if total == 0:
        empty_cols.append(x)
print(f'Empty cols in first 64 rows: {empty_cols[:80]}')

# Now render individual glyph cells with labels
# Based on the pattern, glyphs appear in the left half first
# Let me extract 16x16 cells from the top-left and label them
print('\n=== Creating labeled glyph sheet ===')
cell_size = 16
zoom = 8
cols = W // cell_size  # 16
rows = 8  # just first 8 rows
sheet_w = cols * cell_size * zoom
sheet_h = rows * cell_size * zoom
sheet = Image.new('RGB', (sheet_w, sheet_h), (255, 255, 255))
draw = ImageDraw.Draw(sheet)

for r in range(rows):
    for c in range(cols):
        for py2 in range(cell_size):
            for px2 in range(cell_size):
                src_x = c * cell_size + px2
                src_y = r * cell_size + py2
                if src_y < H and src_x < W:
                    v = pixels[src_y * W + src_x]
                    gray = min(v * 17, 255)
                    # Invert for visibility
                    col_val = 255 - gray
                    dst_x = c * cell_size * zoom + px2 * zoom
                    dst_y = r * cell_size * zoom + py2 * zoom
                    for zx in range(zoom):
                        for zy in range(zoom):
                            sheet.putpixel((dst_x + zx, dst_y + zy), (col_val, col_val, col_val))

# Draw grid
for c in range(cols + 1):
    x = c * cell_size * zoom
    draw.line([(x, 0), (x, sheet_h)], fill=(255, 0, 0), width=2)
for r in range(rows + 1):
    y = r * cell_size * zoom
    draw.line([(0, y), (sheet_w, y)], fill=(255, 0, 0), width=2)

# Add cell indices
for r in range(rows):
    for c in range(cols):
        idx = r * cols + c
        x = c * cell_size * zoom + 4
        y = r * cell_size * zoom + 2
        draw.text((x, y), f'{idx}', fill=(0, 255, 0))

sheet.save(os.path.join(OUTPUT_DIR, 'glyph_cells_16x16_top8rows.png'))
print('Saved glyph_cells_16x16_top8rows.png')

print('\nDone!')
'@
Set-Content -Path 'C:/Programmieren/wizardrytranslation/runs/CLAUDE-RUNS/RUN-20260522-1932-initial-recon/subagents/recon33-atlas-ocr/atlas_cell_extract.py' -Value $script -Encoding UTF8
Write-Host "Script written OK"
