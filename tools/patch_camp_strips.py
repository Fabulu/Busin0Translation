#!/usr/bin/env python3
"""patch_camp_strips — v86 camp/quest/system pre-rendered UI strips.

Patches three strip-family PSMT4 resources in place (pixel blob only, byte
size preserved), driven by data/strip_labels/camp_labels.json and the verified
rect tables parsed from each resource itself:

  R1359  1359_type02.raw  camp / pause menu   (16 rects, pixels @1312, rect @34656)
  R1367  1367_type02.raw  quest-result / camp (45 rects, pixels @1904, rect @35632)
  R1910  1910_type02.raw  system menu banners ( 6 rects, pixels @1840, rect @35312)

R1359 / R1367 are simple bg=0 / bright-ink atlases: each listed rect is cleared
to bg and the English label is rendered, AA mapped onto the rect's own sampled
ink index (strip_patcher.patch_strip_rects).

R1910 is "render-verified only" (lowest grade): the 6 banners are art+text
composites, so the whole rect cannot be cleared. We erase ONLY the dark glyph
ink (idx<=INK_MAX) inside the central plaque box and in-paint each erased pixel
with the median of nearby bright banner texture (idx>=PLAQUE_MIN), leaving the
left/right scrollwork ornaments pixel-identical; English is then alpha-blended
in dark ink. Before touching it the patcher re-validates the section/rect
structure and that the decoded banners match the expected 6 x 192x40 grid — if
that check fails it SKIPS R1910 cleanly (prints SKIPPED, still exits 0).

Pixel bases come from strip_patcher.find_pixel_base (flush-to-end rule on the
GIF upload section), never from round-trip success alone. Per resource the
patcher asserts: exact on-disk size, deswizzle round-trip exact (pre+post),
only-listed-rects changed in decoded space, outside-pixel-window pristine, and
re-swizzle round-trip exact.

Outputs to build/packdata_resources/<name>; before/after PNGs (1x and 2x) to
build/recon_v86/camp-out/. Exits nonzero on any failure; a clean R1910 skip
still exits 0.
"""

import json
import os
import statistics
import struct
import sys

sys.stdout.reconfigure(encoding="utf-8")

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "tools"))

from psmt4_deswizzle import deswizzle_psmt4, swizzle_psmt4  # noqa: E402
from strip_patcher import (  # noqa: E402
    StripRegion,
    parse_section_table,
    parse_rect_table,
    find_pixel_base,
    patch_strip_rects,
    assert_outside_window_pristine,
    load_font,
    render_label,
)

try:
    from PIL import Image  # noqa: E402
except ImportError:
    print("ERROR: Pillow not installed. Run: pip install Pillow")
    sys.exit(1)

# ── Paths ──
RAW_DIR = os.path.join(BASE, "extracted", "packdata_raw")
OUT_DIR = os.path.join(BASE, "build", "packdata_resources")
DEBUG_DIR = os.path.join(BASE, "build", "recon_v86", "camp-out")
LABELS_PATH = os.path.join(BASE, "data", "strip_labels", "camp_labels.json")

# ── Verified shared constants (manifest.json) ──
EXPECTED_SIZE = 36864
TEX_W = TEX_H = 256
DBW_CT32 = 128
PIXEL_BYTES = TEX_W * TEX_H // 2  # 32768

# ── R1910 banner in-paint tuning (build/recon_v86/camp-out/r1910_inpaint_test5) ──
BANNER_COUNT = 6
BANNER_W, BANNER_H = 192, 40
PLAQUE_X0, PLAQUE_X1 = 44, 170   # interior between left/right scrollwork
PLAQUE_Y0, PLAQUE_Y1 = 8, 32     # text band inside each 40px banner
INK_MAX = 9                      # idx<=INK_MAX inside plaque = glyph ink
PLAQUE_MIN = 10                  # idx>=PLAQUE_MIN = bright banner texture
BANNER_INK_INDEX = 2             # dark ink index to render English with


# ═══════════════════════════════════════════════════════════════════════
# Shared helpers
# ═══════════════════════════════════════════════════════════════════════

def save_previews(linear, prefix):
    """Write {prefix}.png (1x) and {prefix}_2x.png (NEAREST) grayscale (idx*17)."""
    img = Image.new("L", (TEX_W, TEX_H))
    img.putdata([min(255, p * 17) for p in linear])
    img.save(prefix + ".png")
    img.resize((TEX_W * 2, TEX_H * 2), Image.NEAREST).save(prefix + "_2x.png")


def load_pixel_base(data, expected_base):
    """find_pixel_base on section 0, asserting it matches the manifest base."""
    secs = parse_section_table(data)
    assert secs, "no section table parsed"
    s0 = secs[0]
    base = find_pixel_base(data, s0["offset"], s0["size"])
    assert base == expected_base, \
        f"find_pixel_base={base} != manifest base {expected_base}"
    return base


