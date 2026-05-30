"""
Brute-force pixel format detection for R1188 (528,384 bytes).
Tries many BPP / width / header-offset / swizzle combinations.
"""
import struct, os, sys
from pathlib import Path
import numpy as np
from PIL import Image

SRC = r"C:\Programmieren\wizardrytranslation\extracted\packdata_raw\1188_type01.raw"
OUT = r"C:\Programmieren\wizardrytranslation\build\r1188_bruteforce"
os.makedirs(OUT, exist_ok=True)

raw = open(SRC, "rb").read()
total = len(raw)
print(f"File size: {total}")

# ---- helpers --------------------------------------------------------

def grayscale_4bpp_linear(data, w, h):
    """Each byte = 2 pixels (lo nibble first, PS2 convention)."""
    needed = (w * h) // 2
    d = data[:needed]
    arr = np.frombuffer(d, dtype=np.uint8)
    lo = (arr & 0x0F) * 17        # scale 0-15 -> 0-255
    hi = ((arr >> 4) & 0x0F) * 17
    pixels = np.empty(len(arr) * 2, dtype=np.uint8)
    pixels[0::2] = lo
    pixels[1::2] = hi
    return pixels[:w*h].reshape((h, w))

def grayscale_4bpp_linear_hiFirst(data, w, h):
    """Hi nibble first variant."""
    needed = (w * h) // 2
    d = data[:needed]
    arr = np.frombuffer(d, dtype=np.uint8)
    hi = ((arr >> 4) & 0x0F) * 17
    lo = (arr & 0x0F) * 17
    pixels = np.empty(len(arr) * 2, dtype=np.uint8)
    pixels[0::2] = hi
    pixels[1::2] = lo
    return pixels[:w*h].reshape((h, w))

def grayscale_8bpp(data, w, h):
    needed = w * h
    d = data[:needed]
    return np.frombuffer(d, dtype=np.uint8).reshape((h, w))

def rgb555(data, w, h):
    needed = w * h * 2
    d = data[:needed]
    arr = np.frombuffer(d, dtype=np.uint16).reshape((h, w))
    r = ((arr & 0x001F) << 3).astype(np.uint8)
    g = (((arr >> 5) & 0x1F) << 3).astype(np.uint8)
    b = (((arr >> 10) & 0x1F) << 3).astype(np.uint8)
    return np.stack([r, g, b], axis=-1)

def rgba5551(data, w, h):
    needed = w * h * 2
    d = data[:needed]
    arr = np.frombuffer(d, dtype=np.uint16).reshape((h, w))
    r = ((arr & 0x001F) << 3).astype(np.uint8)
    g = (((arr >> 5) & 0x1F) << 3).astype(np.uint8)
    b = (((arr >> 10) & 0x1F) << 3).astype(np.uint8)
    a = np.where(arr & 0x8000, 255, 0).astype(np.uint8)
    return np.stack([r, g, b, a], axis=-1)

def rgba32(data, w, h):
    needed = w * h * 4
    d = data[:needed]
    return np.frombuffer(d, dtype=np.uint8).reshape((h, w, 4))

def psmt4_unswizzle(data, w, h):
    """PSMT4 block-based layout: 128x128 pages, 32x16 blocks inside."""
    needed = (w * h) // 2
    d = data[:needed]
    src = np.frombuffer(d, dtype=np.uint8)
    out = np.zeros((h, w), dtype=np.uint8)

    page_w, page_h = 128, 128
    block_w, block_h = 32, 16

    idx = 0
    for py in range(0, h, page_h):
        for px in range(0, w, page_w):
            for by in range(0, page_h, block_h):
                for bx in range(0, page_w, block_w):
                    for y in range(block_h):
                        for x in range(0, block_w, 2):
                            if idx >= len(src):
                                break
                            byte = src[idx]; idx += 1
                            ox = px + bx + x
                            oy = py + by + y
                            if oy < h and ox < w:
                                out[oy, ox] = (byte & 0x0F) * 17
                            if oy < h and ox + 1 < w:
                                out[oy, ox + 1] = ((byte >> 4) & 0x0F) * 17
    return out

