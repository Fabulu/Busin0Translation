#!/usr/bin/env python3
"""patch_r2880.py — R2880 sub7: pre-rendered opening PROLOGUE NARRATION page.

VERIFIED target (build/recon_v86/sheet-sweep/decode3_report.json +
r2880s7_img0_512x512_p14_gray.png):
  - extracted/packdata_raw/2880_type11.raw, sub7 section at offset 1961856,
    pixel payload at FILE offset 1962944, 131072 bytes
  - ONE 512x512 PSMT4 texture:
        deswizzle_psmt4(data[1962944:1962944+131072], 512, 512,
                        bw_psmt4=512, dbw_ct32=256)
  - Content: the full pre-rendered opening prologue narration page —
    18 left-aligned lines of Japanese at 24px pitch (line tops y=1..409),
    inverted ramp (bg index 15, ink index 0, full 0-15 AA ramp).
    The page is text-only: rows 434-511 and everything outside the glyphs
    is uniform bg index 15 (no border/vignette/background art).

Text data lives in data/strip_labels/r2880_prologue.json (JP transcription
+ English lines matched to the v85 R1193 in-engine narration wording and
the official guide prologue).

Safety: SINGLE-WINDOW write discipline. Only bytes in
[1962944, 1962944+131072) are modified; the resource also contains the
opening-movie stills and VIF/anim sections which are NEVER touched.

Usage:
    python tools/patch_r2880.py
Writes build/packdata_resources/2880_type11.raw and before/after PNGs under
build/recon_v86/r2880-out/. Exits nonzero on any failure.
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

SRC = os.path.join(BASE, "extracted", "packdata_raw", "2880_type11.raw")
OUT = os.path.join(BASE, "build", "packdata_resources", "2880_type11.raw")
OUT_DIR = os.path.join(BASE, "build", "recon_v86", "r2880-out")
LABELS = os.path.join(BASE, "data", "strip_labels", "r2880_prologue.json")

PIXEL_OFF = 1962944
PIXEL_SIZE = 131072
TEX_W = TEX_H = 512
BW_PSMT4 = 512
DBW_CT32 = 256
BG = 15          # background palette index (most common; uniform field)
INK = 0          # full-ink palette index (inverted ramp: 15=bg .. 0=ink)


def quantize(gray_img):
    """Map an L-mode AA rendering (0=bg, 255=ink) onto the 15..0 index ramp,
    matching the original page's full 16-step AA ramp."""
    return [BG - (v * (BG - INK) + 127) // 255 for v in gray_img.getdata()]


def save_gray(linear, path, crop=None, scale=1):
    """Save palette indices as grayscale PNG (ink=black on white, like the
    sheet-sweep p14_gray previews)."""
    img = Image.new("L", (TEX_W, TEX_H))
    img.putdata([min(255, p * 17) for p in linear])
    if crop:
        img = img.crop(crop)
    if scale != 1:
        img = img.resize((img.width * scale, img.height * scale),
                         Image.NEAREST)
    img.save(path)
    return path


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    cfg = json.load(open(LABELS, encoding="utf-8"))
    lay = cfg["layout"]
    lines = cfg["lines"]
    line_tops = lay["line_tops"]
    assert len(lines) == len(line_tops), \
        f"{len(lines)} lines vs {len(line_tops)} line tops"

    pristine = open(SRC, "rb").read()
    print(f"source: {SRC} ({len(pristine)} bytes)")

    # ── decode + roundtrip gate (pre-edit) ────────────────────────────
    blob = pristine[PIXEL_OFF:PIXEL_OFF + PIXEL_SIZE]
    assert len(blob) == PIXEL_SIZE
    linear = bytearray(deswizzle_psmt4(blob, TEX_W, TEX_H,
                                       bw_psmt4=BW_PSMT4, dbw_ct32=DBW_CT32))
    assert bytes(swizzle_psmt4(linear, TEX_W, TEX_H, bw_psmt4=BW_PSMT4,
                               dbw_ct32=DBW_CT32)) == blob, \
        "pre-edit swizzle roundtrip FAILED"
    print("roundtrip (pre-edit): PASS")

    before_png = save_gray(linear, os.path.join(OUT_DIR, "r2880s7_before.png"))
    print(f"before: {before_png}")

    # ── clear the text area ───────────────────────────────────────────
    # Page is text-only (verified: rows 434-511 and all non-glyph pixels are
    # uniform bg=15 — no border/vignette art to preserve).
    cx, cy, cw, ch = lay["clear_region"]
    for y in range(cy, cy + ch):
        for x in range(cx, cx + cw):
            linear[y * TEX_W + x] = BG

    # ── typeset English (PER-WINDOW SLOT model) ───────────────────────
    # The cinematic samples each subtitle ROW through 1-3 FIXED UV-X windows
    # (texelX ranges); 5 rows are SPLIT into two windows with a 24px BLANK
    # dead-zone between them.  We draw each line's seg[k] left-aligned INSIDE
    # window[k] (at window.x0 + left_pad) and HARD-ASSERT its ink width fits the
    # window, so no ink ever lands in a dead-zone (the v92 mid-word-drop bug).
    # The clear step above already blanked the whole region, so dead-zones stay
    # bg=15 as long as we never draw into them.
    base_size = lay["font_size"]
    left_pad = lay.get("left_pad", 2)
    band_h = lay["band_height"]
    n_seg = 0
    for i, (top, ln) in enumerate(zip(line_tops, lines)):
        windows = ln["windows"]
        segs = ln["segs"]
        assert len(windows) == len(segs), \
            f"line {i}: {len(windows)} windows vs {len(segs)} segs"
        for (x0, x1), text in zip(windows, segs):
            win_w = x1 - x0
            cap = win_w - left_pad           # usable ink width inside the window
            font = load_font(base_size, bold=True)
            bbox = font.getbbox(text)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            # HARD FAIL if the segment overflows its window — the cinematic would
            # clip it or spill into the dead-zone. Re-word/re-split in the JSON.
            assert tw <= cap, (
                f"line {i} window [{x0},{x1}] seg width {tw}px > {cap}px: "
                f"'{text}' — re-word/re-split in r2880_prologue.json")
            cell = Image.new("L", (TEX_W, band_h), 0)
            draw = ImageDraw.Draw(cell)
            # CENTER the ink within the window: the cinematic stretches each UV
            # window to its own centered on-screen rect, so a short segment
            # left-aligned at x0 appears left-of-center on screen (the v93 line-0
            # glitch). Centering within [x0,x1] places it centered on screen.
            # Never less than left_pad, so ink stays inside the window/off edges.
            ox = x0 + max(left_pad, (win_w - tw) // 2) - bbox[0]
            draw.text((ox, (band_h - th) // 2 - bbox[1]), text, fill=255,
                      font=font)
            idx = quantize(cell)
            for dy in range(band_h):
                row = (top + dy) * TEX_W
                for dx in range(TEX_W):
                    v = idx[dy * TEX_W + dx]
                    if v != BG:
                        linear[row + dx] = v
            n_seg += 1
            print(f"  i={i:2} y={top:3} win[{x0:3},{x1:3}] w={tw:3}px "
                  f"cap={cap:3}px  '{text}'")
    print(f"  typeset {n_seg} window segments across {len(lines)} rows")

    # ── verify dead-zones are blank ────────────────────────────────────
    # Between adjacent windows of a split row there is a 24px texel band the
    # cinematic never samples; any ink there is dropped on screen. Confirm none.
    for i, (top, ln) in enumerate(zip(line_tops, lines)):
        windows = ln["windows"]
        for k in range(len(windows) - 1):
            gx0, gx1 = windows[k][1], windows[k + 1][0]
            if gx1 <= gx0:
                continue
            for dy in range(band_h):
                row = (top + dy) * TEX_W
                bad = [x for x in range(gx0, gx1) if linear[row + x] != BG]
                assert not bad, (
                    f"line {i} dead-zone [{gx0},{gx1}) has ink at y={top+dy} "
                    f"x={bad[:5]} — a segment overflowed its window")
    print("  dead-zones verified blank")

    after_png = save_gray(linear, os.path.join(OUT_DIR, "r2880s7_after.png"))
    crop_png = save_gray(linear, os.path.join(OUT_DIR, "r2880s7_after_2x_top.png"),
                         crop=(0, 0, 512, 152), scale=2)
    crop_b_png = save_gray(
        bytearray(deswizzle_psmt4(blob, TEX_W, TEX_H, bw_psmt4=BW_PSMT4,
                                  dbw_ct32=DBW_CT32)),
        os.path.join(OUT_DIR, "r2880s7_before_2x_top.png"),
        crop=(0, 0, 512, 152), scale=2)
    print(f"after:  {after_png}\ncrops:  {crop_png}, {crop_b_png}")

    # ── re-swizzle + single-window write ──────────────────────────────
    new_blob = bytes(swizzle_psmt4(linear, TEX_W, TEX_H,
                                   bw_psmt4=BW_PSMT4, dbw_ct32=DBW_CT32))
    assert len(new_blob) == PIXEL_SIZE
    # post-edit roundtrip: decoding what we wrote must give back the edit
    assert bytes(deswizzle_psmt4(new_blob, TEX_W, TEX_H, bw_psmt4=BW_PSMT4,
                                 dbw_ct32=DBW_CT32)) == bytes(linear), \
        "post-edit swizzle roundtrip FAILED"

    patched = bytearray(pristine)
    patched[PIXEL_OFF:PIXEL_OFF + PIXEL_SIZE] = new_blob
    patched = bytes(patched)

    assert len(patched) == len(pristine), "total file size changed"
    assert_outside_window_pristine(pristine, patched,
                                   [(PIXEL_OFF, PIXEL_OFF + PIXEL_SIZE)])
    n_diff = sum(1 for a, b in zip(
        pristine[PIXEL_OFF:PIXEL_OFF + PIXEL_SIZE], new_blob) if a != b)
    print(f"asserts: size unchanged ({len(patched)}); outside "
          f"[{PIXEL_OFF}, {PIXEL_OFF + PIXEL_SIZE}) pristine; "
          f"{n_diff} bytes changed inside window")

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