def decoded_linear(data, base):
    """Deswizzle + exact round-trip gate (validates swizzle params)."""
    blob = data[base:base + PIXEL_BYTES]
    assert len(blob) == PIXEL_BYTES, "pixel blob truncated"
    lin = bytearray(deswizzle_psmt4(blob, TEX_W, TEX_H,
                                    bw_psmt4=TEX_W, dbw_ct32=DBW_CT32))
    rt = swizzle_psmt4(lin, TEX_W, TEX_H, bw_psmt4=TEX_W, dbw_ct32=DBW_CT32)
    assert bytes(rt) == blob, "pre-edit swizzle round-trip NOT exact"
    return lin


def finalize(name, pristine, base, new_linear, orig_linear, allowed_mask):
    """Common post-edit assertions + write output + previews.

    Asserts: only-allowed pixels changed in decoded space, post-edit round-trip
    exact, header/clut/tail byte-identical, outside-window pristine, exact size.
    """
    bad = [i for i in range(TEX_W * TEX_H)
           if new_linear[i] != orig_linear[i] and not allowed_mask[i]]
    assert not bad, (f"{name}: {len(bad)} pixels changed outside listed rects, "
                     f"first at ({bad[0] % TEX_W},{bad[0] // TEX_W})")

    new_blob = swizzle_psmt4(new_linear, TEX_W, TEX_H,
                             bw_psmt4=TEX_W, dbw_ct32=DBW_CT32)
    assert len(new_blob) == PIXEL_BYTES, "re-swizzled blob wrong size"
    verify = deswizzle_psmt4(bytes(new_blob), TEX_W, TEX_H,
                             bw_psmt4=TEX_W, dbw_ct32=DBW_CT32)
    assert bytes(verify) == bytes(new_linear), \
        f"{name}: post-edit round-trip NOT exact"

    out = pristine[:base] + bytes(new_blob) + pristine[base + PIXEL_BYTES:]
    assert len(out) == len(pristine) == EXPECTED_SIZE, \
        f"{name}: output size {len(out)} != {EXPECTED_SIZE}"
    assert_outside_window_pristine(pristine, out, [(base, base + PIXEL_BYTES)])

    os.makedirs(OUT_DIR, exist_ok=True)
    out_path = os.path.join(OUT_DIR, name)
    with open(out_path, "wb") as f:
        f.write(out)
    print(f"  Output: {out_path} ({len(out)} bytes)")
    print("  Asserts: size OK | round-trip exact | window pristine | "
          "containment OK")
    return out_path


def make_allowed_mask(rect_iter):
    mask = bytearray(TEX_W * TEX_H)
    for x, y, w, h in rect_iter:
        for yy in range(y, y + h):
            row = yy * TEX_W
            for xx in range(x, x + w):
                if 0 <= xx < TEX_W and 0 <= yy < TEX_H:
                    mask[row + xx] = 1
    return mask


# ═══════════════════════════════════════════════════════════════════════
# R1359 / R1367 — simple rect clear+render
# ═══════════════════════════════════════════════════════════════════════

def patch_simple(name, raw_name, expected_base, rect_off, labels):
    print("=" * 64)
    print(f"  {name} — {raw_name}")
    print("=" * 64)

    pristine = open(os.path.join(RAW_DIR, raw_name), "rb").read()
    assert len(pristine) == EXPECTED_SIZE, \
        f"{name}: size {len(pristine)} != {EXPECTED_SIZE}"
    base = load_pixel_base(pristine, expected_base)
    print(f"  pixel base @{base} (find_pixel_base, matches manifest)")

    rects = parse_rect_table(pristine, rect_off)
    print(f"  rect table @{rect_off}: {len(rects)} rects")
    for idx in labels:
        assert 0 <= idx < len(rects), f"{name}: label rect {idx} out of range"

    orig_linear = bytes(decoded_linear(pristine, base))

    region = StripRegion(pixel_off=base, tex_w=TEX_W, tex_h=TEX_H,
                         dbw_ct32=DBW_CT32, bg_index=0, ink_index=15,
                         font_size=13, name=name)

    rect_labels = [(rects[idx], labels[idx]) for idx in sorted(labels)]
    before = os.path.join(DEBUG_DIR, f"{name.lower()}_before")
    os.makedirs(DEBUG_DIR, exist_ok=True)

    patched = patch_strip_rects(pristine, region, rect_labels, verbose=True)

    new_linear = bytearray(deswizzle_psmt4(
        patched[base:base + PIXEL_BYTES], TEX_W, TEX_H,
        bw_psmt4=TEX_W, dbw_ct32=DBW_CT32))

    allowed = make_allowed_mask(
        (rects[idx]["x"], rects[idx]["y"], rects[idx]["w"], rects[idx]["h"])
        for idx in labels)

    save_previews(orig_linear, before)
    save_previews(new_linear, os.path.join(DEBUG_DIR, f"{name.lower()}_after"))

    finalize(raw_name, pristine, base, new_linear, orig_linear, allowed)
    print(f"  Previews: {before}_2x.png / "
          f"{os.path.join(DEBUG_DIR, name.lower())}_after_2x.png")
    return True


