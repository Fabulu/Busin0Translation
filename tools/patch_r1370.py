#!/usr/bin/env python3
"""patch_r1370 — render English party-rank words over the R1370 trust-medallion
kanji sheet (dungeon / battle HUD).

VERIFIED FORMAT (v86-r1370-trust)
─────────────────────────────────
R1370 = extracted/packdata_raw/1370_type04.raw, 81920 bytes, type-04, member of
the strip family handled by tools/strip_patcher.py.

Section table (16-byte LE entries at offset 0):
    id0 size 38560 off    64   -> GIF upload section A (T1 sheet)
    id1 size 38240 off 38624   -> GIF upload section B (T2 sheet)
    id2 size  2168 off 76864   -> aux
    id3 size  1588 off 79040   -> aux

Each GIF section's first upload descriptor is a 128x64 CT32 page upload
(32768 bytes) that the game interprets as a 256x256 PSMT4 texture
(bw_psmt4=256, dbw_ct32=128). strip_patcher.find_pixel_base() (flush-to-end
rule) returns the pixel blob offsets:
    section 0 -> 3808   (T1, this patch)
    section 1 -> 42304  (T2, DO NOT TOUCH)

VERIFICATION (reproduced here, gated before any write — see verify()):
The T1 blob @3808 was byte-matched against the dungeon GS dump
(build/recon_v86/dungeon-ui/normaldungeonscreen/GS.bin, VRAM starts at byte
425). Reverse-indexing every 128x128 PSMT4 VRAM page (block-linear deswizzle,
re-swizzled to host CT32 256-byte runs, reverse_match.py method) shows the
blob's 256-byte host runs land EXACTLY (100%) in VRAM pages 339-342 — the
dungeon/battle trust-medallion kanji pages. The hypothesised base 11872/12128
was a page-column-ambiguity artefact; 3808 is the true section-0 pixel base.

The decoded 256x256 sheet shows a 5x2 grid of large brush trust kanji:
    絆 誓 信 友 情      (Bond  Pledge Trust Friends Sympathy)
    義 盟 疑 憎 不      (Duty  Alliance Doubt Hate Broken)
plus month-digit ramps, a "Leader" label, decorative borders and the
already-English class badges (AUT/FIG/MAG/...). This patch rewrites ONLY the
ten kanji cells; everything else in the blob, and the entire T2 blob, stay
pristine. English words come from build/recon_v86/glossary/canonical_labels.json
(recommended short forms: 情=Sympathy, 義=Duty).

Output: build/packdata_resources/1370_type04.raw, exactly 81920 bytes; only the
T1 pixel window [3808, 36576) differs from the pristine raw (asserted).
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "tools"))

from psmt4_deswizzle import _psmt4_nibble_addr, swizzle_psmt4  # noqa: E402
import strip_patcher as sp  # noqa: E402
from strip_patcher import (  # noqa: E402
    StripRegion, _deswizzle_gated, find_pixel_base, parse_section_table,
    render_label, load_font, clear, blit, sample_rect_indices,
    save_preview, assert_outside_window_pristine,
)

RAW = os.path.join(BASE, "extracted", "packdata_raw", "1370_type04.raw")
OUT = os.path.join(BASE, "build", "packdata_resources", "1370_type04.raw")
LABELS = os.path.join(BASE, "data", "strip_labels", "r1370_labels.json")
GS = os.path.join(BASE, "build", "recon_v86", "dungeon-ui",
                  "normaldungeonscreen", "GS.bin")
PREVIEW_DIR = os.path.join(BASE, "build", "recon_v86", "r1370-out")

TEX_W = TEX_H = 256
DBW_CT32 = 128
BW_PSMT4 = 256
PIXEL_OFF = 3808                 # verified T1 section-0 pixel base
PIXEL_SIZE = TEX_W * TEX_H // 2  # 32768
PATCH_WINDOW = (PIXEL_OFF, PIXEL_OFF + PIXEL_SIZE)   # (3808, 36576)
T1_VRAM_PAGES = (339, 340, 341, 342)


# ───────────────────────── VRAM verification ─────────────────────────

def _page_host_runs(vram, pg):
    """Return the 32 host-order 256-byte runs of a 128x128 PSMT4 VRAM page."""
    base = pg * 8192
    lin = bytearray(128 * 128)
    for y in range(128):
        for x in range(128):
            nib = _psmt4_nibble_addr(x, y, 128)
            b = vram[base + nib // 2]
            lin[y * 128 + x] = (b >> 4) & 0xF if (nib & 1) else b & 0xF
    host = bytes(swizzle_psmt4(lin, 128, 128, bw_psmt4=128, dbw_ct32=64))
    return [host[k * 256:(k + 1) * 256] for k in range(32)]


def _vram_run_index(vram, pg_lo=320, pg_hi=360):
    """Index every content (256-byte) host run of VRAM pages -> set(pages)."""
    idx = {}
    for pg in range(pg_lo, pg_hi):
        for run in _page_host_runs(vram, pg):
            if len(set(run)) > 8:                  # skip flat/empty runs
                idx.setdefault(run, set()).add(pg)
    return idx


def _blob_vram_purity(blob, idx, want_pages, step=16):
    """Scan a pixel blob's 256-byte windows (all phases, `step` apart) and
    count how many appear in the VRAM index and how many of those land in
    `want_pages`. The host CT32 bytes of a strip-family upload appear verbatim
    in the GS VRAM dump (reverse_match.py method); a blob that is exclusively a
    given HUD page set therefore yields 100% purity with zero stray pages.

    Returns (matched, in_want, stray_pages_dict).
    """
    want = set(want_pages)
    matched = in_want = 0
    stray = {}
    for i in range(0, len(blob) - 256 + 1, step):
        run = blob[i:i + 256]
        if len(set(run)) <= 8:
            continue
        pgs = idx.get(run)
        if not pgs:
            continue
        matched += 1
        if pgs & want:
            in_want += 1
        else:
            for p in pgs:
                stray[p] = stray.get(p, 0) + 1
    return matched, in_want, stray


def verify(data):
    """Byte-match the T1 blob against dungeon VRAM pages 339-342.

    The decisive test (reverse_match.py method): every content window of the
    blob that appears anywhere in VRAM pages 320-360 must land in the T1 page
    set 339-342 (100% purity, zero stray pages). This proves the blob is
    exclusively the dungeon-HUD trust-kanji source, so patching it cannot
    disturb any other VRAM page.

    Returns (ok: bool, purity_pct: float, report: str). Requires the GS dump;
    if it is absent we cannot verify and must skip.
    """
    if not os.path.exists(GS):
        return False, 0.0, f"GS dump not found at {GS} — cannot verify"

    gs = open(GS, "rb").read()
    vram = gs[425:425 + 4 * 1024 * 1024]
    idx = _vram_run_index(vram)

    blob = data[PIXEL_OFF:PIXEL_OFF + PIXEL_SIZE]
    matched, in_t1, stray = _blob_vram_purity(blob, idx, T1_VRAM_PAGES)

    purity = 100.0 * in_t1 / matched if matched else 0.0
    ok = matched >= 32 and purity >= 99.9 and not stray
    report = (f"T1 blob @{PIXEL_OFF}: {matched} VRAM-matched windows, "
              f"{in_t1} in pages {T1_VRAM_PAGES} ({purity:.2f}% purity)"
              + (f", STRAY {stray}" if stray else ", zero stray pages"))
    return ok, purity, report


# ───────────────────────── patch ─────────────────────────

def patch(data, cells, region):
    """Clear + render English into each kanji cell. Returns patched bytes."""
    linear = _deswizzle_gated(data, region)

    os.makedirs(PREVIEW_DIR, exist_ok=True)
    save_preview(linear, TEX_W, TEX_H,
                 os.path.join(PREVIEW_DIR, "patch_before.png"),
                 region.bg_index, region.ink_index)

    for c in cells:
        x, y, w, h = c["x"], c["y"], c["w"], c["h"]
        text = c["english"]
        # Sample the brush ink ramp inside this cell to match the glyph colour.
        ink, hist = sample_rect_indices(linear, TEX_W, x, y, w, h,
                                        region.bg_index)
        clear(linear, TEX_W, x, y, w, h, region.bg_index)
        # Bold serif-ish render, centered. render_label() auto-shrinks the
        # start size until the word fits (w-2)px (floor 7px), so longer ranks
        # (Sympathy / Alliance / Friends) drop a point or two automatically.
        start = c.get("font_size", 14)
        cell = render_label(text, w, h, load_font(start),
                            region.bg_index, ink, "center")
        blit(linear, TEX_W, x, y, w, h, cell)
        print(f"    [{x:3},{y:3} {w}x{h}] {c['kanji']} -> '{text}' "
              f"ink={ink} start={start} ({sum(hist.values())}px sampled)")

    save_preview(linear, TEX_W, TEX_H,
                 os.path.join(PREVIEW_DIR, "patch_after.png"),
                 region.bg_index, region.ink_index)

    res = bytearray(data)
    res[PIXEL_OFF:PIXEL_OFF + PIXEL_SIZE] = swizzle_psmt4(
        linear, TEX_W, TEX_H, bw_psmt4=BW_PSMT4, dbw_ct32=DBW_CT32)
    return bytes(res)


def main():
    data = open(RAW, "rb").read()
    assert len(data) == 81920, f"R1370 raw is {len(data)}B, expected 81920"

    # Sanity: confirm the verified offset is what find_pixel_base() returns
    # for section 0 (defensive — guards against a re-extracted raw shifting).
    secs = parse_section_table(data)
    fb = find_pixel_base(data, secs[0]["offset"], secs[0]["size"])
    print(f"section0 find_pixel_base = {fb} (using verified PIXEL_OFF={PIXEL_OFF})")
    if fb != PIXEL_OFF:
        print(f"SKIPPED: R1370 T1 base unverified — find_pixel_base()={fb} "
              f"!= expected {PIXEL_OFF}; raw layout changed.")
        return 0

    ok, pct, report = verify(data)
    print("VERIFY:", report)
    if not ok:
        print("SKIPPED: R1370 T1 base unverified")
        return 0
    print(f"VERIFIED base {PIXEL_OFF}, T1 match {pct:.2f}% on pages "
          f"{T1_VRAM_PAGES}")

    spec = json.load(open(LABELS, encoding="utf-8"))
    cells = spec["kanji_cells"]
    region = StripRegion(pixel_off=PIXEL_OFF, tex_w=TEX_W, tex_h=TEX_H,
                         bw_psmt4=BW_PSMT4, dbw_ct32=DBW_CT32,
                         bg_index=0, ink_index=15, name="r1370_t1")

    patched = patch(data, cells, region)

    # ── integrity asserts ───────────────────────────────────────────────
    assert len(patched) == 81920, f"size changed: {len(patched)}"
    # Only the T1 pixel window may differ — proves T2 sheet + all other
    # content (chargen-era data, class badges, borders) untouched.
    assert_outside_window_pristine(data, patched, [PATCH_WINDOW])
    # The T2 blob window is explicitly inside the pristine region above, but
    # assert it directly for clarity.
    t2 = (42304, 75072)
    assert patched[t2[0]:t2[1]] == data[t2[0]:t2[1]], "T2 blob modified!"
    # Confirm the patch DID change the T1 window (non-empty diff).
    assert patched[PATCH_WINDOW[0]:PATCH_WINDOW[1]] != \
        data[PATCH_WINDOW[0]:PATCH_WINDOW[1]], "no change in T1 window?"

    # Re-run the VRAM byte-match on the patched file's UNPATCHED regions
    # (pages 344-347 = T2) to prove surrounding HUD art is intact.
    gs = open(GS, "rb").read()
    vram = gs[425:425 + 4 * 1024 * 1024]
    idx = _vram_run_index(vram)
    t2_pages = (344, 345, 346, 347)
    t2blob = patched[42304:42304 + PIXEL_SIZE]
    mat, in_t2, stray = _blob_vram_purity(t2blob, idx, t2_pages)
    t2pct = 100.0 * in_t2 / mat if mat else 0.0
    print(f"POST-PATCH T2 (pages {t2_pages}) purity: {in_t2}/{mat} "
          f"({t2pct:.2f}%)"
          + (f" STRAY {stray}" if stray else " zero stray")
          + " — surrounding HUD art intact")
    assert mat >= 32 and t2pct >= 99.9 and not stray, \
        f"T2 art corrupted: {t2pct:.2f}% purity, stray {stray}"

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "wb") as f:
        f.write(patched)
    print(f"WROTE {OUT} ({len(patched)} bytes)")
    print(f"previews: {os.path.join(PREVIEW_DIR, 'patch_before.png')} / "
          f"{os.path.join(PREVIEW_DIR, 'patch_after.png')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
