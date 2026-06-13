#!/usr/bin/env python3
"""patch_battle_strips — v86 battle + AA pre-rendered kanji strips.

Targets (authoritative spec: build/recon_v86/strip-family-offsets/manifest.json,
every pixel base GS-dump byte-verified against fight1/fight2 VRAM, 32768/32768):
  R1054  battle command menu   pixels @1312,  rects @34656 (16)
  R1360  AA setup menu         pixels @1312,  rects @34656 (8, rect6/7 y-swapped)
  R1361  AA skill names sheet1 pixels @1312,  rects @34656 (20)
  R1362  AA skill names sheet2 pixels @1312,  rects @34656 (18)
  R1363  AA detail UI          pixels @3808,  rects @38560 (83, labeled subset)
  R1364  AA req/row sheet A    pixels @1920,  rects @35456 (rects 28-30 only;
         sheet B @37888 has no text and is NOT touched)

All sheets are 256x256 PSMT4, dbw_ct32=128. Writable window per resource is
ONLY [pixel_off, pixel_off+32768); everything else must stay byte-identical
to the pristine extracted raw. Output goes to build/packdata_resources/<out>.

Labels live in data/strip_labels/battle_labels.json (rect-index keyed).
Per-label options: font (fit start size), mode='freeform' (patch_strip with
per-rect sampled ink + render_label auto-shrink, for cells too narrow for
patch_strip_rects' 9px fit floor — the 24x24 bond kanji), optional=true,
skip=true (leave original pixels), covered_by=N (shares pixels with rect N).

Usage: python tools/patch_battle_strips.py
Exits nonzero on any failure.
"""
import json
import os
import sys
from dataclasses import replace

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "tools"))

from PIL import Image  # noqa: E402

from strip_patcher import (  # noqa: E402
    StripRegion, parse_rect_table, patch_strip_rects, patch_strip,
    assert_outside_window_pristine, sample_rect_indices, save_preview,
    _deswizzle_gated,
)

LABELS_JSON = os.path.join(BASE, "data", "strip_labels", "battle_labels.json")
OUT_DIR = os.path.join(BASE, "build", "packdata_resources")
PNG_DIR = os.path.join(BASE, "build", "recon_v86", "battle-out")

PIXEL_BYTES = 32768  # 256x256 PSMT4
DEFAULT_FONT = 13

RESOURCE_ORDER = ["R1054", "R1360", "R1361", "R1362", "R1363", "R1364"]


def rects_overlap(a, b):
    return (a["x"] < b["x"] + b["w"] and b["x"] < a["x"] + a["w"] and
            a["y"] < b["y"] + b["h"] and b["y"] < a["y"] + a["h"])


def save_png_pair(linear, name, suffix):
    """Save 1x and 2x (nearest) grayscale previews; return the 2x path."""
    p1 = os.path.join(PNG_DIR, f"{name}_{suffix}.png")
    p2 = os.path.join(PNG_DIR, f"{name}_{suffix}_2x.png")
    save_preview(linear, 256, 256, p1, bg=0, ink=15)
    img = Image.open(p1)
    img.resize((512, 512), Image.NEAREST).save(p2)
    return p2


def save_crop(linear, name, suffix, box, scale=3):
    """Save a scaled crop (box = x0,y0,x1,y1) for legibility checks."""
    p1 = os.path.join(PNG_DIR, f"{name}_{suffix}.png")
    img = Image.new("L", (256, 256))
    img.putdata([min(255, p * 17) for p in linear])
    crop = img.crop(box)
    crop.resize((crop.width * scale, crop.height * scale),
                Image.NEAREST).save(p1)
    return p1


