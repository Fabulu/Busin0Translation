#!/usr/bin/env python3
"""R2655 LIBRARY screen decorative pixel strips -> English (wave 5).

R2655 (extracted/packdata_raw/2655_type07.raw, 200704 B) is the LIBRARY
screen's texture container.  Wave-4 recon (scratchpad wave4_recon/
r2655_s6_256x256_2x.png, r2655_s4_d17/d19/d21 PNGs, lib_Screenshot.png)
solved the layout:

  Section s6 @0x28790 (pixel base 0x28830, flush-to-end verified):
    32768 B = 256x256 PSMT4, dbw_ct32=128 -- the brush-calligraphy BANNER
    SHEET holding the section titles (drawn as the right-pane title and,
    pre-MSG-fix, as list rows).  CLUT (d1 @0x30830): index 15 =
    TRANSPARENT, ink = indices 0-14 (brown/gold ramp; JP strokes have a
    dark-brown fringe idx 13/7 and a bright gold core idx 2/6/11).

  Section s4 @0x21A10 (pixel base 0x22040, 23 upload descriptors,
  tile/CLUT interleaved):
    d17 @0x25240 128x128 (dbw 64)  sub-tab labels (CLUT d18: bg=15
        transparent, ink core = idx 0 white, dark AA fringe at high idx)
    d19 @0x27280  64x64  (dbw 32)  ": Show/Hide  (green PS-triangle)"
        (CLUT d20: bg=15, white core idx 0, grays 1-4; GREENS at idx 5-14
        are reserved for the triangle icon -- the English AA ramp must
        avoid them)
    d21 @0x27AC0  64x64  (dbw 32)  footer ": Fast-fwd / R2 / arrows / +"
        (CLUT d22: INVERTED vs the rest of R2655 -- bg = idx 0
        transparent, ink core = idx 15 white; standard dark-bg ramp)
    d4 "NEW" tag and d14 L1/R1 icons are language-neutral: untouched.

  NO BE rect-table exists in R2655 (type07 is not the strip-family
  container); UV geometry is external.  Therefore this patcher is STRICT
  IN-PLACE RE-INK ONLY: each measured JP-ink band box is cleared to the
  region's transparent index and the English is rendered INSIDE the same
  box.  Nothing is moved, resized or appended; every byte outside the four
  pixel blobs stays byte-identical, and every PIXEL outside the declared
  boxes stays identical (both asserted).  This is the R2138-sub4 lesson:
  transfer geometry must remain pristine or the VIF upload crashes.

Split-cell composition (measured, mirrors the JP art):
    on-screen "SHIMUZON no shuki" =  shi cell (98-126, x132-155)
                                   + "muzon no shuki" cell (130-159)
    on-screen "jouhou file"       =  jou cell (226-253, x196-223)
                                   + "hou file" cell (195-221, x149+)
  The full English title is rendered into the LARGE cell and the small
  leading cell is cleared to transparent (leaves a small leading gap on
  screen -- cannot be avoided without the external UV table).

English text canon (see REPORT in the patch log):
    data/r2654_library_names.json sub 6:  The Karman Report / Request
        File / Info File / Simzon's Journal
    data/translate_chunks/chunk_r2654_library_fix.json body labels:
        Item Compendium / Person Register / Glossary / Book List
    data/type2_translated/batch_03.json: Adventurer's Guide
    data/strip_labels/battle_labels.json: Allied Action (AA canon) ->
        the AA compendium (JP "sennjutsu zukan") = "Allied Actions"
    Monster Compendium: no shipped on-screen string; follows the
        r2654_library_names.json _comment ("sub 28 monster compendium")
        and the Item Compendium pattern.

INPUT  (pristine only): extracted/packdata_raw/2655_type07.raw
OUTPUT: build/packdata_resources/2655_type07.raw
  If the output already exists it must be byte-identical to the pristine
  input (never yet patched) or to this run's own product (idempotent
  re-run); anything else aborts.
DEBUG PNGs (before/after, 2x, grayscale + CLUT color):
  <scratchpad>/wave5_strips/  (falls back to build/recon_v86/r2655-out/)

Build wiring (NOT done here): add
    'tools/patch_r2655_library_strips.py',
to the Step 6.5 v86 patcher list in build/build_v9.py (order independent
of the R2654 patchers -- R2655 is a separate resource).

Exits nonzero on any assertion failure.
"""

