#!/usr/bin/env python3
"""strip_patcher — reusable in-place pixel re-rendering for pre-rendered
kanji UI strips inside PACKDATA resources (promoted from the verified v86
prototype build/recon_v86/render-toolchain/strip_patcher.py).

Format model (VERIFIED for R2124@736, R1365@1920, R1054@1312 and the whole
"strip family" R1053/R1054/R1358-R1367/R1910; same family as R2100/R2138 in
tools/patch_r2100.py / tools/patch_r2138.py):
  - The resource stores the texture pixel blob as PSMCT32-upload host data
    ("CT32 raster", dbw_ct32 = tex_w/2 for 256-wide PSMT4 textures).
  - The game uploads it with DBP == TBP0 (block-aligned), so the standard
    VRAM-simulation deswizzle/swizzle in tools/psmt4_deswizzle.py round-trips
    the bytes exactly.
  - Byte size is always preserved: only the pixel blob region is rewritten.

Strip-family container layout (byte-verified, see
build/recon_v86/strip-family-offsets/manifest.json):
  - Section table at file offset 0: 16-byte LE entries (u32 id, u32 size,
    u32 offset, u32 pad). See parse_section_table().
  - Section 0 = GIF upload section: 16B sub-header (u32 A, u32 B, pad, pad),
    A x 0x50-byte GIF A+D packets at +16, A x 20-byte records, then B x
    16-byte LE upload descriptors (u32 pad0, u32 vram_addr, u16 w | u16 h,
    u32 bw). The pixel+CLUT data block ends FLUSH at the section end:
        data_start = section_end - sum(w*h*4 over all descriptors)
    and uploads consume the data sequentially in descriptor order (pixel
    blob first, then 64-byte CLUTs). See find_pixel_base().
  - A later section holds the UV rect table: 8-byte BIG-ENDIAN header
    (u32 5, u32 count) followed by count x 20-byte BE entries
    (u32 x, y, w, h, clut_idx). See parse_rect_table(). Known tables:
    R1054/R1359/R1360/R1361/R1362 @34656, R1363 @38560, R1364 @35456 and
    @71168, R1365/R1366 @35712, R1367 @35632, R1910 @35312.

!!! CRITICAL VALIDATION WARNING !!!
swizzle_psmt4(deswizzle_psmt4(x)) == x is an IDENTITY for ANY byte offset —
the round-trip gate in patch_strip/patch_strip_rects only proves the
swizzle parameters are self-consistent, it does NOT prove the pixel base
offset is correct. A wrong pixel_off round-trips just as cleanly and then
corrupts adjacent data when patched. Callers MUST visually confirm the
decode PNG first (clean kanji glyphs, rect-table boxes aligned with the
artwork) before patching — use the CLI:
    python tools/strip_patcher.py --decode <raw> --off N \
        [--w 256 --h 256 --dbw 128] --out out.png
or trust only offsets derived from find_pixel_base() on a byte-verified
section, never from round-trip success alone.

API:
    region = StripRegion(pixel_off=1312, tex_w=256, tex_h=256,
                         dbw_ct32=128, bg_index=0, ink_index=15)
    patched = patch_strip(resource_bytes, region, labels,
                          preview_prefix="out/r1054")
    # labels: list of (x, y, w, h, text [, fontsize_int | "left"]) tuples

    rects = parse_rect_table(resource_bytes, 34656)
    patched = patch_strip_rects(resource_bytes, region,
                                [(rects[4], "Attack"), (rects[5], "Defend")])

    base = find_pixel_base(resource_bytes, section_off, section_size)
    assert_outside_window_pristine(orig, patched, [(base, base + 32768)])
"""
import os
import struct
import sys
from collections import Counter
from dataclasses import dataclass

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "tools"))
from psmt4_deswizzle import deswizzle_psmt4, swizzle_psmt4  # noqa: E402

from PIL import Image, ImageFont, ImageDraw  # noqa: E402


# ───────────────────────── region descriptor ─────────────────────────

@dataclass
class StripRegion:
    pixel_off: int            # byte offset of swizzled pixel blob in resource
    tex_w: int = 256
    tex_h: int = 256
    bw_psmt4: int = None      # default: tex_w
    dbw_ct32: int = None      # default: tex_w // 2  (family convention)
    bg_index: int = 0         # palette index of transparent background
    ink_index: int = 15       # palette index of full-opacity ink
    font_size: int = 13       # default label font size
    name: str = "strip"

    def __post_init__(self):
        if self.bw_psmt4 is None:
            self.bw_psmt4 = self.tex_w
        if self.dbw_ct32 is None:
            self.dbw_ct32 = self.tex_w // 2

    @property
    def pixel_size(self):
        return self.tex_w * self.tex_h // 2