def patch_resource(res_name, cfg, results):
    print(f"\n=== {res_name} ===")
    raw_path = os.path.join(BASE, cfg["file"])
    orig = open(raw_path, "rb").read()
    pixel_off = cfg["pixel_off"]
    window = (pixel_off, pixel_off + PIXEL_BYTES)
    region = StripRegion(pixel_off=pixel_off, name=res_name)

    rects = parse_rect_table(orig, cfg["rect_table_off"])
    print(f"  rect table @ {cfg['rect_table_off']}: {len(rects)} rects")

    lin_before = _deswizzle_gated(orig, region)
    save_png_pair(lin_before, res_name, "before")

    labels = {int(k): v for k, v in cfg["labels"].items()}

    patched_idx = []     # rect indices whose pixels we rewrite
    covered_idx = []     # rects sharing pixels with a patched rect
    skipped_idx = []     # skip=true entries (kept original pixels)

    # split into fit-groups (font size -> [(rect, text)]) and freeform list
    groups = {}
    freeform = []
    for idx in sorted(labels):
        lab = labels[idx]
        if lab.get("covered_by") is not None:
            covered_idx.append(idx)
            print(f"  rect {idx}: covered by rect {lab['covered_by']} "
                  f"(same pixels) — no separate patch")
            continue
        if lab.get("skip"):
            skipped_idx.append(idx)
            print(f"  rect {idx}: SKIP requested — original pixels kept")
            continue
        if idx >= len(rects):
            raise ValueError(f"{res_name}: label rect {idx} >= table size")
        if lab.get("mode") == "freeform":
            freeform.append((idx, lab))
        else:
            groups.setdefault(lab.get("font", DEFAULT_FONT), []).append(
                (idx, lab))
        patched_idx.append(idx)

    patched = orig
    for font_size in sorted(groups, reverse=True):
        pairs = [(rects[i], lab["en"]) for i, lab in groups[font_size]]
        for i, _lab in groups[font_size]:
            r = rects[i]
            print(f"  patching rect {i} [{r['x']},{r['y']} "
                  f"{r['w']}x{r['h']}] (font<= {font_size})")
        patched = patch_strip_rects(
            patched, replace(region, font_size=font_size), pairs,
            verbose=False)

    # freeform cells (bond kanji): per-rect sampled ink, render_label
    # auto-shrink (floor 7px) instead of fit_font's 9px floor.
    for idx, lab in freeform:
        r = rects[idx]
        ink, hist = sample_rect_indices(lin_before, 256, r["x"], r["y"],
                                        r["w"], r["h"], region.bg_index)
        print(f"  patching rect {idx} [{r['x']},{r['y']} {r['w']}x{r['h']}] "
              f"freeform '{lab['en']}' font {lab.get('font', 8)} ink={ink}")
        patched = patch_strip(
            patched, replace(region, ink_index=ink),
            [(r["x"], r["y"], r["w"], r["h"], lab["en"],
              lab.get("font", 8))],
            verbose=False)

    # ---- asserts ----
    assert len(patched) == len(orig), "size changed"
    assert_outside_window_pristine(orig, patched, [window])
    print(f"  ASSERT ok: size {len(patched)} preserved; bytes outside "
          f"[{window[0]}, {window[1]}) pristine")

    lin_after = _deswizzle_gated(patched, region)
    patched_rects = [rects[i] for i in patched_idx]
    untouched_checked = untouched_overlap = 0
    for i, r in enumerate(rects):
        if i in patched_idx:
            continue
        if i in covered_idx:
            untouched_overlap += 1
            continue
        # Unlabeled rects that overlap a patched rect (e.g. R1363's 1x1
        # dummies at (255,0) inside bond cell 21) are NOT exempt: they fall
        # through to the strict pixel-identity check below, so any real
        # change there still fails the build.
        for dy in range(r["h"]):
            row = (r["y"] + dy) * 256
            a = lin_before[row + r["x"]:row + r["x"] + r["w"]]
            b = lin_after[row + r["x"]:row + r["x"] + r["w"]]
            assert a == b, (f"{res_name}: untouched rect {i} "
                            f"[{r['x']},{r['y']} {r['w']}x{r['h']}] modified "
                            f"at row {dy}")
        untouched_checked += 1
    print(f"  ASSERT ok: {untouched_checked} untouched rects pixel-identical "
          f"({untouched_overlap} skipped as pixel-shared with patched rects)")

    after_png = save_png_pair(lin_after, res_name, "after")

    out_path = os.path.join(OUT_DIR, cfg["out"])
    with open(out_path, "wb") as f:
        f.write(patched)
    print(f"  wrote {out_path}")

    results[res_name] = {
        "patched_rects": patched_idx,
        "covered_rects": covered_idx,
        "skipped_rects": skipped_idx,
        "untouched_verified": untouched_checked,
        "out": out_path,
        "after_png": after_png,
    }
    return lin_before, lin_after


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(PNG_DIR, exist_ok=True)
    cfgs = json.load(open(LABELS_JSON, encoding="utf-8"))
    results = {}
    for res_name in RESOURCE_ORDER:
        lin_b, lin_a = patch_resource(res_name, cfgs[res_name], results)
        if res_name == "R1363":
            # legibility crops for the 24x24 bond-kanji column (rects 21-29:
            # x 208..256, y 0..192) at 1x and 3x
            save_crop(lin_a, "R1363", "bond_after_1x", (208, 0, 256, 192),
                      scale=1)
            save_crop(lin_a, "R1363", "bond_after_3x", (208, 0, 256, 192),
                      scale=3)
            save_crop(lin_b, "R1363", "bond_before_3x", (208, 0, 256, 192),
                      scale=3)

    print("\n=== SUMMARY ===")
    for res_name in RESOURCE_ORDER:
        r = results[res_name]
        print(f"  {res_name}: {len(r['patched_rects'])} rects patched, "
              f"{r['untouched_verified']} untouched verified, "
              f"skipped={r['skipped_rects']} -> {r['out']}")
    print("ALL RESOURCES PATCHED, ALL ASSERTS PASSED")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nFATAL: {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)
