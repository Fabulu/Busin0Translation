$script = @'
import struct, os, sys
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image, ImageDraw

INPUT_FILE = r'C:/Programmieren/wizardrytranslation/extracted/packdata_resources/1272_type01.bin'
EXE_FILE = r'C:/Programmieren/wizardrytranslation/extracted/SLPM_653.78'
OUTPUT_DIR = r'C:/Programmieren/wizardrytranslation/dumps/font_renders/pages'
os.makedirs(OUTPUT_DIR, exist_ok=True)

with open(INPUT_FILE, 'rb') as f:
    data = f.read()

pixel_data = data[256:]

# Best deswizzle so far: block-level with linear column mapping
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

block_xy = {}
for by in range(8):
    for bx in range(4):
        block_xy[PSMT4_BT[by][bx]] = (bx, by)

nibbles = []
for b in pixel_data:
    nibbles.append(b & 0xF)
    nibbles.append((b >> 4) & 0xF)

def unswizzle(nibs, tw, th):
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
                for ci in range(8):
                    col_off = block_off + ci * col_nibs
                    dy_base = ci * 2
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
print('Deswizzling...')
pixels = unswizzle(nibbles, W, H)

def make_image(pix, w, h):
    img = Image.new('L', (w, h))
    d = [min(p * 17, 255) for p in pix]
    img.putdata(d[:w*h])
    return img

# Create zoomed glyph cells at 16x16
# Extract and zoom each cell 8x
cell_size = 16
zoom = 8
cols = W // cell_size  # 16
rows_to_show = 32  # 32 rows of 16px = full 512 height

# Create sheets of 16 rows at a time
for sheet_idx in range(2):
    start_row = sheet_idx * 16
    end_row = min(start_row + 16, rows_to_show)
    n_rows = end_row - start_row

    sheet_w = cols * cell_size * zoom
    sheet_h = n_rows * cell_size * zoom
    sheet = Image.new('RGB', (sheet_w, sheet_h), (255, 255, 255))

    for r in range(n_rows):
        for c in range(cols):
            for py2 in range(cell_size):
                for px2 in range(cell_size):
                    src_x = c * cell_size + px2
                    src_y = (start_row + r) * cell_size + py2
                    if src_y < H and src_x < W:
                        v = pixels[src_y * W + src_x]
                        gray = 255 - min(v * 17, 255)
                        dst_x = c * cell_size * zoom + px2 * zoom
                        dst_y = r * cell_size * zoom + py2 * zoom
                        for zx in range(zoom):
                            for zy in range(zoom):
                                if dst_x + zx < sheet_w and dst_y + zy < sheet_h:
                                    sheet.putpixel((dst_x + zx, dst_y + zy), (gray, gray, gray))

    # Draw grid
    draw = ImageDraw.Draw(sheet)
    for c in range(cols + 1):
        x = c * cell_size * zoom
        draw.line([(x, 0), (x, sheet_h)], fill=(255, 0, 0), width=2)
    for r_line in range(n_rows + 1):
        y = r_line * cell_size * zoom
        draw.line([(0, y), (sheet_w, y)], fill=(255, 0, 0), width=2)

    # Add cell indices
    for r in range(n_rows):
        for c in range(cols):
            idx = (start_row + r) * cols + c
            x = c * cell_size * zoom + 4
            y = r * cell_size * zoom + 2
            draw.text((x, y), str(idx), fill=(0, 180, 0))

    sheet.save(os.path.join(OUTPUT_DIR, f'glyphs_16x16_sheet{sheet_idx}.png'))
    print(f'Saved glyphs_16x16_sheet{sheet_idx}.png')

# Also create zoomed view of rows 2-6 (where first visible glyphs appear)
# with larger zoom (10x)
zoom2 = 10
for target_row in range(2, 8):
    row_h = cell_size * zoom2
    row_w = cols * cell_size * zoom2
    row_img = Image.new('RGB', (row_w, row_h), (255, 255, 255))

    for c in range(cols):
        for py2 in range(cell_size):
            for px2 in range(cell_size):
                src_x = c * cell_size + px2
                src_y = target_row * cell_size + py2
                if src_y < H and src_x < W:
                    v = pixels[src_y * W + src_x]
                    gray = 255 - min(v * 17, 255)
                    dst_x = c * cell_size * zoom2 + px2 * zoom2
                    dst_y = py2 * zoom2
                    for zx in range(zoom2):
                        for zy in range(zoom2):
                            if dst_x + zx < row_w and dst_y + zy < row_h:
                                row_img.putpixel((dst_x + zx, dst_y + zy), (gray, gray, gray))

    draw2 = ImageDraw.Draw(row_img)
    for c in range(cols + 1):
        x = c * cell_size * zoom2
        draw2.line([(x, 0), (x, row_h)], fill=(255, 0, 0), width=1)
    draw2.line([(0, 0), (row_w, 0)], fill=(255, 0, 0), width=1)
    draw2.line([(0, row_h-1), (row_w, row_h-1)], fill=(255, 0, 0), width=1)

    for c in range(cols):
        idx = target_row * cols + c
        x = c * cell_size * zoom2 + 2
        draw2.text((x, 2), str(idx), fill=(0, 180, 0))

    row_img.save(os.path.join(OUTPUT_DIR, f'glyph_row{target_row}_16x16_10x.png'))
    print(f'Saved glyph_row{target_row}_16x16_10x.png')

# Now analyze glyph metrics from EXE
exe = open(EXE_FILE, 'rb').read()
BASE = 0x3C0E78
f240 = struct.pack('<ff', 240.0, 240.0)
n = 0
while exe[BASE+n*28:BASE+n*28+8] == f240 and n < 2000:
    n += 1

# ASCII table
T = 0x3C0870
print('\n=== Summary of key findings ===')
print(f'Atlas: {W}x{H} PSMT4 (4bpp)')
print(f'Total pixel data: {len(pixel_data)} bytes = {len(nibbles)} nibbles')
print(f'Per-glyph EXE entries: {n}')

# Calculate glyph density
# Count non-empty 16x16 cells
nonempty = 0
for r in range(H // cell_size):
    for c in range(W // cell_size):
        has = False
        for y in range(cell_size):
            for x in range(cell_size):
                if pixels[(r*cell_size+y)*W + c*cell_size+x] > 1:  # threshold > 1 to skip near-zero
                    has = True
                    break
            if has:
                break
        if has:
            nonempty += 1

total_cells = (W // cell_size) * (H // cell_size)
print(f'Non-empty 16x16 cells (threshold>1): {nonempty}/{total_cells}')

# Find the last row with significant content
for r in range(H // cell_size - 1, -1, -1):
    total_nz = 0
    for c in range(W // cell_size):
        for y in range(cell_size):
            for x in range(cell_size):
                if pixels[(r*cell_size+y)*W + c*cell_size+x] > 1:
                    total_nz += 1
    if total_nz > 10:
        print(f'Last row with significant content: row {r} (y={r*cell_size}-{r*cell_size+15})')
        break

print('\nDone!')
'@
Set-Content -Path 'C:/Programmieren/wizardrytranslation/runs/CLAUDE-RUNS/RUN-20260522-1932-initial-recon/subagents/recon33-atlas-ocr/atlas_final_render.py' -Value $script -Encoding UTF8
Write-Host "Script written OK"
