#!/usr/bin/env python3
"""analyze_font_entry.py - Font atlas analysis for Busin 0.
Key finding: Resource 1272 (type01, PSMT4 256x512) is the main font texture.
"""
import struct, os, json
from PIL import Image

BASE = "C:/Programmieren/wizardrytranslation"
RES = os.path.join(BASE, "extracted", "packdata_resources")
OUT = os.path.join(BASE, "dumps", "font_renders")
EXE = os.path.join(BASE, "extracted", "SLPM_653.78")
os.makedirs(OUT, exist_ok=True)

def render_psmt4_raw(pix_data, width, filename):
    h = len(pix_data) * 2 // width
    img = Image.new("L", (width, h), 0)
    px = img.load()
    for y in range(h):
        for x in range(0, width, 2):
            bi = y * (width // 2) + x // 2
            if bi >= len(pix_data): break
            b = pix_data[bi]
            px[x, y] = (b & 0xF) * 17
            if x+1 < width: px[x+1, y] = ((b >> 4) & 0xF) * 17
    img.save(os.path.join(OUT, filename + ".png"))

def render_psmt4_paged(pix_data, W, H, filename):
    page_w, page_h = 128, 128
    pages_x, pages_y = W // page_w, H // page_h
    page_bytes = page_w * page_h // 2
    img = Image.new("L", (W, H), 0)
    px = img.load()
    for py in range(pages_y):
        for ppx in range(pages_x):
            pn = py * pages_x + ppx
            ps = pn * page_bytes
            pd = pix_data[ps:ps + page_bytes]
            for y in range(page_h):
                for x in range(0, page_w, 2):
                    bi = y * (page_w // 2) + x // 2
                    if bi >= len(pd): break
                    b = pd[bi]
                    dx, dy = ppx * page_w + x, py * page_h + y
                    if dx < W and dy < H: px[dx, dy] = (b & 0xF) * 17
                    if dx+1 < W and dy < H: px[dx+1, dy] = ((b >> 4) & 0xF) * 17
    img.save(os.path.join(OUT, filename + ".png"))

def main():
    print("Font Atlas Analysis - Busin 0: Wizardry Alternative Neo")
    fn = "1272_type01.bin"
    with open(os.path.join(RES, fn), "rb") as f:
        raw = f.read()
    print(f"Font resource: {fn} ({len(raw)} bytes)")
    tex0 = struct.unpack_from("<Q", raw, 0x50)[0]
    psm = (tex0 >> 20) & 0x3F
    W = 1 << ((tex0 >> 26) & 0xF)
    H = 1 << ((tex0 >> 30) & 0xF)
    print(f"  PSMT4 (PSM={psm}), {W}x{H}, 192+64+{W*H//2}={192+64+W*H//2}")
    pix_data = raw[0xC0 + 64:]
    render_psmt4_raw(pix_data, 128, "font_atlas_raw_128w")
    render_psmt4_paged(pix_data, W, H, "font_atlas_paged_256x512")
    print(f"Renders saved to: {OUT}")

if __name__ == "__main__":
    main()