def row_interleave_8bpp(data, w, h):
    """Simple 2-row interleave pattern common on PS2."""
    needed = w * h
    d = data[:needed]
    arr = np.frombuffer(d, dtype=np.uint8).reshape((h, w))
    out = np.zeros_like(arr)
    for y in range(h):
        # Even rows go to top half, odd rows to bottom half
        if y % 2 == 0:
            out[y // 2, :] = arr[y, :]
        else:
            out[h // 2 + y // 2, :] = arr[y, :]
    return out

def ps2_8bpp_32x4_block(data, w, h):
    """PS2 PSMT8 uses column-based 16x4 blocks within 64x32 pages."""
    needed = w * h
    d = data[:needed]
    src = np.frombuffer(d, dtype=np.uint8)
    out = np.zeros((h, w), dtype=np.uint8)

    idx = 0
    col_w, col_h = 16, 4
    page_w, page_h = 128, 64

    for py in range(0, h, page_h):
        for px in range(0, w, page_w):
            for cy in range(0, page_h, col_h):
                for cx in range(0, page_w, col_w):
                    for y in range(col_h):
                        for x in range(col_w):
                            if idx >= len(src):
                                break
                            ox = px + cx + x
                            oy = py + cy + y
                            if oy < h and ox < w:
                                out[oy, ox] = src[idx]
                            idx += 1
    return out

def save_img(pixels, path, mode='L'):
    """Save with clamped dimensions for sanity."""
    try:
        if isinstance(pixels, np.ndarray):
            if pixels.ndim == 2:
                img = Image.fromarray(pixels, mode='L')
            elif pixels.shape[2] == 3:
                img = Image.fromarray(pixels, mode='RGB')
            elif pixels.shape[2] == 4:
                img = Image.fromarray(pixels, mode='RGBA')
            else:
                return False
            # Limit output size for viewability
            max_dim = 4096
            if img.width > max_dim or img.height > max_dim:
                ratio = min(max_dim / img.width, max_dim / img.height)
                img = img.resize((int(img.width * ratio), int(img.height * ratio)), Image.NEAREST)
            img.save(path)
            return True
    except Exception as e:
        print(f"  ERROR saving {path}: {e}")
        return False

# ---- main brute force -----------------------------------------------

header_offsets = [0, 192, 208, 256, 512, 1024, 2048, 3072, 4096]
count = 0

for hdr in header_offsets:
    data = raw[hdr:]
    dlen = len(data)
    tag = f"hdr{hdr}"

    # 4bpp linear (lo-first)
    for w in [128, 256, 512, 1024, 2048]:
        h = (dlen * 2) // w
        if h < 1 or h > 65536:
            continue
        h = min(h, 16384)  # cap
        name = f"r1188_4bpp_w{w}_{tag}.png"
        print(f"[{count+1}] 4bpp linear lo-first w={w} hdr={hdr} -> {w}x{h}")
        pixels = grayscale_4bpp_linear(data, w, h)
        save_img(pixels, os.path.join(OUT, name))
        count += 1

    # 4bpp linear (hi-first) - only a few key widths
    if hdr in [0, 4096, 3072]:
        for w in [256, 512, 1024]:
            h = (dlen * 2) // w
            h = min(h, 8192)
            name = f"r1188_4bppHi_w{w}_{tag}.png"
            print(f"[{count+1}] 4bpp linear hi-first w={w} hdr={hdr} -> {w}x{h}")
            pixels = grayscale_4bpp_linear_hiFirst(data, w, h)
            save_img(pixels, os.path.join(OUT, name))
            count += 1

    # 8bpp linear
    for w in [128, 256, 512, 1024]:
        h = dlen // w
        if h < 1:
            continue
        h = min(h, 8192)
        name = f"r1188_8bpp_w{w}_{tag}.png"
        print(f"[{count+1}] 8bpp linear w={w} hdr={hdr} -> {w}x{h}")
        pixels = grayscale_8bpp(data, w, h)
        save_img(pixels, os.path.join(OUT, name))
        count += 1

    # 16bpp RGB555 - key sizes only
    if hdr in [0, 4096, 3072, 2048]:
        for w in [128, 256, 512]:
            h = dlen // (w * 2)
            if h < 1:
                continue
            h = min(h, 4096)
            name = f"r1188_16bpp555_w{w}_{tag}.png"
            print(f"[{count+1}] 16bpp RGB555 w={w} hdr={hdr} -> {w}x{h}")
            pixels = rgb555(data, w, h)
            save_img(pixels, os.path.join(OUT, name))
            count += 1

    # 16bpp RGBA5551 - key sizes
    if hdr in [0, 4096, 3072]:
        for w in [256, 512]:
            h = dlen // (w * 2)
            if h < 1:
                continue
            h = min(h, 4096)
            name = f"r1188_16bpp5551_w{w}_{tag}.png"
            print(f"[{count+1}] 16bpp RGBA5551 w={w} hdr={hdr} -> {w}x{h}")
            pixels = rgba5551(data, w, h)
            save_img(pixels, os.path.join(OUT, name))
            count += 1

    # 32bpp RGBA - key sizes
    if hdr in [0, 4096, 3072, 2048]:
        for w in [128, 256, 512]:
            h = dlen // (w * 4)
            if h < 1:
                continue
            h = min(h, 2048)
            name = f"r1188_32bpp_w{w}_{tag}.png"
            print(f"[{count+1}] 32bpp RGBA w={w} hdr={hdr} -> {w}x{h}")
            pixels = rgba32(data, w, h)
            save_img(pixels, os.path.join(OUT, name))
            count += 1

# PSMT4 swizzle attempts with key header offsets
for hdr in [0, 3072, 4096]:
    data = raw[hdr:]
    dlen = len(data)
    tag = f"hdr{hdr}"
    for w in [256, 512, 1024]:
        h = (dlen * 2) // w
        h = min(h, 4096)
        # round to page boundaries
        h = (h // 128) * 128
        w2 = (w // 128) * 128
        if w2 < 128 or h < 128:
            continue
        name = f"r1188_psmt4_w{w2}_{tag}.png"
        print(f"[{count+1}] PSMT4 swizzle w={w2} hdr={hdr} -> {w2}x{h}")
        pixels = psmt4_unswizzle(data, w2, h)
        save_img(pixels, os.path.join(OUT, name))
        count += 1

# 8bpp row-interleave
for hdr in [0, 4096]:
    data = raw[hdr:]
    dlen = len(data)
    tag = f"hdr{hdr}"
    for w in [256, 512]:
        h = dlen // w
        h = min(h, 4096)
        h = (h // 2) * 2  # must be even
        name = f"r1188_8bpp_interleave_w{w}_{tag}.png"
        print(f"[{count+1}] 8bpp row-interleave w={w} hdr={hdr} -> {w}x{h}")
        pixels = row_interleave_8bpp(data, w, h)
        save_img(pixels, os.path.join(OUT, name))
        count += 1

# 8bpp PS2 block swizzle
for hdr in [0, 4096]:
    data = raw[hdr:]
    dlen = len(data)
    tag = f"hdr{hdr}"
    for w in [256, 512]:
        h = dlen // w
        h = min(h, 4096)
        h = (h // 64) * 64
        w2 = (w // 128) * 128
        if w2 < 128 or h < 64:
            continue
        name = f"r1188_8bpp_block_w{w2}_{tag}.png"
        print(f"[{count+1}] 8bpp PS2 block w={w2} hdr={hdr} -> {w2}x{h}")
        pixels = ps2_8bpp_32x4_block(data, w2, h)
        save_img(pixels, os.path.join(OUT, name))
        count += 1

print(f"\nDone! Generated {count} images in {OUT}")
