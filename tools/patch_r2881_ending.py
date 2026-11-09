#!/usr/bin/env python3
"""patch_r2881_ending.py — R2881 sub7: pre-rendered ENDING narration pages.

v204 rewrite (RUN-20261109-1725). Replaces the v94 band/window model, which
was wrong in three ways (all CONFIRMED by recon, see the run's subagent dir):

1. LAYOUT. The cinematic does not sample fixed 2-column windows. It draws one
   sprite per text line from the R2881 sub6 SPRITE TABLE (sub6 @FILE 1967856,
   header <4H4I> counts/offsets, 123 x 28-byte records @+0x17a4:
   <HHhhHHHH> texset, nclut, x, y, u, v, w, h). Each line rect is drawn
   screen-centred (x = -w/2). Our old inferred windows put ~10-13% of the EN
   ink outside every rect, so it never rendered.
2. PALETTE. img0/img1 do NOT use an "inverted ramp". img0 (CLUT @2109680) is
   dark ink 0-4 + light rim 5-9 + white glow 10-14; img1 (CLUT @2240816, plus
   red/cyan variants) is a white core 0-4 + 1px dark outline 5 + dark glow
   10-14. Plain AA through 15..0 rendered as a washed-out grey ghost.
3. COVERAGE. A third text page, img10 (256x256 @2254384, CLUTs @2287152..,
   single-colour alpha ramp = the old quantizer is right there), holds the
   climactic / reprise lines and shipped in Japanese.

Text lives in data/strip_labels/r2881_ending_rects.json, one entry per unique
line rect (page, u, v, w), translated in DISPLAY order (sprite index). The
16px punctuation sprites (、。) are blanked; English carries its own.

Safety:
  * the sprite table is parsed from the pristine resource and every JSON rect
    must exist in it (and every text rect in it must be covered);
  * pristine JP ink outside the rect union must be ~0 (proves the page is
    text-only, so clearing it is safe);
  * each line's ink + glow must fit its rect (or `clip` span) — hard fail;
  * swizzle round-trips are asserted; only the three pixel payloads change.

Usage:
    python tools/patch_r2881_ending.py
Writes build/packdata_resources/2881_type15.raw and true-colour previews under
build/recon_v86/r2881-out/. Exits nonzero on any failure.
"""
import json
import os
import struct
import sys

import numpy as np

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "tools"))
from psmt4_deswizzle import deswizzle_psmt4, swizzle_psmt4  # noqa: E402
from strip_patcher import (assert_outside_window_pristine,  # noqa: E402
                           load_font)

from PIL import Image, ImageDraw  # noqa: E402

SRC = os.path.join(BASE, "extracted", "packdata_raw", "2881_type15.raw")
OUT = os.path.join(BASE, "build", "packdata_resources", "2881_type15.raw")
OUT_DIR = os.path.join(BASE, "build", "recon_v86", "r2881-out")
LABELS = os.path.join(BASE, "data", "strip_labels", "r2881_ending_rects.json")

SUB6_OFF = 1967856
BG = 15
LINE_H = 24
MAX_STRAY_JP_INK = 64      # pristine ink allowed outside the rect union

# page -> geometry, sprite texsets, CLUT offsets (preview only), style, margin
PAGES = {
    "img0": dict(off=1978608, size=512, bw=512, dbw=256, texsets={0},
                 cluts=[2109680], style="dark_core_white_glow", margin=4),
    "img1": dict(off=2109744, size=512, bw=512, dbw=256, texsets={1, 2, 3},
                 cluts=[2240816, 2240880, 2240944],
                 style="white_core_dark_outline", margin=5,
                 # JP-only orphan lines the game never samples from img1
                 # (it draws them from img10): x0, y0, x1, y1
                 dead=[(272, 72, 512, 144), (300, 456, 512, 488),
                       (312, 488, 512, 512)]),
    "img10": dict(off=2254384, size=256, bw=256, dbw=128,
                  texsets={6, 7, 8, 9}, cluts=[2287152, 2287216, 2287280],
                  style="plain_ramp", margin=2),
}