# ───────────────────────── container parsing ─────────────────────────

def parse_section_table(data):
    """Parse the strip-family section table at offset 0.

    Format: consecutive 16-byte LE entries (u32 id, u32 size, u32 offset,
    u32 pad). Entry ids count up from 0; the table ends when the id stops
    being sequential or the offset/size stop being plausible.

    Returns: list of dict(id, size, offset).
    """
    sections = []
    pos = 0
    expect_id = 0
    while pos + 16 <= len(data):
        sid, size, off, _pad = struct.unpack_from("<4I", data, pos)
        if sid != expect_id or off >= len(data) or size == 0 \
                or off + size > len(data):
            break
        sections.append({"id": sid, "size": size, "offset": off})
        pos += 16
        expect_id += 1
        if off <= pos:  # first section begins; table cannot continue past it
            break
    return sections


def parse_rect_table(data, off):
    """Parse a UV rect table at byte offset `off`.

    Format (byte-verified, manifest.json): 8-byte BIG-ENDIAN header
    (u32 magic == 5, u32 count) followed by count x 20-byte BE entries
    (u32 x, u32 y, u32 w, u32 h, u32 clut_idx).

    Returns: list of dict(x, y, w, h, clut), in table order.
    """
    magic, count = struct.unpack_from(">2I", data, off)
    if magic != 5:
        raise ValueError(f"rect table @0x{off:X}: bad magic {magic} (expect 5)")
    end = off + 8 + count * 20
    if end > len(data):
        raise ValueError(f"rect table @0x{off:X}: {count} entries overrun "
                         f"resource (need {end}, have {len(data)})")
    rects = []
    for i in range(count):
        x, y, w, h, clut = struct.unpack_from(">5I", data, off + 8 + i * 20)
        rects.append({"x": x, "y": y, "w": w, "h": h, "clut": clut})
    return rects


def parse_upload_descriptors(data, section_off, section_size):
    """Parse the section-0 GIF upload layout.

    Layout: 16B sub-header (u32 A, u32 B), A x 0x50-byte GIF A+D packets at
    +16, A x 20-byte records, then B x 16-byte LE upload descriptors
    (u32 pad0, u32 vram_addr, u16 w | u16 h, u32 bw).

    Returns: list of dict(vram_addr, w, h, bw, bytes) in upload order.
    """
    a, b = struct.unpack_from("<2I", data, section_off)
    desc_off = section_off + 16 + a * 0x50 + a * 20
    if desc_off + b * 16 > section_off + section_size:
        raise ValueError(f"section @0x{section_off:X}: descriptor run "
                         f"(A={a}, B={b}) overruns section")
    descs = []
    for i in range(b):
        pad0, vram, wh, bw = struct.unpack_from("<4I", data, desc_off + i * 16)
        w, h = wh & 0xFFFF, (wh >> 16) & 0xFFFF
        descs.append({"vram_addr": vram, "w": w, "h": h, "bw": bw,
                      "bytes": w * h * 4})
    return descs


def find_pixel_base(data, section_off, section_size):
    """Locate the pixel blob inside a strip-family GIF upload section.

    VERIFIED flush-to-end rule (manifest.json "pixel_base_rule"): the
    pixel+CLUT data block ends flush at the section end, so
        data_start = section_end - sum(w*h*4 over all upload descriptors)
    and uploads consume the data sequentially in descriptor order (pixel
    blob first, then the 64-byte CLUTs). The returned offset is therefore
    the pixel base. Reproduces ALL byte-verified bases:
    R1054/R1359/R1360/R1361/R1362=1312, R1363=3808, R1364=1920 & 37888,
    R1365/R1366=1920, R1367=1904, R1910=1840, R1358=736.

    Do NOT use marker+8 / sub0+0x4C0 / 0x1460 heuristics, and do NOT trust
    a base just because the swizzle round-trip passes (it always does).
    """
    descs = parse_upload_descriptors(data, section_off, section_size)
    total = sum(d["bytes"] for d in descs)
    base = section_off + section_size - total
    if base < section_off:
        raise ValueError(f"section @0x{section_off:X}: descriptor data "
                         f"({total}B) larger than section ({section_size}B)")
    return base


# ───────────────────────── font handling ─────────────────────────

_font_cache = {}