import os
import struct
import sys

sys.stdout.reconfigure(encoding="utf-8")

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "tools"))

from psmt4_deswizzle import deswizzle_psmt4, swizzle_psmt4  # noqa: E402
from strip_patcher import (  # noqa: E402
    parse_section_table, parse_upload_descriptors, find_pixel_base,
    assert_outside_window_pristine)

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("ERROR: Pillow not installed. Run: pip install Pillow")
    sys.exit(1)

# ── Paths ──
IN_PATH = os.path.join(BASE, "extracted", "packdata_raw", "2655_type07.raw")
OUT_DIR = os.path.join(BASE, "build", "packdata_resources")
OUT_PATH = os.path.join(OUT_DIR, "2655_type07.raw")

_SCRATCH = (r"C:\Users\FABIAN~1\AppData\Local\Temp\claude"
            r"\C--Programmieren-wizardrytranslation"
            r"\ecc36257-22cb-4b50-aba9-4e922aa0f1af\scratchpad\wave5_strips")
DEBUG_DIR = _SCRATCH if os.path.isdir(os.path.dirname(_SCRATCH)) else \
    os.path.join(BASE, "build", "recon_v86", "r2655-out")

RES_SIZE = 200704

# ── Structural signature (pristine-input gate) ──
EXPECT_SECTIONS = [  # (id, offset, size)
    (0, 0x70, 64), (1, 0xB0, 131296), (2, 0x20190, 6), (3, 0x201A0, 6252),
    (4, 0x21A10, 26864), (5, 0x28300, 1160), (6, 0x28790, 32992)]
S4_OFF, S4_SIZE = 0x21A10, 26864
S6_OFF, S6_SIZE = 0x28790, 32992
S4_PIXEL_BASE = 0x22040          # 23 descriptors, flush-to-end
S6_PIXEL_BASE = 0x28830          # 256x256 PSMT4 banner sheet

# ── Fonts: FAIL LOUDLY (no silent load_default fallback) ──
BANNER_FONT_CANDS = ["C:/Windows/Fonts/timesbd.ttf",
                     "C:/Windows/Fonts/georgiab.ttf"]
TILE_FONT_CANDS = ["C:/Windows/Fonts/arialbd.ttf"]
FONT_FLOOR = 9


def resolve_font_path(cands, what):
    for fp in cands:
        if os.path.exists(fp):
            return fp
    print(f"FATAL: no TTF found for {what} (tried {cands}) -- refusing the "
          "Pillow bitmap fallback; install the font or edit the candidate "
          "list.")
    sys.exit(1)


_font_cache = {}


def load_font(path, size):
    key = (path, size)
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(path, size)
    return _font_cache[key]


# ── AA ramps: coverage 0..255 -> palette index (index 0 of each ramp is
#    the transparent background; last entry is the full-opacity ink core) ──
RAMP_S6 = [15, 13, 7, 5, 1, 2]      # brown fringe -> gold core (JP anatomy)
RAMP_D17 = [15, 14, 12, 9, 4, 2, 0]  # dark AA rim -> white core (JP anatomy)
RAMP_D19 = [15, 4, 3, 2, 1, 0]       # grays only -- idx 5-14 are the
                                     # triangle's GREENS, never used for text
RAMP_D21 = [0, 1, 4, 8, 12, 15]      # inverted tile: transparent -> white