def parse_sprites(raw):
    n0, n1, n2, n3, o0, o1, o2, o3 = struct.unpack_from("<4H4I", raw, SUB6_OFF)
    assert (n3, o3) == (123, 0x17A4), f"sub6 header changed: {n3} @{o3:#x}"
    recs = []
    for i in range(n3):
        t, nc, x, y, u, v, w, h = struct.unpack_from(
            "<HHhhHHHH", raw, SUB6_OFF + o3 + 28 * i)
        recs.append(dict(i=i, texset=t, nclut=nc, x=x, y=y, u=u, v=v, w=w,
                         h=h))
    assert recs[0] == dict(i=0, texset=0, nclut=1, x=-92, y=-12, u=0, v=0,
                           w=184, h=24), "sprite table layout mismatch"
    return recs


# ── quantizers: coverage c in [0,1], distance d (px) to nearest c>=0.3 ──
def _dist_to_core(cov, radius=5):
    core = cov >= 0.3
    h, w = core.shape
    d = np.full((h, w), 99.0)
    pad = np.pad(core, radius)
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            dist = (dx * dx + dy * dy) ** 0.5
            if dist > radius:
                continue
            shifted = pad[radius + dy:radius + dy + h, radius + dx:radius + dx + w]
            d = np.where(shifted & (d > dist), dist, d)
    return d


def quantize(cov, style):
    """Map a coverage map to palette indices reproducing the JP page style
    (recipe measured from pristine glyph stats, recon glyph_stats.txt)."""
    out = np.full(cov.shape, BG, np.uint8)
    if style == "plain_ramp":                       # 15=clear .. 0=full ink
        return np.rint(BG - cov * BG).astype(np.uint8)
    d = _dist_to_core(cov)
    if style == "dark_core_white_glow":             # img0
        glow = [(1.0, 10), (1.5, 12), (2.3, 13), (3.3, 14)]
        ink = [(0.75, 4), (0.6, 3), (0.45, 2), (0.3, 9), (0.2, 8), (0.1, 7)]
    elif style == "white_core_dark_outline":        # img1
        glow = [(1.5, 5), (2.0, 10), (2.3, 11), (2.9, 12), (3.6, 13),
                (4.3, 14)]
        ink = [(0.75, 0), (0.55, 1), (0.4, 2), (0.25, 3), (0.12, 4)]
    else:
        raise ValueError(style)
    for lim, idx in reversed(glow):                 # nearest band wins
        out[(d <= lim) & (d > 0)] = idx
    for lim, idx in reversed(ink):                  # strongest coverage wins
        out[cov >= lim] = idx
    return out


