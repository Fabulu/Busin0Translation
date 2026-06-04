#!/usr/bin/env python3
"""Verify the patched R2138 sub7 atlas: check all labels, centering, residual Japanese."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
from psmt4_deswizzle import deswizzle_psmt4

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PIXEL_OFFSET = 0x0755D0
PIXEL_SIZE = 32768
TEX_W, TEX_H = 256, 256
BW_PSMT4, DBW_CT32 = 256, 128

def load(path):
    with open(path, "rb") as f:
        raw = f.read()
    pix = raw[PIXEL_OFFSET:PIXEL_OFFSET + PIXEL_SIZE]
    return deswizzle_psmt4(pix, TEX_W, TEX_H, bw_psmt4=BW_PSMT4, dbw_ct32=DBW_CT32)

lin_orig = load(os.path.join(BASE, "extracted", "packdata_raw", "2138_type29.raw"))
lin_patch = load(os.path.join(BASE, "build", "packdata_resources", "2138_type29.raw"))

STAT_LABELS = [
    (192, 14,  64, 16, "HP"),
    (192, 78,  64, 16, "Str"),
    (192, 98,  64, 16, "Int"),
    (192, 118, 64, 16, "Pie"),
    (192, 138, 64, 16, "Vit"),
    (192, 158, 64, 16, "Agi"),
    (192, 178, 64, 16, "Lck"),
    (192, 198, 64, 16, "Atk"),
    (192, 218, 64, 16, "Eva"),
    (192, 238, 64, 18, "Def"),
]
TAB_LABELS = [
    (0,   0,  96, 20, "Basic Info"),
    (0,  20,  96, 20, "Detail Status"),
    (0,  40,  96, 20, "Item"),
    (0,  58,  96, 20, "Mage Magic"),
    (0,  78,  96, 20, "Priest Magic"),
]
INPUT_MODE_LABELS = [
    (96,   0, 14, 20, "Ka"),
    (96,  20, 14, 20, "ka"),
    (96,  40, 20, 20, "A1"),
    (96,  58, 20, 20, "!@"),
]
CHARGEN_FIELD_LABELS = [
    (110,  0, 56, 20, "Gender"),
    (110, 20, 56, 20, "Race"),
    (110, 40, 56, 20, "Align"),
    (110, 60, 56, 20, "Class"),
    (86,  78, 36, 22, "OK"),
]
LARGE_LABELS = [
    (108, 78, 44, 22, "HP"),
]

ALL = []
ALL += [("STAT", x, y, w, h, t) for x,y,w,h,t in STAT_LABELS]
ALL += [("TAB", x, y, w, h, t) for x,y,w,h,t in TAB_LABELS]
ALL += [("INPUT", x, y, w, h, t) for x,y,w,h,t in INPUT_MODE_LABELS]
ALL += [("CHARGEN", x, y, w, h, t) for x,y,w,h,t in CHARGEN_FIELD_LABELS]
ALL += [("LARGE", x, y, w, h, t) for x,y,w,h,t in LARGE_LABELS]

report = []
report.append("R2138 Sub7 Patch Verification Report")
report.append("=" * 50)
report.append("")
report.append("Patched file: build/packdata_resources/2138_type29.raw")
report.append("Original file: extracted/packdata_raw/2138_type29.raw")
report.append(f"Sub7 pixel offset: 0x{PIXEL_OFFSET:06X}, size: {PIXEL_SIZE}")
report.append(f"Texture: {TEX_W}x{TEX_H} PSMT4, bw={BW_PSMT4}, dbw_ct32={DBW_CT32}")
report.append("")

total_changed = sum(1 for a,b in zip(lin_orig, lin_patch) if a != b)
report.append(f"Total changed pixels: {total_changed} / {TEX_W*TEX_H} ({100*total_changed/(TEX_W*TEX_H):.1f}%)")
report.append("")

report.append("LABEL VERIFICATION")
report.append("-" * 50)

issues = []
for cat, x, y, w, h, text in ALL:
    nonzero_patch = 0
    changed = 0
    for py in range(y, min(y+h, TEX_H)):
        for px in range(x, min(x+w, TEX_W)):
            idx = py * TEX_W + px
            if lin_patch[idx] != 0:
                nonzero_patch += 1
            if lin_patch[idx] != lin_orig[idx]:
                changed += 1

    area = w * h
    fill_pct = 100 * nonzero_patch / area
    change_pct = 100 * changed / area

    min_x, max_x, min_y, max_y = w, 0, h, 0
    for py in range(y, min(y+h, TEX_H)):
        for px in range(x, min(x+w, TEX_W)):
            if lin_patch[py * TEX_W + px] != 0:
                rx, ry = px - x, py - y
                min_x = min(min_x, rx)
                max_x = max(max_x, rx)
                min_y = min(min_y, ry)
                max_y = max(max_y, ry)

    if nonzero_patch == 0:
        status = "EMPTY!"
        issues.append(f"{cat}/{text}: No visible text")
    else:
        text_w = max_x - min_x + 1
        text_h = max_y - min_y + 1
        center_x = (min_x + max_x) / 2
        ideal_cx = w / 2
        offset = center_x - ideal_cx
        if abs(offset) > w * 0.15:
            centering = f"OFF-CENTER (offset={offset:+.1f}px)"
            issues.append(f"{cat}/{text}: {centering}")
        else:
            centering = "centered"
        status = f"OK  bbox=({min_x},{min_y})-({max_x},{max_y})  {text_w}x{text_h}px  {centering}"

    report.append(f"  [{cat:7s}] {text:15s}  fill={fill_pct:4.1f}%  changed={change_pct:4.1f}%  {status}")

report.append("")

# Check clear-only zones
report.append("CLEAR-ONLY ZONES")
report.append("-" * 50)
CLEAR_ONLY = [(0, 98, 96, 14), (96, 98, 70, 14)]
for x, y, w, h in CLEAR_ONLY:
    nonzero = 0
    for py in range(y, min(y+h, TEX_H)):
        for px in range(x, min(x+w, TEX_W)):
            if lin_patch[py * TEX_W + px] != 0:
                nonzero += 1
    if nonzero > 0:
        report.append(f"  Zone ({x},{y} {w}x{h}): {nonzero} residual pixels!")
        issues.append(f"Clear zone ({x},{y}): {nonzero} residual pixels")
    else:
        report.append(f"  Zone ({x},{y} {w}x{h}): clean OK")

report.append("")
report.append("UNPATCHED REGIONS (should be unchanged)")
report.append("-" * 50)
UNPATCHED = [
    (166, 0, 90, 14, "LEVEL"),
    (166, 34, 90, 20, "EXP"),
    (166, 54, 90, 20, "NEXT"),
    (0, 240, 166, 16, "0123456789"),
]
for x, y, w, h, desc in UNPATCHED:
    changed = 0
    for py in range(y, min(y+h, TEX_H)):
        for px in range(x, min(x+w, TEX_W)):
            if lin_patch[py * TEX_W + px] != lin_orig[py * TEX_W + px]:
                changed += 1
    if changed == 0:
        report.append(f"  {desc:15s} ({x},{y} {w}x{h}): unchanged  OK")
    else:
        report.append(f"  {desc:15s} ({x},{y} {w}x{h}): {changed} pixels changed  WARNING")
        issues.append(f"Unpatched region {desc} was modified!")

report.append("")
report.append("ANTI-ALIASING CHECK")
report.append("-" * 50)
for cat, x, y, w, h, text in ALL[:5]:
    vals = set()
    for py in range(y, min(y+h, TEX_H)):
        for px in range(x, min(x+w, TEX_W)):
            v = lin_patch[py * TEX_W + px]
            if v != 0:
                vals.add(v)
    if len(vals) > 2:
        report.append(f"  {text:15s}: {len(vals)} unique values {sorted(vals)} -> anti-aliased")
    elif len(vals) > 0:
        report.append(f"  {text:15s}: {len(vals)} unique values {sorted(vals)} -> binary (no AA)")
    else:
        report.append(f"  {text:15s}: empty")

report.append("")
report.append("RESIDUAL JAPANESE CHECK")
report.append("-" * 50)
# Check if any patched region has pixels matching original but not matching expected English
# Simple approach: count how many pixels in patched regions are identical to original
for cat, x, y, w, h, text in ALL:
    same_as_orig = 0
    total_nonzero_orig = 0
    for py in range(y, min(y+h, TEX_H)):
        for px in range(x, min(x+w, TEX_W)):
            idx = py * TEX_W + px
            if lin_orig[idx] != 0:
                total_nonzero_orig += 1
            if lin_patch[idx] != 0 and lin_patch[idx] == lin_orig[idx]:
                same_as_orig += 1
    if total_nonzero_orig > 0 and same_as_orig > total_nonzero_orig * 0.5:
        report.append(f"  {text:15s}: {same_as_orig}/{total_nonzero_orig} pixels match original -> POSSIBLE RESIDUAL")
        issues.append(f"{cat}/{text}: possible residual Japanese ({same_as_orig} matching pixels)")
    else:
        report.append(f"  {text:15s}: {same_as_orig} matching orig pixels (of {total_nonzero_orig} orig) -> clean")

report.append("")
report.append("SUMMARY")
report.append("=" * 50)
if issues:
    report.append(f"Issues found: {len(issues)}")
    for iss in issues:
        report.append(f"  - {iss}")
else:
    report.append("All labels verified OK. No issues found.")

report.append("")
report.append("All 25 expected labels:")
report.append("  Tab labels (5): Basic Info, Detail Status, Item, Mage Magic, Priest Magic")
report.append("  Input mode (4): Ka, ka, A1, !@")
report.append("  Chargen fields (5): Gender, Race, Align, Class, OK")
report.append("  Large HP (1): HP")
report.append("  Stat labels (10): HP, Str, Int, Pie, Vit, Agi, Lck, Atk, Eva, Def")

txt = "\n".join(report)
print(txt)

out_path = os.path.join(BASE, "dumps", "r2138_sub7_comparison.txt")
with open(out_path, "w") as f:
    f.write(txt)
print(f"\nSaved: {out_path}")
