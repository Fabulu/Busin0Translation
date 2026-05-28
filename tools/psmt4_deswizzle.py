import sys, io, struct, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from PIL import Image

FONT_FILE = "extracted/packdata_resources/1272_type01.bin"
OUTDIR = "dumps/font_renders/deswizzle"
os.makedirs(OUTDIR, exist_ok=True)

data = open(FONT_FILE, "rb").read()
header = data[:192]
palette = data[192:256]
pixels = data[256:]

W, H = 256, 512

# Unpack 4bpp to individual pixel values
raw_pixels = []
for b in pixels:
    raw_pixels.append(b & 0x0F)
    raw_pixels.append((b >> 4) & 0x0F)
print(f"Unpacked {len(raw_pixels)} pixels ({W}x{H}={W*H})")

# PSMT4 block table for 128-wide pages
# Block positions within a page (32x16 blocks in 128x128 page = 4cols x 8rows = 32 blocks)
BLOCK_TABLE = [
    (0,0),(1,0),(0,1),(1,1),(0,2),(1,2),(0,3),(1,3),
    (2,0),(3,0),(2,1),(3,1),(2,2),(3,2),(2,3),(3,3),
    (0,4),(1,4),(0,5),(1,5),(0,6),(1,6),(0,7),(1,7),
    (2,4),(3,4),(2,5),(3,5),(2,6),(3,6),(2,7),(3,7),
]

def deswizzle_psmt4(raw, w, h):
    out = [0] * (w * h)
    page_w = 128
    page_h = 128
    block_w = 32
    block_h = 16
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

# Also try with column XOR
def deswizzle_psmt4_xor(raw, w, h):
    out = [0] * (w * h)
    page_w = 128
    page_h = 128
    block_w = 32
    block_h = 16
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
                        # Apply column XOR based on row
                        col_adj = col ^ ((row & 2) << 3)
                        if col_adj >= block_w:
                            col_adj = col
                        src = block_base + row * block_w + col_adj
                        if src < len(raw):
                            dst_x = px_idx * page_w + bx * block_w + col
                            dst_y = py_idx * page_h + by * block_h + row
                            if dst_x < w and dst_y < h:
                                out[dst_y * w + dst_x] = raw[src]
    return out

def save_image(pixels, w, h, filename, invert=True):
    img = Image.new("L", (w, h))
    if invert:
        pix = [min(p * 17, 255) for p in pixels]
    else:
        pix = [255 - min(p * 17, 255) for p in pixels]
    img.putdata(pix[:w*h])
    path = os.path.join(OUTDIR, filename)
    img.save(path)
    print(f"  Saved: {filename}")

# Method 1: Raw linear
save_image(raw_pixels, W, H, "method1_raw_linear.png")
save_image(raw_pixels, W, H, "method1_raw_linear_inv.png", invert=False)

# Method 2: Raw at 128 width
save_image(raw_pixels, 128, H*2, "method2_raw_128w.png")

# Method 3: Block deswizzle
desw = deswizzle_psmt4(raw_pixels, W, H)
save_image(desw, W, H, "method3_block_deswizzle.png")
save_image(desw, W, H, "method3_block_deswizzle_inv.png", invert=False)

# Method 4: Block + XOR column deswizzle
desw_xor = deswizzle_psmt4_xor(raw_pixels, W, H)
save_image(desw_xor, W, H, "method4_block_xor.png")
save_image(desw_xor, W, H, "method4_block_xor_inv.png", invert=False)

# Method 5: Nibble-swapped then deswizzle
swapped = []
for b in pixels:
    swapped.append((b >> 4) & 0x0F)
    swapped.append(b & 0x0F)
desw_swap = deswizzle_psmt4(swapped, W, H)
save_image(desw_swap, W, H, "method5_nibswap_block.png")
save_image(desw_swap, W, H, "method5_nibswap_block_inv.png", invert=False)

desw_swap_xor = deswizzle_psmt4_xor(swapped, W, H)
save_image(desw_swap_xor, W, H, "method6_nibswap_xor.png")
save_image(desw_swap_xor, W, H, "method6_nibswap_xor_inv.png", invert=False)

print("Done! Check dumps/font_renders/deswizzle/")
