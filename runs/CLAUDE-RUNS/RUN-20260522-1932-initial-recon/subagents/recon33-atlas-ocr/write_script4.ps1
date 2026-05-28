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
                            src_col = COL_TABLE_EVEN[col_idx] if col_idx < len(COL_TABLE_EVEN) else col_idx
                        else:
                            src_col = COL_TABLE_ODD[col_idx] if col_idx < len(COL_TABLE_ODD) else col_idx
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

def make_image(pix, w, h):
    img = Image.new('L', (w, h))
    d = [min(p * 17, 255) for p in pix]
    img.putdata(d[:w*h])
    return img

base_img = make_image(pixels, W, H)
# Save at 3x zoom with grid overlays
for glyph_size in [10, 12, 14, 16, 18, 20]:
    scale = 3
    img_rgb = base_img.copy().convert('RGB').resize((W*scale, H*scale), Image.NEAREST)
    draw = ImageDraw.Draw(img_rgb)
    cc = W // glyph_size
    rc = H // glyph_size
    for c in range(cc + 1):
        x = c * glyph_size * scale
        draw.line([(x, 0), (x, H*scale)], fill=(255, 0, 0), width=1)
    for r in range(rc + 1):
        y = r * glyph_size * scale
        draw.line([(0, y), (W*scale, y)], fill=(255, 0, 0), width=1)
    img_rgb.save(os.path.join(OUTPUT_DIR, f'G_coldesw_grid{glyph_size}.png'))
    print(f'  Grid {glyph_size}x{glyph_size}: {cc}x{rc} = {cc*rc} cells')

# Also save zoomed sections of the top part (ASCII range)
# Top 64 rows at 6x zoom
for glyph_size in [10, 12, 14, 16]:
    crop_h = 64
    crop_data = pixels[:W*crop_h]
    crop_img = make_image(crop_data, W, crop_h)
    scale = 6
    img_rgb = crop_img.convert('RGB').resize((W*scale, crop_h*scale), Image.NEAREST)
    draw = ImageDraw.Draw(img_rgb)
    cc = W // glyph_size
    rc = crop_h // glyph_size
    for c in range(cc + 1):
        x = c * glyph_size * scale
        draw.line([(x, 0), (x, crop_h*scale)], fill=(255, 0, 0), width=1)
    for r in range(rc + 1):
        y = r * glyph_size * scale
        draw.line([(0, y), (W*scale, y)], fill=(255, 0, 0), width=1)
    img_rgb.save(os.path.join(OUTPUT_DIR, f'G_top64_grid{glyph_size}.png'))
    print(f'  Top64 grid {glyph_size}')

# Save the top 128 rows (first page) zoomed
crop_h = 128
crop_data = pixels[:W*crop_h]
crop_img = make_image(crop_data, W, crop_h)
scale = 4
img_rgb = crop_img.convert('RGB').resize((W*scale, crop_h*scale), Image.NEAREST)
img_rgb.save(os.path.join(OUTPUT_DIR, f'G_top128_4x.png'))
print('Saved G_top128_4x')

# Now extract individual glyph cells and analyze pixel density
# This helps determine the correct cell size
print('\n=== Pixel density analysis per cell size ===')
for glyph_size in [10, 12, 14, 16]:
    cc = W // glyph_size
    rc = H // glyph_size
    nonempty = 0
    total = cc * rc
    for r in range(rc):
        for c in range(cc):
            has_pixels = False
            for y in range(glyph_size):
                for x in range(glyph_size):
                    py2 = r * glyph_size + y
                    px2 = c * glyph_size + x
                    if py2 < H and px2 < W:
                        if pixels[py2 * W + px2] > 0:
                            has_pixels = True
                            break
                if has_pixels:
                    break
            if has_pixels:
                nonempty += 1
    print(f'  {glyph_size}x{glyph_size}: {nonempty}/{total} non-empty cells ({100*nonempty/total:.1f}%)')

# Find the row where characters stop having content (bottom of atlas)
print('\n=== Row occupancy ===')
for y in range(0, H, 16):
    row_pixels = sum(1 for x in range(W) for dy in range(min(16, H-y)) if pixels[(y+dy)*W+x] > 0)
    if row_pixels > 0:
        print(f'  Row y={y:3d}-{y+15}: {row_pixels} non-zero pixels')

print('\nDone!')
'@
Set-Content -Path 'C:/Programmieren/wizardrytranslation/runs/CLAUDE-RUNS/RUN-20260522-1932-initial-recon/subagents/recon33-atlas-ocr/atlas_grid_analyze.py' -Value $script -Encoding UTF8
Write-Host "Script written OK"