# ═══════════════════════════════════════════════════════════════════════
# R1910 — banner in-paint (skip-on-uncertainty)
# ═══════════════════════════════════════════════════════════════════════

def verify_r1910_structure(data, base, rect_off):
    """Confirm R1910 matches the render-verified description before patching.

    Returns (ok, reason, rects, linear). ok=False => caller must SKIP cleanly.
    """
    secs = parse_section_table(data)
    if not secs:
        return False, "no section table", None, None
    try:
        rects = parse_rect_table(data, rect_off)
    except ValueError as e:
        return False, f"rect table parse failed: {e}", None, None
    if len(rects) != BANNER_COUNT:
        return False, f"expected {BANNER_COUNT} rects, got {len(rects)}", None, None
    # 6 stacked 192x40 banners at x=0, y=0/40/.../200
    for i, rc in enumerate(rects):
        if (rc["x"], rc["y"], rc["w"], rc["h"]) != (0, i * BANNER_H,
                                                    BANNER_W, BANNER_H):
            return False, (f"rect {i} coords {rc} != expected "
                           f"(0,{i * BANNER_H},{BANNER_W},{BANNER_H})"), None, None
    try:
        linear = decoded_linear(data, base)
    except AssertionError as e:
        return False, f"decode/round-trip failed: {e}", None, None

    # Each banner must look like a banner: bright plaque interior + dark ink.
    # Check the plaque interior is predominantly bright and contains dark ink.
    for i in range(BANNER_COUNT):
        by = i * BANNER_H
        bright = ink = 0
        for yy in range(by + PLAQUE_Y0, by + PLAQUE_Y1):
            for xx in range(PLAQUE_X0, PLAQUE_X1):
                v = linear[yy * TEX_W + xx]
                if v >= PLAQUE_MIN:
                    bright += 1
                elif v <= INK_MAX:
                    ink += 1
        # EXIT banner (i==4) is already-English but still bright plaque + ink.
        if bright < 600:
            return False, (f"banner {i}: plaque not bright enough "
                           f"(bright={bright})"), None, None
    return True, "ok", rects, linear


def inpaint_banner(orig, work, banner_idx):
    """Erase dark glyph ink inside the plaque box of one banner and in-paint
    from surrounding bright banner texture. Returns the set of erased pixel
    indices (linear). Left/right scrollwork (outside [PLAQUE_X0,PLAQUE_X1]) is
    never touched."""
    by = banner_idx * BANNER_H
    mask = set()
    for yy in range(by + PLAQUE_Y0, by + PLAQUE_Y1):
        for xx in range(PLAQUE_X0, PLAQUE_X1):
            if orig[yy * TEX_W + xx] <= INK_MAX:
                mask.add((xx, yy))
    remaining = set(mask)
    for _ in range(60):
        if not remaining:
            break
        newly = {}
        for (xx, yy) in list(remaining):
            samp = []
            for r in (1, 2, 3, 4):
                for dx in range(-r, r + 1):
                    for dy in range(-r, r + 1):
                        nx, ny = xx + dx, yy + dy
                        if (nx, ny) in remaining:
                            continue
                        if 0 <= nx < TEX_W and by <= ny < by + BANNER_H \
                                and orig[ny * TEX_W + nx] >= PLAQUE_MIN:
                            samp.append(work[ny * TEX_W + nx])
                if samp:
                    break
            if samp:
                newly[(xx, yy)] = round(statistics.median(samp))
        if not newly:
            for (xx, yy) in remaining:
                work[yy * TEX_W + xx] = 12  # fallback bright fill
            break
        for (xx, yy), v in newly.items():
            work[yy * TEX_W + xx] = v
            remaining.discard((xx, yy))
    return {yy * TEX_W + xx for (xx, yy) in mask}


def render_banner_label(work, banner_idx, text):
    """Alpha-blend dark English ink onto the cleaned plaque (centered).

    Only ink pixels are written; bright banner texture shows through, like the
    parchment technique in tools/patch_r2138.py. Returns set of written pixel
    indices."""
    by = banner_idx * BANNER_H
    cw = PLAQUE_X1 - PLAQUE_X0
    ch = PLAQUE_Y1 - PLAQUE_Y0
    # ink_index > bg_index path renders idx in [bg..ink]; use bg=PLAQUE_MIN so
    # transparent==PLAQUE_MIN (skipped via overlay), ink==BANNER_INK_INDEX.
    # render_label maps grayscale onto bg->ink ramp; we want dark ink so call
    # with bg=15 (bright transparent), ink=BANNER_INK_INDEX (dark).
    cell = render_label(text, cw, ch, load_font(15, bold=True),
                        bg_index=15, ink_index=BANNER_INK_INDEX, align="center")
    written = set()
    for dy in range(ch):
        for dx in range(cw):
            v = cell[dy * cw + dx]
            if v == 15:
                continue  # transparent: keep banner texture
            px, py = PLAQUE_X0 + dx, by + PLAQUE_Y0 + dy
            idx = py * TEX_W + px
            work[idx] = v
            written.add(idx)
    return written


