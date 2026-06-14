#!/usr/bin/env python3
"""patch_r2882_grave.py — R2882 sub7: pre-rendered GRAVE-cutscene narration page.

A 256x256 PSMT4 page (pixel payload at FILE offset 644368, 32768 bytes, inverted
ramp bg=15/ink=0) holding a 7-line CENTERED poetic narration.  Unlike R2880/R2881
this page has NO split UV windows — every line is a single centered run — so we
just center each English line on the 256px page.  Text/layout in
data/strip_labels/r2882_grave.json.

Same SINGLE-WINDOW write discipline as patch_r2880.py: only the pixel payload
[644368, 644368+32768) is touched; the rest of the resource (tombstone/butterfly
PSMT8 stills + VIF) is asserted pristine.  Real-PS2 safe (PACKDATA pixels only).
"""
import json
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "tools"))
from psmt4_deswizzle import deswizzle_psmt4, swizzle_psmt4  # noqa: E402
from strip_patcher import assert_outside_window_pristine, load_font  # noqa: E402

from PIL import Image, ImageDraw  # noqa: E402

OUT_DIR = os.path.join(BASE, "build", "recon_v86", "r2882-out")
LABELS = os.path.join(BASE, "data", "strip_labels", "r2882_grave.json")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    cfg = json.load(open(LABELS, encoding="utf-8"))
    tex = cfg["texture"]
    lay = cfg["layout"]
    lines = cfg["lines"]
    SRC = os.path.join(BASE, *tex["file"].split("/"))
    OUT = os.path.join(BASE, "build", "packdata_resources",
                       os.path.basename(SRC))
    POFF, PSZ = tex["pixel_off"], tex["pixel_size"]
    TEX_W, TEX_H = tex["tex_w"], tex["tex_h"]
    BW, DBW = tex["bw_psmt4"], tex["dbw_ct32"]
    BG, INK = tex["bg_index"], tex["ink_index"]
    line_tops = lay["line_tops"]
    band_h = lay["band_height"]
    size = lay["font_size"]
    max_w = lay["max_line_width"]
    assert len(lines) == len(line_tops), \
        f"{len(lines)} lines vs {len(line_tops)} line tops"

    def quantize(gray):
        return [BG - (v * (BG - INK) + 127) // 255 for v in gray.getdata()]

    pristine = open(SRC, "rb").read()
    print(f"source: {SRC} ({len(pristine)} bytes)")
    blob = pristine[POFF:POFF + PSZ]
    assert len(blob) == PSZ
    linear = bytearray(deswizzle_psmt4(blob, TEX_W, TEX_H, bw_psmt4=BW,
                                       dbw_ct32=DBW))
    assert bytes(swizzle_psmt4(linear, TEX_W, TEX_H, bw_psmt4=BW,
                               dbw_ct32=DBW)) == blob, "pre-edit roundtrip FAILED"
    print("roundtrip (pre-edit): PASS")

    # clear the text region to bg
    cx, cy, cw, ch = lay["clear_region"]
    for y in range(cy, cy + ch):
        for x in range(cx, cx + cw):
            linear[y * TEX_W + x] = BG

    # typeset each line CENTERED on the page
    font = load_font(size, bold=True)
    for i, (top, ln) in enumerate(zip(line_tops, lines)):
        text = ln["en"]
        bbox = font.getbbox(text)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        assert tw <= max_w, (
            f"line {i} width {tw}px > {max_w}px: '{text}' — reword in "
            f"data/strip_labels/r2882_grave.json")
        cell = Image.new("L", (TEX_W, band_h), 0)
        draw = ImageDraw.Draw(cell)
        ox = (TEX_W - tw) // 2 - bbox[0]
        draw.text((ox, (band_h - th) // 2 - bbox[1]), text, fill=255, font=font)
        idx = quantize(cell)
        for dy in range(band_h):
            row = (top + dy) * TEX_W
            for dx in range(TEX_W):
                v = idx[dy * TEX_W + dx]
                if v != BG:
                    linear[row + dx] = v
        print(f"  i={i} y={top:3} w={tw:3}px  '{text}'")

    img = Image.new("L", (TEX_W, TEX_H))
    img.putdata([min(255, p * 17) for p in linear])
    img.save(os.path.join(OUT_DIR, "r2882s7_after.png"))

    new_blob = bytes(swizzle_psmt4(linear, TEX_W, TEX_H, bw_psmt4=BW,
                                   dbw_ct32=DBW))
    assert len(new_blob) == PSZ
    assert bytes(deswizzle_psmt4(new_blob, TEX_W, TEX_H, bw_psmt4=BW,
                                 dbw_ct32=DBW)) == bytes(linear), \
        "post-edit roundtrip FAILED"
    patched = bytearray(pristine)
    patched[POFF:POFF + PSZ] = new_blob
    assert len(patched) == len(pristine), "total file size changed"
    assert_outside_window_pristine(pristine, bytes(patched),
                                   [(POFF, POFF + PSZ)])
    n = sum(1 for a, b in zip(blob, new_blob) if a != b)
    print(f"asserts: size unchanged; outside [{POFF},{POFF + PSZ}) pristine; "
          f"{n} bytes changed inside window")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "wb").write(patched)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # noqa: BLE001
        print(f"FAILED: {e}", file=sys.stderr)
        sys.exit(1)
