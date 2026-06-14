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

PER-WINDOW SLOT model (v94) — IDENTICAL discipline to tools/patch_r2880.py.
Each page is a TWO-COLUMN poetic layout: a LEFT column window [0,232] and a
RIGHT column window [256,512], separated by a 24px BLANK gutter dead-zone at
x=232..256 (a few rows are single CENTERED windows). The cinematic samples
each row band through FIXED UV-X windows; English authored as one continuous
run would spill into the gutter dead-zone and be DROPPED on screen (the R2880
v92 mid-word-drop bug). FIX: each row band lists 'windows' ([x0,x1] texels)
and 'segs' (one English segment per window); we draw seg[k] left-aligned at
windows[k][0]+left_pad and HARD-ASSERT its ink width fits the window, leaving
every gutter dead-zone blank.

No GS dump of the ending exists; the windows were inferred from the JP page's
two-column ink structure on the 24px grid (build/recon_cine/ending). The
English was condensed from the v86 transcription to fit each window at 16px.

Transcription + per-window English live in data/strip_labels/r2881_ending.json.

Safety: SINGLE-WINDOW write discipline. Only bytes inside the two pixel
windows are modified; the rest of the 2.3MB resource (movie stills, VIF/anim
sections, credits art, the small img2/3/4 border sprites) is never touched.

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
BG = 15          # background palette index (uniform field)
INK = 0          # full-ink palette index (inverted ramp: 15=bg .. 0=ink)


def quantize(gray_img):
    """Map an L-mode AA rendering (0=bg, 255=ink) onto the 15..0 index ramp."""
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


def patch_page(pristine, tex, lay):
    off = tex["pixel_off"]
    tag = tex["id"]
    line_tops = lay["line_tops"]
    band_h = lay["band_height"]
    base_size = lay["font_size"]
    left_pad = lay.get("left_pad", 2)
    lines = tex["lines"]
    assert len(lines) == len(line_tops), \
        f"{tag}: {len(lines)} lines vs {len(line_tops)} line tops"

    blob = pristine[off:off + PIXEL_SIZE]
    assert len(blob) == PIXEL_SIZE
    linear = bytearray(deswizzle_psmt4(blob, TEX_W, TEX_H,
                                       bw_psmt4=BW_PSMT4, dbw_ct32=DBW_CT32))
    assert bytes(swizzle_psmt4(linear, TEX_W, TEX_H, bw_psmt4=BW_PSMT4,
                               dbw_ct32=DBW_CT32)) == blob, \
        f"{tag} pre-edit swizzle roundtrip FAILED"

    save_gray(linear, os.path.join(OUT_DIR, f"r2881s7_{tag}_before.png"))

    # ── clear the whole text field ────────────────────────────────────
    # Pages are text-only on a uniform bg=15 field (verified: no border art on
    # the two 512x512 pages; border sprites live in img2/3/4, never touched).
    for i in range(TEX_W * TEX_H):
        linear[i] = BG

    # ── typeset English (PER-WINDOW SLOT model) ───────────────────────
    font = load_font(base_size, bold=True)
    n_seg = 0
    for top, ln in zip(line_tops, lines):
        windows = ln["windows"]
        segs = ln["segs"]
        assert len(windows) == len(segs), \
            f"{tag} band {ln['band']}: {len(windows)} windows vs {len(segs)} segs"
        for (x0, x1), text in zip(windows, segs):
            if not text:
                continue
            win_w = x1 - x0
            cap = win_w - left_pad           # usable ink width inside the window
            bbox = font.getbbox(text)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            # HARD FAIL if the segment overflows its window — the cinematic
            # would clip it or spill into the gutter dead-zone. Re-word/re-split
            # in r2881_ending.json.
            assert tw <= cap, (
                f"{tag} band {ln['band']} window [{x0},{x1}] seg width {tw}px "
                f"> {cap}px: '{text}' — re-word/re-split in r2881_ending.json")
            cell = Image.new("L", (TEX_W, band_h), 0)
            draw = ImageDraw.Draw(cell)
            # left-align ink at x0+left_pad, vertically centered in the band
            ox = x0 + left_pad - bbox[0]
            draw.text((ox, (band_h - th) // 2 - bbox[1]), text, fill=255,
                      font=font)
            idx = quantize(cell)
            for dy in range(band_h):
                if top + dy >= TEX_H:
                    break
                row = (top + dy) * TEX_W
                for dx in range(TEX_W):
                    v = idx[dy * TEX_W + dx]
                    if v != BG:
                        linear[row + dx] = v
            n_seg += 1
    print(f"  {tag}: typeset {n_seg} window segments across {len(lines)} bands")

    # ── verify gutter dead-zones are blank ─────────────────────────────
    # Between adjacent windows of a split band there is a texel band the
    # cinematic never samples; any ink there is dropped on screen. Confirm none.
    for top, ln in zip(line_tops, lines):
        windows = ln["windows"]
        for k in range(len(windows) - 1):
            gx0, gx1 = windows[k][1], windows[k + 1][0]
            if gx1 <= gx0:
                continue
            for dy in range(band_h):
                if top + dy >= TEX_H:
                    break
                row = (top + dy) * TEX_W
                bad = [x for x in range(gx0, gx1) if linear[row + x] != BG]
                assert not bad, (
                    f"{tag} band {ln['band']} dead-zone [{gx0},{gx1}) has ink "
                    f"at y={top+dy} x={bad[:5]} — a segment overflowed")
    print(f"  {tag}: dead-zones verified blank")

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
    lay = cfg["layout"]
    pristine = open(SRC, "rb").read()
    print(f"source: {SRC} ({len(pristine)} bytes)")

    patched = bytearray(pristine)
    windows = []
    for tex in cfg["textures"]:
        off, new_blob = patch_page(pristine, tex, lay)
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