def load_font(size, bold=True):
    key = (size, bold)
    if key not in _font_cache:
        cands = (["C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/arial.ttf"]
                 if bold else ["C:/Windows/Fonts/arial.ttf"])
        font = None
        for fp in cands:
            if os.path.exists(fp):
                font = ImageFont.truetype(fp, size)
                break
        if font is None:
            font = ImageFont.load_default()
        _font_cache[key] = font
    return _font_cache[key]


def text_width(text, size):
    f = load_font(size)
    bbox = f.getbbox(text)
    return (bbox[2] - bbox[0]) if bbox else 0


def fit_font(text, max_w, start_size=13, floor=9):
    """Largest font size <= start_size whose rendering of `text` fits max_w.

    Raises ValueError if the text is still too wide at the floor size.
    """
    size = start_size
    while text_width(text, size) > max_w and size > floor:
        size -= 1
    if text_width(text, size) > max_w:
        raise ValueError(f"text '{text}' does not fit {max_w}px even at "
                         f"{floor}px font — shorten the label")
    return size


# ───────────────────────── label rendering ─────────────────────────

def render_label(text, width, height, font, bg_index, ink_index, align="center"):
    """Render anti-aliased text into a w*h cell of palette indices.

    Grayscale 0..255 is mapped linearly onto the bg→ink index ramp, which is
    correct for the grayscale-ramp CLUTs these UI strips use (ink at high
    index for R2124/R1365; pass ink_index < bg_index for inverted atlases).
    """
    if not text:
        return [bg_index] * (width * height)

    cur = font
    bbox = cur.getbbox(text)
    while bbox and (bbox[2] - bbox[0]) > width - 2 and cur.size > 7:
        cur = load_font(cur.size - 1)
        bbox = cur.getbbox(text)

    # Overflow tripwire (menu-overflow hardening): never silently clip. If the
    # text is still wider than the cell even at the min font, abort the build
    # rather than ship a truncated label.
    if bbox and (bbox[2] - bbox[0]) > width:
        raise ValueError(
            "menu label %r overflows its %dpx cell (%dpx even at min font) "
            "-- shorten the label" % (text, width, bbox[2] - bbox[0]))

    img = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(img)
    if bbox:
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        ox = (1 - bbox[0]) if align == "left" else max(0, (width - tw) // 2) - bbox[0]
        oy = max(0, (height - th) // 2) - bbox[1]
        draw.text((ox, oy), text, fill=255, font=cur)

    out = []
    span = ink_index - bg_index  # may be negative (inverted convention)
    for v in img.getdata():
        out.append(bg_index + (v * span + 127) // 255 if span > 0
                   else bg_index + (v * span - 127) // 255)
    return out


def blit(linear, tex_w, x, y, w, h, cell):
    tex_h = len(linear) // tex_w
    for dy in range(h):
        for dx in range(w):
            px, py = x + dx, y + dy
            if 0 <= px < tex_w and 0 <= py < tex_h:
                linear[py * tex_w + px] = cell[dy * w + dx]


def clear(linear, tex_w, x, y, w, h, bg):
    blit(linear, tex_w, x, y, w, h, [bg] * (w * h))


def sample_rect_indices(linear, tex_w, x, y, w, h, bg_index):
    """Sample the ink index from the original glyph pixels inside a rect.

    Returns (ink_index, Counter of non-bg indices). Empirically (R1054,
    R1365) the family CLUTs are a monotonic alpha ramp (entry byte 1 rises
    0..127 with index) but each pre-rendered glyph carries a wide 1-index
    halo, so the MOST COMMON non-bg index is the faint halo, not the ink.
    The ink is therefore taken as the weighted 95th-percentile index of the
    non-bg histogram, ordered by distance from bg_index (handles both
    bg=0/ink-high and inverted bg=15/ink-low atlases). Falls back to 15
    (or 0 for inverted) if the rect has no glyph pixels.
    """
    hist = Counter()
    tex_h = len(linear) // tex_w
    for dy in range(h):
        for dx in range(w):
            px, py = x + dx, y + dy
            if 0 <= px < tex_w and 0 <= py < tex_h:
                v = linear[py * tex_w + px]
                if v != bg_index:
                    hist[v] += 1
    if not hist:
        return (15 if bg_index < 8 else 0), hist
    order = sorted(hist, key=lambda i: abs(i - bg_index))
    total = sum(hist.values())
    cum = 0
    ink = order[-1]
    for idx in order:
        cum += hist[idx]
        if cum >= 0.95 * total:
            ink = idx
            break
    return ink, hist


def save_preview(linear, tex_w, tex_h, path, bg, ink):
    img = Image.new("L", (tex_w, tex_h))
    if ink > bg:
        img.putdata([min(255, p * 17) for p in linear])
    else:
        img.putdata([min(255, (15 - p) * 17) for p in linear])
    img.save(path)


# ───────────────────────── swizzle plumbing ─────────────────────────

def _deswizzle_gated(resource_bytes, r):
    """Deswizzle region pixels and verify the swizzle round-trip.

    NOTE: this gate only validates the swizzle PARAMETERS, not pixel_off —
    see the module docstring. Callers must have visually confirmed the
    decode at this offset.
    """
    blob = bytes(resource_bytes[r.pixel_off:r.pixel_off + r.pixel_size])
    if len(blob) != r.pixel_size:
        raise ValueError("pixel blob extends past end of resource")
    linear = bytearray(deswizzle_psmt4(blob, r.tex_w, r.tex_h,
                                       bw_psmt4=r.bw_psmt4, dbw_ct32=r.dbw_ct32))
    if bytes(swizzle_psmt4(linear, r.tex_w, r.tex_h,
                           bw_psmt4=r.bw_psmt4, dbw_ct32=r.dbw_ct32)) != blob:
        raise ValueError(f"{r.name}: deswizzle round-trip FAILED — "
                         "wrong tex_w/tex_h/dbw_ct32/pixel_off")
    return linear


def _reswizzle_into(resource_bytes, r, linear):
    """Swizzle `linear` back into a copy of the resource; assert integrity."""
    res = bytearray(resource_bytes)
    res[r.pixel_off:r.pixel_off + r.pixel_size] = swizzle_psmt4(
        linear, r.tex_w, r.tex_h, bw_psmt4=r.bw_psmt4, dbw_ct32=r.dbw_ct32)
    # Integrity: same length, nothing outside the blob changed.
    assert len(res) == len(resource_bytes)
    assert res[:r.pixel_off] == resource_bytes[:r.pixel_off]
    assert res[r.pixel_off + r.pixel_size:] == \
        resource_bytes[r.pixel_off + r.pixel_size:]
    return bytes(res)


# ───────────────────────── main entry points ─────────────────────────

def patch_strip(resource_bytes, region, labels, clear_only=(),
                preview_prefix=None, verbose=True):
    """Render English labels in place into a pre-rendered strip.

    resource_bytes : full resource (bytes); returned copy has same length.
    region         : StripRegion
    labels         : iterable of (x, y, w, h, text [, fontsize | "left"])
    clear_only     : iterable of (x, y, w, h) zones to blank
    preview_prefix : if set, writes {prefix}_before.png / {prefix}_after.png
    Returns: patched bytes (identical length, only pixel blob modified).
    """
    r = region
    linear = _deswizzle_gated(resource_bytes, r)
    if verbose:
        print(f"  {r.name}: round-trip PASS "
              f"({r.tex_w}x{r.tex_h} dbw={r.dbw_ct32} @0x{r.pixel_off:X})")

    if preview_prefix:
        save_preview(linear, r.tex_w, r.tex_h, preview_prefix + "_before.png",
                     r.bg_index, r.ink_index)

    for (x, y, w, h) in clear_only:
        clear(linear, r.tex_w, x, y, w, h, r.bg_index)

    for entry in labels:
        x, y, w, h, text = entry[:5]
        size, align = r.font_size, "center"
        for extra in entry[5:]:
            if isinstance(extra, int):
                size = extra
            elif isinstance(extra, str):
                align = extra
        clear(linear, r.tex_w, x, y, w, h, r.bg_index)
        if text:
            cell = render_label(text, w, h, load_font(size),
                                r.bg_index, r.ink_index, align)
            blit(linear, r.tex_w, x, y, w, h, cell)
        if verbose:
            print(f"    [{x:3},{y:3} {w}x{h}] '{text}'")

    if preview_prefix:
        save_preview(linear, r.tex_w, r.tex_h, preview_prefix + "_after.png",
                     r.bg_index, r.ink_index)

    return _reswizzle_into(resource_bytes, r, linear)


def patch_strip_rects(resource_bytes, region, rect_labels,
                      preview_prefix=None, verbose=True):
    """Like patch_strip, but driven by parse_rect_table() rects.

    rect_labels : iterable of (rect_dict, english_text) pairs, where
                  rect_dict has keys x, y, w, h (as from parse_rect_table).
    For each rect the original glyph pixels are sampled (histogram of
    non-background indices) to find the actual ink index — these strips do
    NOT all use ink=15 — then the rect is cleared to region.bg_index and
    the English text is rendered centered with AA mapped onto the bg→ink
    ramp. The font auto-shrinks from region.font_size until the text fits
    rect width minus 4px (floor 9px); raises ValueError if still too wide.

    Returns: patched bytes (identical length, only pixel blob modified).
    """
    r = region
    linear = _deswizzle_gated(resource_bytes, r)
    if verbose:
        print(f"  {r.name}: round-trip PASS "
              f"({r.tex_w}x{r.tex_h} dbw={r.dbw_ct32} @0x{r.pixel_off:X})")

    if preview_prefix:
        save_preview(linear, r.tex_w, r.tex_h, preview_prefix + "_before.png",
                     r.bg_index, r.ink_index)

    for rect, text in rect_labels:
        x, y, w, h = rect["x"], rect["y"], rect["w"], rect["h"]
        ink, hist = sample_rect_indices(linear, r.tex_w, x, y, w, h,
                                        r.bg_index)
        clear(linear, r.tex_w, x, y, w, h, r.bg_index)
        if text:
            size = fit_font(text, w - 4, start_size=r.font_size, floor=9)
            cell = render_label(text, w, h, load_font(size),
                                r.bg_index, ink, "center")
            blit(linear, r.tex_w, x, y, w, h, cell)
        if verbose:
            print(f"    [{x:3},{y:3} {w}x{h}] ink={ink} "
                  f"({sum(hist.values())} px sampled) '{text}'")

    if preview_prefix:
        save_preview(linear, r.tex_w, r.tex_h, preview_prefix + "_after.png",
                     r.bg_index, r.ink_index)

    return _reswizzle_into(resource_bytes, r, linear)


def assert_outside_window_pristine(orig, patched, windows):
    """Assert patched differs from orig ONLY inside [start, end) windows.

    orig / patched : bytes-like, must be equal length.
    windows        : iterable of (start, end) byte ranges allowed to differ.
    Raises AssertionError on length mismatch or any out-of-window change.
    """
    assert len(orig) == len(patched), \
        f"length changed: {len(orig)} -> {len(patched)}"
    spans = sorted((int(s), int(e)) for s, e in windows)
    pos = 0
    for s, e in spans:
        assert orig[pos:s] == patched[pos:s], (
            f"bytes modified outside windows in [{pos}, {s}) — first diff at "
            f"{pos + next(i for i, (a, b) in enumerate(zip(orig[pos:s], patched[pos:s])) if a != b)}")
        pos = max(pos, e)
    assert orig[pos:] == patched[pos:], (
        f"bytes modified outside windows in [{pos}, {len(orig)}) — first diff at "
        f"{pos + next(i for i, (a, b) in enumerate(zip(orig[pos:], patched[pos:])) if a != b)}")


# ───────────────────────── CLI ─────────────────────────

def _cli():
    import argparse
    ap = argparse.ArgumentParser(
        description="Decode a strip-family PSMT4 pixel blob to a grayscale "
                    "PNG for visual confirmation (idx*17). ALWAYS inspect "
                    "this before patching — round-trip success does NOT "
                    "validate the offset.")
    ap.add_argument("--decode", required=True, metavar="RAW",
                    help="path to the raw resource file")
    ap.add_argument("--off", required=True, type=lambda s: int(s, 0),
                    help="pixel blob byte offset (decimal or 0x hex)")
    ap.add_argument("--w", type=int, default=256, help="texture width")
    ap.add_argument("--h", type=int, default=256, help="texture height")
    ap.add_argument("--dbw", type=int, default=128,
                    help="PSMCT32 upload buffer width (family default 128)")
    ap.add_argument("--out", required=True, help="output PNG path")
    args = ap.parse_args()

    data = open(args.decode, "rb").read()
    region = StripRegion(pixel_off=args.off, tex_w=args.w, tex_h=args.h,
                         dbw_ct32=args.dbw,
                         name=os.path.basename(args.decode))
    linear = _deswizzle_gated(data, region)
    out_dir = os.path.dirname(os.path.abspath(args.out))
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    save_preview(linear, args.w, args.h, args.out, bg=0, ink=15)
    print(f"decoded {args.decode} @0x{args.off:X} "
          f"({args.w}x{args.h} dbw={args.dbw}) -> {args.out}")
    print("round-trip PASS (parameters self-consistent; offset still needs "
          "VISUAL confirmation)")


if __name__ == "__main__":
    _cli()
