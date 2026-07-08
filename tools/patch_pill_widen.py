#!/usr/bin/env python3
"""patch_pill_widen — widen the item-name "pill" capsule (R2139 sub13 rec2 +
R2138 sub27 box art) from 192px to 256px.

THE BUG (issue: treasure-drop / shop item-name placement): long English item
names ("Town Return Potion", "Zateal Spell Book") overflow the ornate capsule
drawn behind the item name. On screen the capsule is a constant ~192px wide —
sized for short Japanese item names.

DRAW ARCHITECTURE (v180 recon — supersedes PILL_INVESTIGATION_DOSSIER.md):
  * The dossier's "seven 188x24 records at 0xdca192" were a MISALIGNED parse
    (off by 2 into the 10-byte record stream; "u=1801" = the previous record's
    page/flag bytes 0x0709; byte +9 of each packed record is unwritten malloc
    garbage — parser 0x490D20 writes only 9 bytes). Corrected records there are
    seven 24x12 tiles at v=188 — unrelated to the pill.
  * The dossier's candidate call site 0x170E98 (tile pairs 185/186 vs 187/188)
    draws the big torn-parchment dialog box (R2139 sub10: 40px caps + middle,
    "Take the item?" window), NOT the pill. Falsified.
  * The REAL pill art: R2138 sub27 (256x256 PSMT4 atlas @0x16D4F0, pixel data
    @+0x740), box band at (u,v)=(0,136)..(192,200): double-line left cap
    (x0..6), horizontal rails, right border at x184..186 with bracket serifs
    to x189, columns 190..255 of the band 100% blank (index 0).
  * Its geometry record: R2139 sub13 rec2 (BE u32 {u=0, v=136, w=192, h=64,
    page=3} at file offset 0x1220). The shop scene (pillshop.p2s) has R2139
    loaded byte-identical at 0xdca... heap and the on-screen capsule measures
    ~196px = 192 + bilinear edge — consistent with a natural-width draw.
  * Handle chain (group 1/2): tile-entry table 0x4B6340, handle table 0x4B61F0
    entry 11 = {R2138 sub27 pixels, R2139 sub13 geometry}. Tiles 187..191 map
    to sub13 recs 0..4; the box record = group-1/2 tile 189.

THE FIX (dossier option 1, resource-side):
  1. R2139 sub13 rec2 w: 192 -> 256 (2 bytes at file offset 0x1228, BE u32).
  2. R2138 sub27 band re-ink: for rows y in [136,200), new[176..256) =
     old[112..192)  — duplicates 64px of clean middle rail and lands the right
     border at x248..250 (serifs to x253). Everything else pixel-identical.
  If the draw honors the record's natural width, the capsule widens to 256px.
  If the draw turns out to pass an explicit width, the art is compressed
  ~1.33x horizontally into the same 192px box (cosmetically benign) — a single
  boot at the pill shop / a treasure drop disambiguates. Data-only, no EXE
  bytes, no battle-arena bytes.

GATES (any failure aborts the build):
  * R2139 pristine record bytes must equal the expected {0,136,192,64,3}.
  * R2138 sub27 pristine-window roundtrip must be byte-lossless (proves the
    deswizzle geometry, cf. patch_r2138 strict_roundtrip).
  * The pristine band margin x[192,256) y[136,200) must be 100% index 0.
  * Output diff containment: deswizzled pixels may differ from input ONLY
    inside x[176,256) x y[136,200); bytes outside the sub27 pixel window must
    be byte-identical to the input file.

Inputs:  build/packdata_resources/2138_type29.raw  (Step 3.9 output — REQUIRED)
         extracted/packdata_raw/2139_type15.raw    (pristine)
Outputs: build/packdata_resources/2138_type29.raw  (in place)
         build/packdata_resources/2139_type15.raw
Preview: build/pill_widen_before.png / build/pill_widen_after.png
"""
import os
import struct
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "tools"))

from psmt4_deswizzle import deswizzle_psmt4, swizzle_psmt4  # noqa: E402

R2138_PATH = os.path.join(BASE, "build", "packdata_resources", "2138_type29.raw")
R2139_IN = os.path.join(BASE, "extracted", "packdata_raw", "2139_type15.raw")
R2139_OUT = os.path.join(BASE, "build", "packdata_resources", "2139_type15.raw")

# R2138 sub27 pixel window (same constants as tools/patch_r2138.py sub27 def)
SUB27_OFF = 0x16D4F0
SUB27_PIXEL_OFF = 0x740
SUB27_PIXEL_SIZE = 32768
TEX_W = TEX_H = 256
BW_PSMT4 = 256
DBW_CT32 = 128

# Band of the pill box art inside the sub27 texture
BAND_Y0, BAND_Y1 = 136, 200          # rows [136, 200)
SRC_X0, SRC_X1 = 112, 192            # copied span (middle rail + right cap)
DST_X0 = 176                         # paste destination (DST_X0+80 = 256)

# R2139 sub13 rec2 (BE u32 fields at file offset 0x1220)
REC_OFF = 0x1220
PRISTINE_REC = struct.pack(">5I", 0, 136, 192, 64, 3)
NEW_W = 256


def fail(msg):
    print(f"FATAL(patch_pill_widen): {msg}")
    sys.exit(1)


