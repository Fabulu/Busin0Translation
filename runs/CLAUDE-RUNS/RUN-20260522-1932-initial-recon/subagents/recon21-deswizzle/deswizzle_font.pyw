"""
PS2 PSMT4 Font Atlas Deswizzle - Multiple Approaches
BUSIN 0: Wizardry Alternative Neo font atlas analysis
Run with: python deswizzle_font.pyw
"""
import struct, os, sys
try:
    from PIL import Image
except ImportError:
    os.system("pip install Pillow")
    from PIL import Image

INPUT_FILE = "C:/Programmieren/wizardrytranslation/extracted/packdata_resources/1272_type01.bin"
OUTPUT_DIR = "C:/Programmieren/wizardrytranslation/dumps/font_renders/deswizzle"
FINDINGS_DIR = "C:/Programmieren/wizardrytranslation/runs/CLAUDE-RUNS/RUN-20260522-1932-initial-recon/subagents/recon21-deswizzle"
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(FINDINGS_DIR, exist_ok=True)

with open(INPUT_FILE, "rb") as f:
    data = f.read()
print(f"File size: {len(data)} bytes")

HEADER_SIZE = 192
PALETTE_SIZE = 64
PIXEL_OFFSET = HEADER_SIZE + PALETTE_SIZE
header = data[:HEADER_SIZE]
palette_data = data[HEADER_SIZE:HEADER_SIZE + PALETTE_SIZE]
pixel_data = data[PIXEL_OFFSET:]
print(f"Header first 32 bytes: {header[:32].hex()}")
print(f"Palette data: {palette_data.hex()}")
print(f"Pixel data size: {len(pixel_data)} bytes")

# Parse 16 ABGR1555 palette entries
palette_rgb = []
for i in range(16):
    val = struct.unpack_from("<H", palette_data, i * 2)[0]
    r = (val & 0x1F) << 3
    g = ((val >> 5) & 0x1F) << 3
    b = ((val >> 10) & 0x1F) << 3
    palette_rgb.append((r, g, b, 255 if i > 0 else 0))
    print(f"  Pal[{i:2d}]: 0x{val:04X} R={r:3d} G={g:3d} B={b:3d}")

gray_pal = [(i * 17, i * 17, i * 17, 255 if i > 0 else 0) for i in range(16)]
results = {}


def save_img(pixels, w, h, name, pal=None):
    if pal is None:
        pal = gray_pal
    img = Image.new("RGBA", (w, h))
    for y in range(h):
        for x in range(w):
            idx = pixels[y * w + x] if y * w + x < len(pixels) else 0
            img.putpixel((x, y), pal[idx % len(pal)])
    path = os.path.join(OUTPUT_DIR, f"{name}.png")
    img.save(path)
    print(f"  Saved: {name}.png")
    results[name] = path


def extract_4bpp(raw, ns=False):
    px = []
    for b in raw:
        if ns:
            px.append((b >> 4) & 0xF)
            px.append(b & 0xF)
        else:
            px.append(b & 0xF)
            px.append((b >> 4) & 0xF)
    return px


# PSMT4 block table
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


def psmt4_deswizzle(raw, tw, th, ns=False):
    pixels = [0] * (tw * th)
    pw, ph, bw, bh = 128, 128, 32, 16
    pxc = (tw + pw - 1) // pw
    pyc = (th + ph - 1) // ph
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
                    for py in range(bh):
                        for px in range(bw):
                            pidx = py * bw + px
                            bi = bo + pidx // 2
                            if bi >= len(raw):
                                continue
                            bv = raw[bi]
                            if ns:
                                ci = ((bv >> 4) & 0xF) if pidx % 2 == 0 else (bv & 0xF)
                            else:
                                ci = (bv & 0xF) if pidx % 2 == 0 else ((bv >> 4) & 0xF)
                            dx = bx + px
                            dy = by + py
                            if dx < tw and dy < th:
                                pixels[dy * tw + dx] = ci
    return pixels


# ============================================================
# APPROACH A: Raw linear (no deswizzle)
# ============================================================
print("\n=== A: Raw linear ===")
for w in [128, 256, 512]:
    for ns in [False, True]:
        px = extract_4bpp(pixel_data, ns)
        h = len(px) // w
        suf = "_ns" if ns else ""
        save_img(px, w, h, f"A_raw{suf}_w{w}_h{h}")

# ============================================================
# APPROACH D: Treat as 8bpp
# ============================================================
print("\n=== D: 8bpp ===")
for w in [128, 256]:
    px = [b % 16 for b in pixel_data]
    h = len(px) // w
    save_img(px, w, h, f"D_8bpp_w{w}_h{h}")

# ============================================================
# APPROACH E: Standard PSMT4 deswizzle
# ============================================================
print("\n=== E: PSMT4 deswizzle ===")
for w, h in [(256, 512), (128, 1024)]:
    if w * h // 2 <= len(pixel_data):
        for ns in [False, True]:
            px = psmt4_deswizzle(pixel_data, w, h, ns)
            suf = "_ns" if ns else ""
            save_img(px, w, h, f"E_psmt4{suf}_w{w}_h{h}")

# ============================================================
# APPROACH F: XOR block reorder
# ============================================================
print("\n=== F: XOR block reorder ===")


def xor_deswizzle(raw, tw, th):
    src = extract_4bpp(raw)
    dst = [0] * (tw * th)
    pw, ph, bw, bh = 128, 128, 32, 16
    pxc = (tw + pw - 1) // pw
    for y in range(th):
        for x in range(tw):
            pgx = x // pw
            pgy = y // ph
            pi = pgy * pxc + pgx
            bx2 = (x % pw) // bw
            by2 = (y % ph) // bh
            bn = PSMT4_BT[by2][bx2] if by2 < 8 and bx2 < 4 else 0
            px2 = x % bw
            py2 = y % bh
            si = pi * (pw * ph) + bn * (bw * bh) + py2 * bw + px2
            if si < len(src):
                dst[y * tw + x] = src[si]
    return dst


