#!/usr/bin/env python3
"""patch_r2147 — re-render the tavern submenu sheet and the quest/bulletin
button-hint strip inside R2147 into English, plus mirror the hint strip into
R2155.

Resources (extracted/packdata_raw/):
  2147_type06.raw  382976 bytes
  2155_type10.raw  274432 bytes

Two VERIFIED pixel windows in R2147 (all 256x256 PSMT4,
deswizzle_psmt4(data[off:off+32768], 256, 256, bw_psmt4=256, dbw_ct32=128);
GS-dump byte-verified — see build/recon_v86/tavern-submenu/derive_map.py):

  Window 1 @0x560  (section 0) — tavern submenu sheet. ALSO the bulletin/
    quest screen title source; rows are ~24px bands. 9 menu-item bands:
      外に出る=Go Outside; 王国掲示板=Message Board; 依頼=Requests;
      達成履歴=Personal Deeds; トラップゲーム=Trap Game;
      酒場+'bar LUNA LIGHT' band → cleared whole band, 'Bar Luna Light'
        rendered fresh; 練習=Practice; ゲーム=Game; 景品交換=Prize Exchange.

  Window 2 @0x12020 (section 2, == decimal 73760, the same offset the task
    calls "sub2 @73760") — bulletin-board sheet. Two button-help rows below
    the 'Bulletin Board' ribbon:
      Row1 (y40-55): 'L1・R1/切替' → 'L1/R1 Switch'; '次頁' → 'Next Page'.
      Row2 (y56-71): '○/決定' → keep the ○ glyph + 'OK'; '×/戻る' → keep ×
        + 'Back'; '切り替え' → 'Switch'.
    Everything already-English (Bulletin Board ribbon, REQUEST LIST, NEW,
    digits, 1p-10p) and the marble decoration are untouched.

NEVER touched: 0x000-0x55F (display list + upload records, runtime-patched by
the EE), CLUT regions, the canvas @0x1A6A0, and subs 3-5. Only the two 32KB
pixel windows are rewritten; byte size is preserved exactly.

R2155 mirror: 2155_type10.raw holds a byte-identical copy of the hint strip
at +0x9920 (VERIFIED). After patching window 2, this asserts
  pristine R2155[0x9920:0x9920+32768] == pristine R2147[0x12020:...]
then writes the SAME patched 32KB into R2155 @0x9920; all other R2155 bytes
stay pristine.

Outputs:
  build/packdata_resources/2147_type06.raw
  build/packdata_resources/2155_type10.raw
Previews (build/recon_v86/r2147-out/):
  win1_before.png/win1_after.png, win2_before.png/win2_after.png

Exits nonzero on any failure.
"""
import json
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "tools"))

from strip_patcher import (  # noqa: E402
    StripRegion, patch_strip, assert_outside_window_pristine,
)

R2147_IN = os.path.join(BASE, "extracted", "packdata_raw", "2147_type06.raw")
R2155_IN = os.path.join(BASE, "extracted", "packdata_raw", "2155_type10.raw")
R2147_OUT = os.path.join(BASE, "build", "packdata_resources", "2147_type06.raw")
R2155_OUT = os.path.join(BASE, "build", "packdata_resources", "2155_type10.raw")
LABELS_JSON = os.path.join(BASE, "data", "strip_labels", "r2147_labels.json")
PREVIEW_DIR = os.path.join(BASE, "build", "recon_v86", "r2147-out")

R2147_SIZE = 382976
R2155_SIZE = 274432
WIN_SIZE = 256 * 256 // 2          # 32768
R2155_MIRROR_OFF = 0x9920          # hint-strip copy inside R2155
HINT_WIN_OFF = 0x12020             # window 2 in R2147


