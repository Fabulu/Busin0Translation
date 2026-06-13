#!/usr/bin/env python3
"""patch_r2881_ending.py — R2881 sub7: pre-rendered ENDING / EPILOGUE pages.

R2881 is the ending cutscene resource (sibling of opening R2880). sub7 holds
TWO 512x512 PSMT4 text pages (img0, img1), identical in format to the R2880
prologue page (inverted ramp bg=15 / ink=0, dbw_ct32=256, bw_psmt4=512):

  - extracted/packdata_raw/2881_type15.raw
  - img0 pixel payload at FILE offset 1978608, 131072 bytes
  - img1 pixel payload at FILE offset 2109744, 131072 bytes
        deswizzle_psmt4(data[off:off+131072], 512, 512,
                        bw_psmt4=512, dbw_ct32=256)

Each page is a free-form TWO-COLUMN poetic layout (left col x~0-250, right col
x~250-500, plus a few centered lines). The English is typeset per-line at the
column anchor matching the original block, NOT as a single left-aligned list.

Transcription + English live in data/strip_labels/r2881_ending.json.
Located/verified in build/recon_v86/ending/ (decode_ending_report.json +
r2881s7_img0/img1 2x crops, roundtrip PASS on both windows).

Safety: SINGLE-WINDOW write discipline. Only bytes inside the two pixel
windows are modified; the rest of the 2.3MB resource (opening-movie stills,
VIF/anim sections, credits art) is never touched.

Usage:
    python tools/patch_r2881_ending.py
Writes build/packdata_resources/2881_type15.raw and before/after PNGs under
build/recon_v86/r2881-out/. Exits nonzero on any failure.
"""
import json
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "tools"))
from psmt4_deswizzle import deswizzle_psmt4, swizzle_psmt4  # noqa: E402
from strip_patcher import (assert_outside_window_pristine,  # noqa: E402
                           load_font)

from PIL import Image, ImageDraw  # noqa: E402

SRC = os.path.join(BASE, "extracted", "packdata_raw", "2881_type15.raw")
OUT = os.path.join(BASE, "build", "packdata_resources", "2881_type15.raw")
OUT_DIR = os.path.join(BASE, "build", "recon_v86", "r2881-out")
LABELS = os.path.join(BASE, "data", "strip_labels", "r2881_ending.json")

TEX_W = TEX_H = 512
BW_PSMT4 = 512
DBW_CT32 = 256
PIXEL_SIZE = 131072
BG = 15
INK = 0
BAND_H = 23
FONT_SIZE = 18

# Column anchors (left edge of typeset text) and max widths, in pixels.
X_LEFT = 4
W_LEFT = 250
X_RIGHT = 258
W_RIGHT = 250
W_CENTER = 504  # centered lines span the page; centered around 256


def quantize(gray_img):
    return [BG - (v * (BG - INK) + 127) // 255 for v in gray_img.getdata()]


def save_gray(linear, path, crop=None, scale=1):
    img = Image.new("L", (TEX_W, TEX_H))
    img.putdata([min(255, p * 17) for p in linear])
    if crop:
        img = img.crop(crop)
    if scale != 1:
        img = img.resize((img.width * scale, img.height * scale),
                         Image.NEAREST)
    img.save(path)
    return path


def typeset_line(linear, top, text, left_x, max_w, center=False):
    """Render one line of English into the linear page at row `top`,
    anchored at left_x (or centered in [0,512) if center)."""
    if not text:
        return
    size = FONT_SIZE
    font = load_font(size, bold=True)
    while font.getbbox(text)[2] - font.getbbox(text)[0] > max_w and size > 11:
        size -= 1
        font = load_font(size, bold=True)
    bbox = font.getbbox(text)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    assert tw <= max_w, f"line too wide even at {size}px: '{text}'"
    if center:
        x0 = (TEX_W - tw) // 2 - bbox[0]
    else:
        x0 = left_x - bbox[0]
    cell = Image.new("L", (TEX_W, BAND_H), 0)
    draw = ImageDraw.Draw(cell)
    draw.text((x0, (BAND_H - th) // 2 - bbox[1]), text, fill=255, font=font)
    idx = quantize(cell)
    for dy in range(BAND_H):
        row = (top + dy) * TEX_W
        if top + dy >= TEX_H:
            break
        for dx in range(TEX_W):
            v = idx[dy * TEX_W + dx]
            if v != BG:
                linear[row + dx] = v


def patch_page(pristine, tex):
    off = tex["pixel_off"]
    blob = pristine[off:off + PIXEL_SIZE]
    assert len(blob) == PIXEL_SIZE
    linear = bytearray(deswizzle_psmt4(blob, TEX_W, TEX_H,
                                       bw_psmt4=BW_PSMT4, dbw_ct32=DBW_CT32))
    assert bytes(swizzle_psmt4(linear, TEX_W, TEX_H, bw_psmt4=BW_PSMT4,
                               dbw_ct32=DBW_CT32)) == blob, \
        f"{tex['id']} pre-edit swizzle roundtrip FAILED"

    tag = tex["id"]
    save_gray(linear, os.path.join(OUT_DIR, f"r2881s7_{tag}_before.png"))

    # clear the whole text field (pages are text-only on a uniform bg=15 field)
    for i in range(TEX_W * TEX_H):
        linear[i] = BG

    for ln in tex.get("left_column", []):
        typeset_line(linear, ln["y"], ln["en"], X_LEFT, W_LEFT)
    for ln in tex.get("right_column", []):
        typeset_line(linear, ln["y"], ln["en"], X_RIGHT, W_RIGHT)
    for ln in tex.get("center_lines", []):
        typeset_line(linear, ln["y"], ln["en"], 0, W_CENTER, center=True)

    save_gray(linear, os.path.join(OUT_DIR, f"r2881s7_{tag}_after.png"))

    new_blob = bytes(swizzle_psmt4(linear, TEX_W, TEX_H,
                                   bw_psmt4=BW_PSMT4, dbw_ct32=DBW_CT32))
    assert len(new_blob) == PIXEL_SIZE
    assert bytes(deswizzle_psmt4(new_blob, TEX_W, TEX_H, bw_psmt4=BW_PSMT4,
                                 dbw_ct32=DBW_CT32)) == bytes(linear), \
        f"{tag} post-edit swizzle roundtrip FAILED"
    return off, new_blob


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    cfg = json.load(open(LABELS, encoding="utf-8"))
    pristine = open(SRC, "rb").read()
    print(f"source: {SRC} ({len(pristine)} bytes)")

    patched = bytearray(pristine)
    windows = []
    for tex in cfg["textures"]:
        off, new_blob = patch_page(pristine, tex)
        patched[off:off + PIXEL_SIZE] = new_blob
        windows.append((off, off + PIXEL_SIZE))
        n_diff = sum(1 for a, b in zip(
            pristine[off:off + PIXEL_SIZE], new_blob) if a != b)
        print(f"  {tex['id']}: window [{off}, {off + PIXEL_SIZE}), "
              f"{n_diff} bytes changed")

    patched = bytes(patched)
    assert len(patched) == len(pristine), "total file size changed"
    assert_outside_window_pristine(pristine, patched, windows)
    print(f"asserts: size unchanged ({len(patched)}); outside windows pristine")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "wb") as f:
        f.write(patched)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    try:
        main()
    except (AssertionError, Exception) as e:  # noqa: BLE001
        print(f"FAILED: {e}", file=sys.stderr)
        sys.exit(1)
