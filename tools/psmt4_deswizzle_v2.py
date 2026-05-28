"""
PS2 PSMT4 Font Atlas Deswizzler v2
Correct implementation for BUSIN 0 (Wizardry) font atlas.

The PS2 GS stores PSMT4 textures in pages of 128x128 pixels (8192 bytes each).
Within each page, data is linear at 128 pixels per row (64 bytes per row).
Pages are arranged in a row-major grid to form the full texture.

For a 256x512 PSMT4 texture:
  - 2 pages per row x 4 rows = 8 pages
  - Page layout: row-major (page 0=top-left, page 1=top-right, ...)
"""
import os, sys
from PIL import Image

INPUT = "C:/Programmieren/wizardrytranslation/extracted/packdata_resources/1272_type01.bin"
OUTDIR = "C:/Programmieren/wizardrytranslation/dumps/font_renders"

def deswizzle_psmt4_linear(raw_data, tex_w, tex_h):
    """Deswizzle PSMT4 texture by rendering each page linearly at 128px width."""
    PAGE_W = 128
    PAGE_H = 128
    PAGE_BYTES = PAGE_W * PAGE_H // 2
    pages_x = tex_w // PAGE_W
    pages_y = tex_h // PAGE_H
    out = bytearray(tex_w * tex_h)
    for py in range(pages_y):
        for px in range(pages_x):
            page_idx = py * pages_x + px
            page_off = page_idx * PAGE_BYTES
            for ly in range(PAGE_H):
                for lx in range(PAGE_W):
                    pidx = ly * PAGE_W + lx
                    bi = page_off + pidx // 2
                    np = pidx & 1
                    if bi < len(raw_data):
                        bv = raw_data[bi]
                        pv = (bv & 0x0F) if np == 0 else ((bv >> 4) & 0x0F)
                    else:
                        pv = 0
                    ox = px * PAGE_W + lx
                    oy = py * PAGE_H + ly
                    if ox < tex_w and oy < tex_h:
                        out[oy * tex_w + ox] = pv
    return out


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    with open(INPUT, "rb") as f:
        raw = f.read()
    print("Input: %d bytes" % len(raw))
    HEADER_SIZE = 256
    td = raw[HEADER_SIZE:]
    W, H = 256, 512
    print("Deswizzling %dx%d PSMT4..." % (W, H))
    pixels = deswizzle_psmt4_linear(td, W, H)
    img = Image.new("L", (W, H))
    for y in range(H):
        for x in range(W):
            img.putpixel((x, y), 255 - pixels[y * W + x] * 17)
    out1 = os.path.join(OUTDIR, "font_atlas_deswizzled_correct.png")
    img.save(out1)
    print("Saved: " + out1)
    out2 = os.path.join(OUTDIR, "font_atlas_deswizzled_correct_2x.png")
    img.resize((W * 2, H * 2), Image.NEAREST).save(out2)
    print("Saved: " + out2)
    nz = sum(1 for p in pixels if p != 15)
    print("Glyph pixels: %d / %d (%.1f%%)" % (nz, len(pixels), 100.0 * nz / len(pixels)))
    print("Done")


if __name__ == "__main__":
    main()