def ramp_map(gray, ramp):
    """Map AA coverage 0..255 onto a ramp of palette indices."""
    n = len(ramp)
    return ramp[min(n - 1, gray * n // 256)]


def render_cell(text, w, h, font_path, start_size, ramp):
    """Render text into a w*h index cell, auto-shrinking to fit w-2.

    Returns (cell_indices, used_size).  Raises if the floor size still
    does not fit (caller must shorten the label).
    """
    size = start_size
    font = load_font(font_path, size)
    bbox = font.getbbox(text)
    while bbox and (bbox[2] - bbox[0]) > w - 2 and size > FONT_FLOOR:
        size -= 1
        font = load_font(font_path, size)
        bbox = font.getbbox(text)
    if bbox and (bbox[2] - bbox[0]) > w - 2:
        raise ValueError(f"'{text}' does not fit {w}px even at "
                         f"{FONT_FLOOR}px -- shorten the label")
    img = Image.new("L", (w, h), 0)
    if bbox:
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        ox = max(0, (w - tw) // 2) - bbox[0]
        oy = max(0, (h - th) // 2) - bbox[1]
        ImageDraw.Draw(img).text((ox, oy), text, fill=255, font=font)
    return [ramp_map(v, ramp) for v in img.getdata()], size


# ── Region + job tables ────────────────────────────────────────────────
class Region:
    def __init__(self, name, pixel_off, tex_w, tex_h, bg_index, ramp,
                 font_path, clut_off):
        self.name = name
        self.pixel_off = pixel_off
        self.tex_w, self.tex_h = tex_w, tex_h
        self.dbw_ct32 = tex_w // 2
        self.bg_index = bg_index
        self.ramp = ramp
        self.font_path = font_path
        self.clut_off = clut_off
        self.pixel_size = tex_w * tex_h // 2

    def deswizzle(self, data):
        blob = bytes(data[self.pixel_off:self.pixel_off + self.pixel_size])
        lin = bytearray(deswizzle_psmt4(blob, self.tex_w, self.tex_h,
                                        bw_psmt4=self.tex_w,
                                        dbw_ct32=self.dbw_ct32))
        rt = bytes(swizzle_psmt4(lin, self.tex_w, self.tex_h,
                                 bw_psmt4=self.tex_w,
                                 dbw_ct32=self.dbw_ct32))
        if rt != blob:
            raise ValueError(f"{self.name}: swizzle round-trip FAILED")
        return lin

    def reswizzle_into(self, data, lin):
        out = bytearray(data)
        out[self.pixel_off:self.pixel_off + self.pixel_size] = swizzle_psmt4(
            lin, self.tex_w, self.tex_h, bw_psmt4=self.tex_w,
            dbw_ct32=self.dbw_ct32)
        return bytes(out)


# Labels: (x, y, w, h, text, start_size)  -- boxes are the measured JP ink
# bounding boxes (inclusive extents converted to w/h), i.e. guaranteed to
# lie inside whatever external UV cell samples them.
# Clears:  (x, y, w, h)  -- split-cell leading glyphs blanked entirely.

# s6 banner sheet, 256x256, bg=15 (canon citation per band in the tuple tail)
S6_LABELS = [
    #  x    y    w   h   text                 size  JP band          canon
    (5,   3, 136, 28, "Library",            22),  # raiburarii    (header)
    (146, 3, 109, 28, "Bestiary", 22),  # mamono zukan (v165: was Monster Compendium at an 11px squeeze; Bestiary fills the 109px band at full height; no shipped string binds the term)
    (1,  34, 118, 29, "Allied Actions",     22),  # senjutsu zkn  (AA canon)
    (146, 34, 109, 29, "Person Register",   22),  # jinbutsu mkn  (chunk fix)
    (5,  66, 143, 29, "Adventurer's Guide", 22),  # bouken tebiki (batch_03)
    (1,  98, 114, 29, "Book List",          22),  # shomotsu list (chunk fix)
    (3, 130, 114, 30, "Glossary",           22),  # yougo jiten   (chunk fix)
    (131, 130, 118, 30, "Simzon's Journal", 22),  # muzon no shuki (names json)
    (1, 166, 157, 24, "Item Compendium",    20),  # item zukan    (chunk fix)
    (1, 195, 140, 27, "Request File",       22),  # irai file     (names json)
    (149, 195, 104, 27, "Info File",        22),  # hou file      (names json)
    (2, 226, 156, 28, "The Karman Report",  22),  # karman no shinjitsu (nj)
]
S6_CLEARS = [
    (132,  98, 24, 29),   # "shi" of SHImuzon no shuki (split-cell lead)
    (196, 226, 28, 28),   # "jou" of JOUhou file       (split-cell lead)
]

# d17 sub-tabs, 128x128, bg=15.  Row 2 (full-width "123") stays PRISTINE.
D17_LABELS = [
    (1,   0,  62, 32, "Info",      20),   # jouhou
    (65,  0,  62, 32, "Details",   20),   # kaisetsu
    (3,  64, 120, 32, "Abilities", 22),   # tokushu nouryoku
    (3,  97, 117, 31, "Art",       22),   # irasuto
]

# d19, 64x64, bg=15.  Keep ":" (x5-8,y4-13) and the green triangle
# (x48-63,y49-62).  JP text is two lines (hyouji / hi-hyouji) -> mirror it.
D19_CLEARS = [(3, 16, 57, 32)]
D19_LABELS = [
    (3, 16, 57, 15, "Show",  13),
    (3, 31, 57, 17, "/Hide", 13),
]

# d21, 64x64, bg=0 (INVERTED).  Keep ":" (x5-8,y6-13), "R2"+arrows row
# (y16-31) and "+" (y32-47).  JP "hayaokuri" occupies x16-63, y0-15.
D21_LABELS = [(16, 0, 48, 16, "Fast-fwd", 11)]


# ── pixel helpers ──
def blit(lin, W, x, y, w, h, cell):
    for dy in range(h):
        row = (y + dy) * W
        cell_row = dy * w
        for dx in range(w):
            lin[row + x + dx] = cell[cell_row + dx]


def clear(lin, W, x, y, w, h, bg):
    for dy in range(h):
        row = (y + dy) * W + x
        lin[row:row + w] = bytes([bg]) * w


def save_previews(lin, region, data, tag):
    """Grayscale (ink-normalized) + CLUT-color previews, 2x NEAREST."""
    W, H = region.tex_w, region.tex_h
    g = Image.new("L", (W, H))
    if region.bg_index == 15:
        g.putdata([min(255, (15 - p) * 17) for p in lin])
    else:
        g.putdata([min(255, p * 17) for p in lin])
    g.resize((W * 2, H * 2), Image.NEAREST).save(
        os.path.join(DEBUG_DIR, f"{region.name}_{tag}_gray.png"))

    clut = data[region.clut_off:region.clut_off + 64]
    pal = [struct.unpack_from("<4B", clut, i * 4) for i in range(16)]
    c = Image.new("RGBA", (W, H))
    c.putdata([(pal[p][0], pal[p][1], pal[p][2],
                min(255, pal[p][3] * 2)) for p in lin])
    bgimg = Image.new("RGBA", (W, H), (72, 48, 24, 255))  # brown UI board
    bgimg.alpha_composite(c)
    bgimg.resize((W * 2, H * 2), Image.NEAREST).convert("RGB").save(
        os.path.join(DEBUG_DIR, f"{region.name}_{tag}_color.png"))


# ═══════════════════════════════ main ═══════════════════════════════
def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(DEBUG_DIR, exist_ok=True)

    banner_font = resolve_font_path(BANNER_FONT_CANDS, "banner serif")
    tile_font = resolve_font_path(TILE_FONT_CANDS, "tile sans")
    print(f"fonts: banner={os.path.basename(banner_font)} "
          f"tiles={os.path.basename(tile_font)}")

    data = open(IN_PATH, "rb").read()

    # ── Gate 1: pristine-input structural signature ──
    assert len(data) == RES_SIZE, \
        f"input size {len(data)} != {RES_SIZE} -- not pristine R2655"
    secs = parse_section_table(data)
    got = [(s["id"], s["offset"], s["size"]) for s in secs]
    assert got == EXPECT_SECTIONS, f"section table mismatch: {got}"
    assert find_pixel_base(data, S4_OFF, S4_SIZE) == S4_PIXEL_BASE
    assert find_pixel_base(data, S6_OFF, S6_SIZE) == S6_PIXEL_BASE
    descs = parse_upload_descriptors(data, S4_OFF, S4_SIZE)
    assert len(descs) == 23, f"s4 descriptor count {len(descs)} != 23"
    assert (descs[17]["w"], descs[17]["h"]) == (64, 32)   # d17 128x128 PSMT4
    assert (descs[19]["w"], descs[19]["h"]) == (32, 16)   # d19  64x64
    assert (descs[21]["w"], descs[21]["h"]) == (32, 16)   # d21  64x64
    print("pristine gate: size + section table + pixel bases OK")

    regions = {
        "s6":  Region("s6",  S6_PIXEL_BASE, 256, 256, 15, RAMP_S6,
                      banner_font, 0x30830),
        "d17": Region("d17", 0x25240, 128, 128, 15, RAMP_D17,
                      tile_font, 0x27240),
        "d19": Region("d19", 0x27280, 64, 64, 15, RAMP_D19,
                      tile_font, 0x27A80),
        "d21": Region("d21", 0x27AC0, 64, 64, 0, RAMP_D21,
                      tile_font, 0x282C0),
    }
    jobs = {
        "s6":  (S6_LABELS, S6_CLEARS),
        "d17": (D17_LABELS, []),
        "d19": (D19_LABELS, D19_CLEARS),
        "d21": (D21_LABELS, []),
    }

    # ── Gate 1b: JP ink actually present in every band (double-patch trap) ──
    pristine_lin = {}
    for name, r in regions.items():
        lin = r.deswizzle(data)
        pristine_lin[name] = bytes(lin)
        labels, clears = jobs[name]
        for (x, y, w, h, *_ ) in list(labels) + [c + ("",) for c in clears]:
            ink = sum(1 for dy in range(h) for dx in range(w)
                      if lin[(y + dy) * r.tex_w + x + dx] != r.bg_index)
            assert ink > 8, (f"{name} box ({x},{y},{w},{h}) has no JP ink "
                             f"({ink}px) -- input already patched?")
    print("pristine gate: JP ink present in all "
          f"{sum(len(j[0]) + len(j[1]) for j in jobs.values())} boxes")

    # ── Re-ink ──
    patched = data
    shrunk = []
    for name, r in regions.items():
        labels, clears = jobs[name]
        lin = bytearray(pristine_lin[name])
        for (x, y, w, h) in clears:
            clear(lin, r.tex_w, x, y, w, h, r.bg_index)
            print(f"  {name} [{x:3},{y:3} {w}x{h}] CLEARED (split-cell lead)")
        for (x, y, w, h, text, size) in labels:
            clear(lin, r.tex_w, x, y, w, h, r.bg_index)
            cell, used = render_cell(text, w, h, r.font_path, size, r.ramp)
            blit(lin, r.tex_w, x, y, w, h, cell)
            note = f" (shrunk {size}->{used})" if used < size else ""
            if used < size:
                shrunk.append(f"{name} '{text}' {size}->{used}px")
            print(f"  {name} [{x:3},{y:3} {w}x{h}] '{text}' @{used}px{note}")
        patched = r.reswizzle_into(patched, lin)

    # ── Gate 2: byte containment (only the four pixel blobs changed) ──
    assert_outside_window_pristine(
        data, patched,
        [(r.pixel_off, r.pixel_off + r.pixel_size) for r in regions.values()])
    print("containment gate A: bytes outside the 4 pixel blobs pristine")

    # ── Gate 3: pixel containment (diffs only inside declared boxes) ──
    for name, r in regions.items():
        labels, clears = jobs[name]
        boxes = [(x, y, w, h) for (x, y, w, h, *_ ) in labels] + clears
        new_lin = r.deswizzle(patched)
        old_lin = pristine_lin[name]
        bad = []
        for i, (a, b) in enumerate(zip(old_lin, new_lin)):
            if a == b:
                continue
            x, y = i % r.tex_w, i // r.tex_w
            if not any(bx <= x < bx + bw and by <= y < by + bh
                       for (bx, by, bw, bh) in boxes):
                bad.append((x, y))
        assert not bad, f"{name}: {len(bad)} pixels modified OUTSIDE " \
                        f"declared boxes, first at {bad[:5]}"
    print("containment gate B: all pixel diffs inside declared band boxes")

    # ── Previews ──
    for name, r in regions.items():
        save_previews(pristine_lin[name], r, data, "before")
        save_previews(r.deswizzle(patched), r, patched, "after")
    print(f"previews written to {DEBUG_DIR}")

    # ── Gate 4: output handling (idempotence) ──
    if os.path.exists(OUT_PATH):
        existing = open(OUT_PATH, "rb").read()
        if existing == patched:
            print("output already identical (idempotent re-run) -- OK")
        elif existing == data:
            print("output was a pristine build copy -- overwriting")
        else:
            print(f"FATAL: {OUT_PATH} exists and is neither pristine nor "
                  "this patcher's own output -- another patcher touched "
                  "R2655?  Refusing to overwrite.")
            sys.exit(1)
    with open(OUT_PATH, "wb") as f:
        f.write(patched)
    diff = sum(1 for a, b in zip(data, patched) if a != b)
    print(f"wrote {OUT_PATH} ({len(patched)} B, {diff} bytes differ)")
    if shrunk:
        print("bands shrunk below start size: " + "; ".join(shrunk))
    print("R2655 library strips: ALL GATES PASS")


if __name__ == "__main__":
    main()