def render_line(text, font, rect, margin):
    """Coverage map (24 x span) for one line, ink+glow kept inside the span."""
    lo, hi = rect.get("clip", [rect["u"], rect["u"] + rect["w"]])
    span = hi - lo
    bbox = font.getbbox(text)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    cap = span - 2 * margin
    assert tw <= cap, (f"seq {rect['seq']} '{text}' is {tw}px > {cap}px "
                       f"(rect {rect['page']} u={rect['u']} v={rect['v']}) — "
                       f"reword in r2881_ending_rects.json")
    # vertically the JP glyphs fill the 24px rect too; only the faint outer
    # glow rings (alpha <= 0x30) get clipped at the rect edge, as in the JP.
    assert th <= LINE_H - 4, f"seq {rect['seq']}: text too tall"
    img = Image.new("L", (span, LINE_H), 0)
    x = margin if rect.get("align") == "left" else (span - tw) // 2
    ImageDraw.Draw(img).text((x - bbox[0], (LINE_H - th) // 2 - bbox[1]),
                             text, fill=255, font=font)
    return lo, np.asarray(img, dtype=np.float64) / 255.0


def patch_page(raw, name, rects, sprites, font, previews):
    g = PAGES[name]
    off, n, size = g["off"], g["size"], g["size"] * g["size"] // 2
    blob = raw[off:off + size]
    lin = np.array(deswizzle_psmt4(blob, n, n, bw_psmt4=g["bw"],
                                   dbw_ct32=g["dbw"]), np.uint8).reshape(n, n)
    assert bytes(swizzle_psmt4(bytes(lin.ravel()), n, n, bw_psmt4=g["bw"],
                               dbw_ct32=g["dbw"])) == blob, \
        f"{name}: pre-edit swizzle roundtrip FAILED"

    mine = [s for s in sprites if s["texset"] in g["texsets"]]
    union = np.zeros((n, n), bool)
    for s in mine:
        union[s["v"]:s["v"] + s["h"], s["u"]:s["u"] + s["w"]] = True
    dead = np.zeros((n, n), bool)
    for x0, y0, x1, y1 in g.get("dead", []):
        dead[y0:y1, x0:x1] = True
    assert not (dead & union).any(), f"{name}: dead region overlaps a sprite"
    stray = int(((lin != BG) & ~union & ~dead).sum())
    assert stray <= MAX_STRAY_JP_INK, \
        f"{name}: {stray} JP ink px outside sprite rects — page not text-only"

    # every text rect (w>16) in the table must be covered by a JSON rect
    keys = {(r["u"], r["v"], r["w"]) for r in rects}
    for r in rects:
        keys.update(tuple(a) for a in r.get("aliases", []))
    for s in mine:
        if s["h"] == LINE_H and s["w"] > 16:
            assert (s["u"], s["v"], s["w"]) in keys, \
                f"{name}: sprite {s['i']} rect not translated"
    table = {(s["u"], s["v"], s["w"]) for s in mine}
    for r in rects:
        assert (r["u"], r["v"], r["w"]) in table, \
            f"seq {r['seq']}: rect not in sprite table"

    before = lin.copy()
    lin[:, :] = BG                     # text-only page (asserted above);
    for r in rects:                    # punctuation sprites stay blank
        lo, cov = render_line(r["en"], font, r, g["margin"])
        idx = quantize(cov, g["style"])
        sub = lin[r["v"]:r["v"] + LINE_H, lo:lo + idx.shape[1]]
        np.copyto(sub, idx, where=idx != BG)

    # nothing may be drawn outside the rect union
    assert not ((lin != BG) & ~union).any(), f"{name}: ink outside rects"

    new_blob = bytes(swizzle_psmt4(bytes(lin.ravel()), n, n, bw_psmt4=g["bw"],
                                   dbw_ct32=g["dbw"]))
    assert len(new_blob) == size
    assert bytes(deswizzle_psmt4(new_blob, n, n, bw_psmt4=g["bw"],
                                 dbw_ct32=g["dbw"])) == bytes(lin.ravel()), \
        f"{name}: post-edit swizzle roundtrip FAILED"
    previews.append((name, before, lin.copy()))
    print(f"  {name}: {len(rects)} lines, "
          f"{sum(a != b for a, b in zip(blob, new_blob))} bytes changed")
    return off, new_blob


def clut(raw, off):
    c = np.frombuffer(raw[off:off + 64], np.uint8).reshape(16, 4).astype(float)
    c[:, 3] = np.minimum(c[:, 3] / 128.0, 1.0)
    return c


def save_previews(raw, previews):
    """True-colour composites (real CLUTs) over dark / mid / bright fields."""
    os.makedirs(OUT_DIR, exist_ok=True)
    for name, before, after in previews:
        g = PAGES[name]
        tiles = []
        for ci, coff in enumerate(g["cluts"]):
            pal = clut(raw, coff)
            for bgv in (20, 128, 235):
                row = []
                for page in (before, after):
                    px = pal[page]
                    a = px[..., 3:4]
                    rgb = px[..., :3] * a + bgv * (1 - a)
                    row.append(rgb.astype(np.uint8))
                tiles.append(np.concatenate(row, axis=1))
        img = np.concatenate(tiles, axis=0)
        Image.fromarray(img).save(os.path.join(OUT_DIR, f"r2881_{name}_truecolour.png"))


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    cfg = json.load(open(LABELS, encoding="utf-8"))
    raw = open(SRC, "rb").read()
    print(f"source: {SRC} ({len(raw)} bytes)")
    sprites = parse_sprites(raw)
    font = load_font(cfg["font_size"], bold=True)

    patched = bytearray(raw)
    windows, previews = [], []
    for name in PAGES:
        rects = [r for r in cfg["rects"] if r["page"] == name]
        off, new_blob = patch_page(raw, name, rects, sprites, font, previews)
        patched[off:off + len(new_blob)] = new_blob
        windows.append((off, off + len(new_blob)))
    patched = bytes(patched)
    assert len(patched) == len(raw), "total file size changed"
    assert_outside_window_pristine(raw, patched, windows)
    print("asserts: size unchanged; only the 3 pixel payloads changed")
    save_previews(raw, previews)

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
