import sys, struct, os
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image, ImageDraw

FONT_FILE = r'C:/Programmieren/wizardrytranslation/extracted/packdata_resources/1272_type01.bin'
EXE_FILE = r'C:/Programmieren/wizardrytranslation/extracted/SLPM_653.78'
OUTDIR = r'C:/Programmieren/wizardrytranslation/dumps/font_renders/pages'
os.makedirs(OUTDIR, exist_ok=True)

data = open(FONT_FILE, 'rb').read()
pixels_raw = data[256:]

raw_pixels = []
for b in pixels_raw:
    raw_pixels.append(b & 0x0F)
    raw_pixels.append((b >> 4) & 0x0F)
print(f'Total raw pixels: {len(raw_pixels)}')

BLOCK_TABLE = [
    (0,0),(1,0),(0,1),(1,1),(0,2),(1,2),(0,3),(1,3),
    (2,0),(3,0),(2,1),(3,1),(2,2),(3,2),(2,3),(3,3),
    (0,4),(1,4),(0,5),(1,5),(0,6),(1,6),(0,7),(1,7),
    (2,4),(3,4),(2,5),(3,5),(2,6),(3,6),(2,7),(3,7),
]

def deswizzle_psmt4(raw, w, h):
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
                        src = block_base + row * block_w + col
                        if src < len(raw):
                            dst_x = px_idx * page_w + bx * block_w + col
                            dst_y = py_idx * page_h + by * block_h + row
                            if dst_x < w and dst_y < h:
                                out[dst_y * w + dst_x] = raw[src]
    return out

W, H = 256, 512
desw = deswizzle_psmt4(raw_pixels, W, H)

def make_image(pixels, w, h, invert=False):
    img = Image.new('L', (w, h))
    if invert:
        pix = [255 - min(p * 17, 255) for p in pixels]
    else:
        pix = [min(p * 17, 255) for p in pixels]
    img.putdata(pix[:w*h])
    return img

print('\n=== Rendering 128x128 pages from RAW data ===')
raw_w = 128
raw_h = len(raw_pixels) // raw_w
n_pages_raw = raw_h // 128
print(f'Raw at 128w: {raw_w}x{raw_h}, {n_pages_raw} pages')
for pg in range(min(n_pages_raw, 8)):
    start = pg * 128 * 128
    page_data = raw_pixels[start:start + 128*128]
    img = make_image(page_data, 128, 128)
    img_inv = make_image(page_data, 128, 128, invert=True)
    img.resize((512, 512), Image.NEAREST).save(os.path.join(OUTDIR, f'raw_page{pg}_128x128.png'))
    img_inv.resize((512, 512), Image.NEAREST).save(os.path.join(OUTDIR, f'raw_page{pg}_128x128_inv.png'))
    print(f'  Saved raw page {pg}')

print('\n=== Rendering 128x128 pages from DESWIZZLED 256x512 ===')
for py in range(4):
    for px in range(2):
        page_data = []
        for row in range(128):
            for col in range(128):
                x = px * 128 + col
                y = py * 128 + row
                page_data.append(desw[y * W + x])
        pg_idx = py * 2 + px
        img = make_image(page_data, 128, 128)
        img_inv = make_image(page_data, 128, 128, invert=True)
        img.resize((512, 512), Image.NEAREST).save(os.path.join(OUTDIR, f'desw_page{pg_idx}_128x128.png'))
        img_inv.resize((512, 512), Image.NEAREST).save(os.path.join(OUTDIR, f'desw_page{pg_idx}_128x128_inv.png'))
        print(f'  Saved desw page {pg_idx} (col={px}, row={py})')

print('\n=== Grid overlay tests ===')
for glyph_size in [10, 12, 14, 16]:
    page_data = [desw[row * W + col] for row in range(128) for col in range(128)]
    img = make_image(page_data, 128, 128, invert=True).convert('RGB').resize((512, 512), Image.NEAREST)
    draw = ImageDraw.Draw(img)
    scale = 4
    cc = 128 // glyph_size
    rc = 128 // glyph_size
    for c in range(cc + 1):
        draw.line([(c * glyph_size * scale, 0), (c * glyph_size * scale, 512)], fill=(255, 0, 0), width=1)
    for r in range(rc + 1):
        draw.line([(0, r * glyph_size * scale), (512, r * glyph_size * scale)], fill=(255, 0, 0), width=1)
    img.save(os.path.join(OUTDIR, f'desw_page0_grid{glyph_size}x{glyph_size}.png'))
    print(f'  Grid {glyph_size}x{glyph_size}: {cc}x{rc} = {cc*rc} per page')

    page_data_raw = raw_pixels[:128*128]
    img_raw = make_image(page_data_raw, 128, 128, invert=True).convert('RGB').resize((512, 512), Image.NEAREST)
    draw2 = ImageDraw.Draw(img_raw)
    for c in range(cc + 1):
        draw2.line([(c * glyph_size * scale, 0), (c * glyph_size * scale, 512)], fill=(255, 0, 0), width=1)
    for r in range(rc + 1):
        draw2.line([(0, r * glyph_size * scale), (512, r * glyph_size * scale)], fill=(255, 0, 0), width=1)
    img_raw.save(os.path.join(OUTDIR, f'raw_page0_grid{glyph_size}x{glyph_size}.png'))