px = xor_deswizzle(pixel_data, 256, 512)
save_img(px, 256, 512, "F_xor_w256_h512")

# ============================================================
# APPROACH J: Tile layouts
# ============================================================
print("\n=== J: Tile layouts ===")


def tile_deswizzle(raw, tw, th, tilew, tileh, ns=False):
    src = extract_4bpp(raw, ns)
    dst = [0] * (tw * th)
    txc = tw // tilew
    tyc = th // tileh
    tsz = tilew * tileh
    for ty in range(tyc):
        for tx in range(txc):
            ti = ty * txc + tx
            to2 = ti * tsz
            for py in range(tileh):
                for px in range(tilew):
                    si = to2 + py * tilew + px
                    dx = tx * tilew + px
                    dy = ty * tileh + py
                    if si < len(src) and dy < th and dx < tw:
                        dst[dy * tw + dx] = src[si]
    return dst


for ts in [(8, 8), (16, 16), (32, 32)]:
    for ns in [False, True]:
        px = tile_deswizzle(pixel_data, 256, 512, ts[0], ts[1], ns)
        suf = "_ns" if ns else ""
        save_img(px, 256, 512, f"J_tile{ts[0]}x{ts[1]}{suf}_w256_h512")

# ============================================================
# APPROACH K: Morton Z-order
# ============================================================
print("\n=== K: Morton Z-order ===")


def morton_desw(raw, tw, th, tb):
    src = extract_4bpp(raw)
    dst = [0] * (tw * th)
    tsz = 1 << tb
    tpx = tw // tsz
    tpy = th // tsz
    tps = tsz * tsz
    for ty in range(tpy):
        for tx in range(tpx):
            ti = ty * tpx + tx
            to2 = ti * tps
            for i in range(tps):
                px2 = 0
                py2 = 0
                for bit in range(tb):
                    px2 |= ((i >> (2 * bit)) & 1) << bit
                    py2 |= ((i >> (2 * bit + 1)) & 1) << bit
                si = to2 + i
                dx = tx * tsz + px2
                dy = ty * tsz + py2
                if si < len(src) and dx < tw and dy < th:
                    dst[dy * tw + dx] = src[si]
    return dst


for tb in [3, 4, 5]:
    px = morton_desw(pixel_data, 256, 512, tb)
    save_img(px, 256, 512, f"K_morton{1 << tb}_w256_h512")

# ============================================================
# APPROACH H: With actual palette
# ============================================================
print("\n=== H: With actual palette ===")
for ns in [False, True]:
    px = extract_4bpp(pixel_data, ns)
    suf = "_ns" if ns else ""
    save_img(px, 256, 512, f"H_palette{suf}_w256_h512", palette_rgb)
    px2 = psmt4_deswizzle(pixel_data, 256, 512, ns)
    save_img(px2, 256, 512, f"H_psmt4_pal{suf}_w256_h512", palette_rgb)

# ============================================================
# APPROACH L: CSM1 palette index swizzle
# ============================================================
print("\n=== L: CSM1 palette swap ===")


def csm1_pal_swap(idx):
    if (idx & 0x18) == 0x08:
        return (idx & ~0x18) | 0x10
    if (idx & 0x18) == 0x10:
        return (idx & ~0x18) | 0x08
    return idx


csm1_gray = [
    (csm1_pal_swap(i) * 17, csm1_pal_swap(i) * 17, csm1_pal_swap(i) * 17, 255 if i > 0 else 0)
    for i in range(16)
]
for ns in [False, True]:
    px = extract_4bpp(pixel_data, ns)
    suf = "_ns" if ns else ""
    save_img(px, 256, 512, f"L_csm1pal{suf}_w256_h512", csm1_gray)

# ============================================================
# APPROACH G: PSMT4 with column deswizzle
# ============================================================
print("\n=== G: PSMT4 with column deswizzle ===")

COL_TABLE_EVEN = [0, 1, 4, 5, 8, 9, 12, 13]
COL_TABLE_ODD = [2, 3, 6, 7, 10, 11, 14, 15]


def psmt4_full_deswizzle(raw, tw, th, ns=False):
    pixels = [0] * (tw * th)
    pw, ph, bw, bh = 128, 128, 32, 16
    col_w, col_h = 32, 2
    pxc = (tw + pw - 1) // pw
    pyc = (th + ph - 1) // ph
    col_size = (col_w * col_h) // 2  # 32 bytes
    bs = (bw * bh) // 2  # 256 bytes
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
                        for py in range(col_h):
                            for px in range(col_w):
                                pidx = py * col_w + px
                                bi = col_off + pidx // 2
                                if bi >= len(raw):
                                    continue
                                bv = raw[bi]
                                if ns:
                                    ci = ((bv >> 4) & 0xF) if pidx % 2 == 0 else (bv & 0xF)
                                else:
                                    ci = (bv & 0xF) if pidx % 2 == 0 else ((bv >> 4) & 0xF)
                                dx = bx + px
                                dy = by + col_y + py
                                if dx < tw and dy < th:
                                    pixels[dy * tw + dx] = ci
    return pixels


for ns in [False, True]:
    px = psmt4_full_deswizzle(pixel_data, 256, 512, ns)
    suf = "_ns" if ns else ""
    save_img(px, 256, 512, f"G_psmt4_coldesw{suf}_w256_h512")

# ============================================================
# Summary
# ============================================================
print(f"\nTotal renders: {len(results)}")
for name in sorted(results.keys()):
    print(f"  {name}")
print("DONE")
