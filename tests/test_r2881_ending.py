#!/usr/bin/env python3
"""
test_r2881_ending.py -- the ENDING narration pages (R2881 sub7) render where
and how the game draws them.

RUN-20261109-1725 (v204), player report "final sequence text hard to read;
fade-to-black / fade-to-white text untranslated". Pins the three fixes:
  * every EN ink pixel lies inside a sprite rect of the R2881 sub6 table
    (the v94 inferred windows lost ~10-13% of the ink off-rect);
  * the palette style matches the JP page: img0 = dark core + white glow
    (index 10 ring present), img1 = white core + 1px dark outline (index 5
    ring present) -- the old plain 15..0 ramp produced a grey ghost;
  * img10 (climax / reprise lines) is no longer pristine Japanese, and every
    text rect in the sprite table has an EN line in r2881_ending_rects.json.
TIER-2: SKIPs when the pristine resource or the build output is absent.
"""

import importlib.util
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _helpers import ROOT, Skip, main_exit

sys.path.insert(0, os.path.join(ROOT, "tools"))
from psmt4_deswizzle import deswizzle_psmt4  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "patch_r2881_ending", os.path.join(ROOT, "tools", "patch_r2881_ending.py"))
P = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(P)


def _load():
    if not os.path.isfile(P.SRC) or not os.path.isfile(P.OUT):
        raise Skip("R2881 pristine/build missing")
    return open(P.SRC, "rb").read(), open(P.OUT, "rb").read()


def _page(raw, name):
    g = P.PAGES[name]
    n = g["size"]
    blob = raw[g["off"]:g["off"] + n * n // 2]
    return np.array(deswizzle_psmt4(blob, n, n, bw_psmt4=g["bw"],
                                    dbw_ct32=g["dbw"]), np.uint8).reshape(n, n)


def test_en_ink_inside_sprite_rects():
    pristine, built = _load()
    spr = P.parse_sprites(pristine)
    for name, g in P.PAGES.items():
        lin = _page(built, name)
        n = g["size"]
        union = np.zeros((n, n), bool)
        for s in spr:
            if s["texset"] in g["texsets"]:
                union[s["v"]:s["v"] + s["h"], s["u"]:s["u"] + s["w"]] = True
        off = int(((lin != P.BG) & ~union).sum())
        assert off == 0, f"{name}: {off} EN px outside every sprite rect"


def test_palette_style_matches_jp():
    _, built = _load()
    ink0 = _page(built, "img0")
    assert (ink0 == 4).sum() > 5000 and (ink0 == 10).sum() > 5000, \
        "img0 lacks dark core (4) / glow ring (10) -- plain ramp regression"
    ink1 = _page(built, "img1")
    assert (ink1 == 0).sum() > 5000 and (ink1 == 5).sum() > 5000, \
        "img1 lacks white core (0) / dark outline (5) -- plain ramp regression"


def test_img10_translated_and_all_rects_covered():
    pristine, built = _load()
    assert not np.array_equal(_page(pristine, "img10"), _page(built, "img10")), \
        "img10 (climax/reprise lines) ships pristine Japanese"
    cfg = json.load(open(P.LABELS, encoding="utf-8"))
    keys = set()
    for r in cfg["rects"]:
        assert r["en"].strip(), f"seq {r['seq']} empty"
        keys.add((r["page"], r["u"], r["v"], r["w"]))
        for a in r.get("aliases", []):
            keys.add((r["page"],) + tuple(a))
    for s in P.parse_sprites(pristine):
        page = next((k for k, g in P.PAGES.items() if s["texset"] in g["texsets"]), None)
        if page and s["h"] == P.LINE_H and s["w"] > 16:
            assert (page, s["u"], s["v"], s["w"]) in keys, \
                f"sprite {s['i']} ({page}) has no EN line"


TESTS = [test_en_ink_inside_sprite_rects, test_palette_style_matches_jp,
         test_img10_translated_and_all_rects_covered]

if __name__ == "__main__":
    main_exit(TESTS, "test_r2881_ending")