print('\n=== Full deswizzled atlas with grid overlay ===')
full_img = make_image(desw, W, H, invert=True)
for glyph_size in [10, 12, 14, 16]:
    img_rgb = full_img.copy().convert('RGB').resize((W*2, H*2), Image.NEAREST)
    draw = ImageDraw.Draw(img_rgb)
    cc = W // glyph_size
    rc = H // glyph_size
    for c in range(cc + 1):
        draw.line([(c * glyph_size * 2, 0), (c * glyph_size * 2, H*2)], fill=(255, 0, 0), width=1)
    for r in range(rc + 1):
        draw.line([(0, r * glyph_size * 2), (W*2, r * glyph_size * 2)], fill=(255, 0, 0), width=1)
    img_rgb.save(os.path.join(OUTDIR, f'full_atlas_grid{glyph_size}x{glyph_size}.png'))
    print(f'  Full atlas grid {glyph_size}x{glyph_size}: {cc}x{rc} = {cc*rc} cells')

print('\n=== EXE per-glyph property structs ===')
exe = open(EXE_FILE, 'rb').read()
BASE = 0x3C0E78
f240 = struct.pack('<ff', 240.0, 240.0)
n = 0
while exe[BASE+n*28:BASE+n*28+8] == f240 and n < 2000:
    n += 1
print(f'240.0-group entries: {n}')

glyph_props = []
for i in range(n):
    o = BASE + i * 28
    metric = exe[o+9]
    atlas_row = exe[o+17]
    atlas_col = exe[o+18]
    glyph_props.append((i, metric, atlas_row, atlas_col))
    if i < 20 or (i % 20 == 0):
        print(f'  Glyph {i:3d}: metric={metric:3d} row={atlas_row} col={atlas_col}')

max_row = max(g[2] for g in glyph_props)
max_col = max(g[3] for g in glyph_props)
print(f'\nAtlas coord ranges: row 0-{max_row}, col 0-{max_col}')

from collections import Counter
row_counts = Counter(g[2] for g in glyph_props)
col_counts = Counter(g[3] for g in glyph_props)
print(f'Row distribution: {dict(sorted(row_counts.items()))}')
print(f'Col distribution: {dict(sorted(col_counts.items()))}')

print('\n=== ASCII glyph table cross-reference ===')
T = 0x3C0870
ascii_map = []
for j in range(84):
    o = T + j * 2
    v = struct.unpack_from('<H', exe, o)[0]
    ascii_char = chr(0x20 + j) if 0x20 + j < 127 else '?'
    ascii_map.append((0x20 + j, ascii_char, v))
print('ASCII -> glyph index -> atlas position:')
for ac, ch, glyph_idx in ascii_map:
    if glyph_idx < len(glyph_props):
        _, metric, row, col = glyph_props[glyph_idx]
        print(f'  0x{ac:02X} chr={ch} -> glyph {glyph_idx:3d} -> metric={metric:3d} row={row} col={col}')
    else:
        print(f'  0x{ac:02X} chr={ch} -> glyph {glyph_idx:3d} -> OUT OF RANGE')

print('\n=== Linearity and page analysis ===')
print('First 30 glyphs:')
for i in range(min(30, len(glyph_props))):
    _, metric, row, col = glyph_props[i]
    print(f'  glyph[{i:3d}] metric={metric:3d} row={row} col={col}')

page_glyph_counts = Counter((g[2], g[3]) for g in glyph_props)
print(f'\nGlyphs per atlas page (row,col):')
for k in sorted(page_glyph_counts.keys()):
    print(f'  row={k[0]} col={k[1]}: {page_glyph_counts[k]} glyphs')

print('\nMetric range per page:')
for page_key in sorted(page_glyph_counts.keys()):
    metrics_in_page = sorted([g[1] for g in glyph_props if (g[2], g[3]) == page_key])
    mstr = str(metrics_in_page[:25])
    print(f'  row={page_key[0]} col={page_key[1]}: min={min(metrics_in_page)} max={max(metrics_in_page)} count={len(metrics_in_page)} vals={mstr}')

print('\nDone!')