def main():
    print("--- patch_pill_widen: item-name capsule 192 -> 256 ---")

    # ---------- R2139: widen the geometry record ----------
    if not os.path.exists(R2139_IN):
        fail(f"missing pristine {R2139_IN}")
    r2139 = bytearray(open(R2139_IN, "rb").read())
    if len(r2139) != 6144:
        fail(f"R2139 unexpected size {len(r2139)} (want 6144)")
    got = bytes(r2139[REC_OFF:REC_OFF + 20])
    if got != PRISTINE_REC:
        fail(f"R2139 sub13 rec2 mismatch at 0x{REC_OFF:X}: {got.hex()} "
             f"(want {PRISTINE_REC.hex()}) — resource layout changed?")
    struct.pack_into(">I", r2139, REC_OFF + 8, NEW_W)
    # Containment: exactly the w-field word may differ from pristine.
    pristine = open(R2139_IN, "rb").read()
    diffs = [i for i, (a, b) in enumerate(zip(pristine, r2139)) if a != b]
    if not diffs or not all(REC_OFF + 8 <= i < REC_OFF + 12 for i in diffs):
        fail(f"R2139 diff containment violated: {[hex(i) for i in diffs]}")
    with open(R2139_OUT, "wb") as f:
        f.write(r2139)
    print(f"  R2139 sub13 rec2 w: 192 -> {NEW_W} "
          f"({len(diffs)} bytes changed at {[hex(i) for i in diffs]}) -> {R2139_OUT}")

    # ---------- R2138 sub27: re-ink the box band ----------
    if not os.path.exists(R2138_PATH):
        fail(f"missing {R2138_PATH} (Step 3.9 patch_r2138 must run first)")
    r2138 = bytearray(open(R2138_PATH, "rb").read())
    if len(r2138) != 1542144:
        fail(f"R2138 unexpected size {len(r2138)}")
    lo = SUB27_OFF + SUB27_PIXEL_OFF
    hi = lo + SUB27_PIXEL_SIZE
    pix_in = bytes(r2138[lo:hi])

    lin = bytearray(deswizzle_psmt4(pix_in, TEX_W, TEX_H,
                                    bw_psmt4=BW_PSMT4, dbw_ct32=DBW_CT32))
    if len(lin) != TEX_W * TEX_H:
        fail("deswizzle size mismatch")
    # GATE: lossless roundtrip on the INPUT before we touch anything.
    if bytes(swizzle_psmt4(lin, TEX_W, TEX_H, bw_psmt4=BW_PSMT4,
                           dbw_ct32=DBW_CT32)) != pix_in:
        fail("sub27 roundtrip not lossless — geometry wrong, refusing to patch")
    lin_before = bytes(lin)

    # GATE: the target margin must be blank in the input.
    for y in range(BAND_Y0, BAND_Y1):
        for x in range(192, 256):
            if lin[y * TEX_W + x] != 0:
                fail(f"sub27 margin not blank at ({x},{y}) — layout changed?")

    # Re-ink: shift [112,192) right by 64 -> [176,256) per band row.
    for y in range(BAND_Y0, BAND_Y1):
        row = y * TEX_W
        src = lin_before[row + SRC_X0:row + SRC_X1]
        lin[row + DST_X0:row + DST_X0 + len(src)] = src

    # GATE: containment — only x[176,256) y[136,200) may differ.
    for i, (a, b) in enumerate(zip(lin_before, lin)):
        if a != b:
            x, y = i % TEX_W, i // TEX_W
            if not (DST_X0 <= x < 256 and BAND_Y0 <= y < BAND_Y1):
                fail(f"pixel containment violated at ({x},{y})")

    # Sanity: right border must now have a solid vertical run near x248..250.
    ink_248 = sum(1 for y in range(BAND_Y0, BAND_Y1)
                  if lin[y * TEX_W + 248] != 0)
    if ink_248 < 40:
        fail(f"re-inked right border missing (col248 ink rows={ink_248})")

    pix_out = bytes(swizzle_psmt4(lin, TEX_W, TEX_H,
                                  bw_psmt4=BW_PSMT4, dbw_ct32=DBW_CT32))
    r2138[lo:hi] = pix_out
    # GATE: nothing outside the pixel window may change.
    orig = open(R2138_PATH, "rb").read()
    if r2138[:lo] != orig[:lo] or r2138[hi:] != orig[hi:]:
        fail("bytes outside sub27 pixel window changed")
    with open(R2138_PATH, "wb") as f:
        f.write(r2138)
    print(f"  R2138 sub27 band re-inked (rows {BAND_Y0}..{BAND_Y1 - 1}, "
          f"cols {DST_X0}..255; border now ~x248) -> {R2138_PATH}")

    # Previews
    try:
        from PIL import Image
        for tag, data in (("before", lin_before), ("after", bytes(lin))):
            img = Image.new("L", (TEX_W, 80))
            img.putdata([min(p, 15) * 17 for p in
                         data[(BAND_Y0 - 8) * TEX_W:(BAND_Y1 + 8) * TEX_W]])
            img.save(os.path.join(BASE, "build", f"pill_widen_{tag}.png"))
        print("  previews: build/pill_widen_before.png / _after.png")
    except Exception as e:  # preview is non-load-bearing
        print(f"  (preview skipped: {e})")

    print("patch_pill_widen: OK")


if __name__ == "__main__":
    main()