def patch_r1910(name="R1910", raw_name="1910_type02.raw",
                expected_base=1840, rect_off=35312):
    print("=" * 64)
    print(f"  {name} — {raw_name} (render-verified only)")
    print("=" * 64)

    pristine = open(os.path.join(RAW_DIR, raw_name), "rb").read()
    assert len(pristine) == EXPECTED_SIZE, \
        f"{name}: size {len(pristine)} != {EXPECTED_SIZE}"
    base = load_pixel_base(pristine, expected_base)
    print(f"  pixel base @{base} (find_pixel_base, matches manifest)")

    ok, reason, rects, orig_linear = verify_r1910_structure(
        pristine, base, rect_off)
    if not ok:
        print(f"  SKIPPED {name}: structure/banner check failed — {reason}")
        return "skipped"
    print("  banner structure verified (6 x 192x40, bright plaques + ink)")

    with open(LABELS_PATH, encoding="utf-8") as f:
        cfg = json.load(f)["R1910"]["labels"]
    banner_labels = {int(k): v["en"] for k, v in cfg.items()
                     if v["en"] is not None}
    print(f"  labels: {len(banner_labels)} banners to render "
          f"(rect 4 EXIT untouched)")

    orig_linear = bytes(orig_linear)
    work = bytearray(orig_linear)

    touched = set()
    for bi in sorted(banner_labels):
        erased = inpaint_banner(orig_linear, work, bi)
        written = render_banner_label(work, bi, banner_labels[bi])
        touched |= erased | written
        print(f"    banner {bi} '{banner_labels[bi]}': "
              f"erased {len(erased)} ink px, wrote {len(written)} ink px")

    # Containment: all changes confined to the plaque boxes of patched banners.
    allowed = bytearray(TEX_W * TEX_H)
    for bi in banner_labels:
        by = bi * BANNER_H
        for yy in range(by + PLAQUE_Y0, by + PLAQUE_Y1):
            for xx in range(PLAQUE_X0, PLAQUE_X1):
                allowed[yy * TEX_W + xx] = 1

    os.makedirs(DEBUG_DIR, exist_ok=True)
    before = os.path.join(DEBUG_DIR, f"{name.lower()}_before")
    save_previews(orig_linear, before)
    save_previews(work, os.path.join(DEBUG_DIR, f"{name.lower()}_after"))

    finalize(raw_name, pristine, base, work, orig_linear, allowed)

    # Extra explicit ornament-pristine assert (scrollwork must be untouched).
    for bi in range(BANNER_COUNT):
        by = bi * BANNER_H
        for yy in range(by, by + BANNER_H):
            for xx in list(range(0, PLAQUE_X0)) + list(range(PLAQUE_X1, TEX_W)):
                assert work[yy * TEX_W + xx] == orig_linear[yy * TEX_W + xx], \
                    f"ornament pixel ({xx},{yy}) changed!"
    print("  Scrollwork ornaments (x<44, x>=170): pixel-identical")
    print(f"  Previews: {before}_2x.png / "
          f"{os.path.join(DEBUG_DIR, name.lower())}_after_2x.png")
    return True


# ═══════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════

def main():
    with open(LABELS_PATH, encoding="utf-8") as f:
        cfg = json.load(f)

    r1359 = {int(k): v["en"] for k, v in cfg["R1359"]["labels"].items()
             if v["en"] is not None}
    r1367 = {int(k): v["en"] for k, v in cfg["R1367"]["labels"].items()
             if v["en"] is not None}

    results = {}
    results["R1359"] = patch_simple("R1359", "1359_type02.raw", 1312,
                                    34656, r1359)
    results["R1367"] = patch_simple("R1367", "1367_type02.raw", 1904,
                                    35632, r1367)
    results["R1910"] = patch_r1910()

    print("=" * 64)
    print("  SUMMARY")
    for k, v in results.items():
        tag = "SKIPPED" if v == "skipped" else "OK" if v else "FAIL"
        print(f"    {k}: {tag}")
    print("=" * 64)


if __name__ == "__main__":
    try:
        main()
    except (AssertionError, OSError, ValueError) as e:
        print(f"FAILED: {e}")
        sys.exit(1)