def _load_labels():
    with open(LABELS_JSON, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    return cfg


def _tuplify(labels):
    """JSON arrays -> tuples the strip_patcher API expects."""
    return [tuple(e) for e in labels]


def main():
    if sys.stdout.encoding and "utf" not in sys.stdout.encoding.lower():
        sys.stdout.reconfigure(encoding="utf-8")

    os.makedirs(os.path.dirname(R2147_OUT), exist_ok=True)
    os.makedirs(PREVIEW_DIR, exist_ok=True)

    cfg = _load_labels()
    tex_w = cfg["tex_w"]
    tex_h = cfg["tex_h"]
    dbw = cfg["dbw_ct32"]
    bg = cfg["bg_index"]
    ink = cfg["ink_index"]

    orig = open(R2147_IN, "rb").read()
    assert len(orig) == R2147_SIZE, \
        f"R2147 size {len(orig)} != {R2147_SIZE}"

    patched = orig
    windows = []
    for i, win in enumerate(cfg["windows"], start=1):
        off = win["pixel_off"]
        region = StripRegion(pixel_off=off, tex_w=tex_w, tex_h=tex_h,
                             dbw_ct32=dbw, bg_index=bg, ink_index=ink,
                             name=win["name"])
        labels = _tuplify(win["labels"])
        print(f"[window {i}] {win['name']} @0x{off:X}")
        patched = patch_strip(patched, region, labels,
                              preview_prefix=os.path.join(PREVIEW_DIR,
                                                          f"win{i}"))
        windows.append((off, off + WIN_SIZE))

    # ── R2147 integrity: ONLY the two pixel windows changed ──
    assert len(patched) == R2147_SIZE, "R2147 length changed"
    assert_outside_window_pristine(orig, patched, windows)

    # Per-window roundtrip exactness: re-patching the already-patched bytes is
    # idempotent (render is deterministic) — confirms the window encodes cleanly.
    recheck = patched
    for i, win in enumerate(cfg["windows"], start=1):
        region = StripRegion(pixel_off=win["pixel_off"], tex_w=tex_w,
                             tex_h=tex_h, dbw_ct32=dbw, bg_index=bg,
                             ink_index=ink, name=win["name"])
        recheck = patch_strip(recheck, region, _tuplify(win["labels"]),
                              verbose=False)
    assert recheck == patched, "re-patch not idempotent — encode unstable"

    with open(R2147_OUT, "wb") as f:
        f.write(patched)
    print(f"wrote {R2147_OUT} ({len(patched)} bytes)")

    # ── R2155 mirror ──
    r2155_orig = open(R2155_IN, "rb").read()
    assert len(r2155_orig) == R2155_SIZE, \
        f"R2155 size {len(r2155_orig)} != {R2155_SIZE}"

    pristine_hint = orig[HINT_WIN_OFF:HINT_WIN_OFF + WIN_SIZE]
    r2155_mirror = r2155_orig[R2155_MIRROR_OFF:R2155_MIRROR_OFF + WIN_SIZE]
    assert r2155_mirror == pristine_hint, (
        "R2155 mirror @0x9920 is NOT byte-identical to pristine "
        "R2147 hint window @0x12020 — mirror assumption broken")

    patched_hint = patched[HINT_WIN_OFF:HINT_WIN_OFF + WIN_SIZE]
    r2155_patched = bytearray(r2155_orig)
    r2155_patched[R2155_MIRROR_OFF:R2155_MIRROR_OFF + WIN_SIZE] = patched_hint
    r2155_patched = bytes(r2155_patched)

    assert len(r2155_patched) == R2155_SIZE, "R2155 length changed"
    assert_outside_window_pristine(
        r2155_orig, r2155_patched,
        [(R2155_MIRROR_OFF, R2155_MIRROR_OFF + WIN_SIZE)])

    with open(R2155_OUT, "wb") as f:
        f.write(r2155_patched)
    print(f"wrote {R2155_OUT} ({len(r2155_patched)} bytes)")

    # ── decode the R2155 mirror window for visual confirmation ──
    region = StripRegion(pixel_off=R2155_MIRROR_OFF, tex_w=tex_w, tex_h=tex_h,
                         dbw_ct32=dbw, bg_index=bg, ink_index=ink,
                         name="r2155_mirror")
    from strip_patcher import _deswizzle_gated, save_preview
    lin = _deswizzle_gated(r2155_patched, region)
    save_preview(lin, tex_w, tex_h,
                 os.path.join(PREVIEW_DIR, "r2155_mirror_after.png"), bg, ink)
    lin0 = _deswizzle_gated(r2155_orig, region)
    save_preview(lin0, tex_w, tex_h,
                 os.path.join(PREVIEW_DIR, "r2155_mirror_before.png"), bg, ink)

    print("OK: all asserts passed.")


if __name__ == "__main__":
    main()
