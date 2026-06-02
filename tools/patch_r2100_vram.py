#!/usr/bin/env python3
"""
R2100 chargen/stat font atlas patcher using VRAM simulation.

Instead of deswizzle-edit-reswizzle (which may have TBW mismatch issues),
this patcher works directly in simulated GS VRAM space:

  1. Upload each sub-block's pixel data to VRAM using PSMCT32 addressing
     at the sub-block's embedded upload parameters (TBP0=0, dbw_ct32=128)
  2. Clear and write English letters using PSMT4 addressing at each
     glyph cell's pixel coordinates (col*16, row*16) with bw_psmt4=256
     (TBW=4 from TEX0 register)
  3. Download from VRAM back to PSMCT32 host format

This matches the R1188 Phase 4 approach (patch_r1188_comprehensive.py)
and avoids any position mapping issues from TBW mismatches.

R2100 structure:
  - 64-byte descriptor table (4 entries x 16 bytes)
  - 4 x 34,624 byte sub-blocks:
      - 0x4C0 (1216) bytes: VIF/GIF DMA chain header
      - 32,768 bytes: PSMT4 pixel data (256x256, uploaded as PSMCT32)
      - 640 bytes: CLUT tail (10 palettes)

GIF A+D from header: TEX0 TBP0=0, TBW=4, PSM=PSMT4, 256x256
  -> bw_psmt4 = TBW * 64 = 256
  -> Upload: dbw_ct32 = 128 (32768 bytes / 4 / 64 rows = 128 px wide)
"""

import struct
import sys
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "tools"))

from psmt4_deswizzle import (
    deswizzle_psmt4, swizzle_psmt4,
    _psmct32_word_addr, _psmt4_nibble_addr,
)

try:
    from PIL import Image, ImageFont, ImageDraw
except ImportError:
    print("ERROR: Pillow not installed. Run: pip install Pillow")
    sys.exit(1)

# ── Paths ──
DIG_PATH = os.path.join(BASE, "extracted", "PACKDATA.DIG")
OUTPUT_PATH = os.path.join(BASE, "build", "packdata_resources", "2100_type04.raw")
PREVIEW_DIR = os.path.join(BASE, "build")

# ── Constants ──
SECTOR = 2048
R2100_TOC_INDEX = 2100
TOC_ENTRIES = 2883
NUM_SUBS = 4
SUB_SIZE = 34624      # 0x8740
HDR_SIZE = 0x4C0      # 1216 bytes of VIF/GIF header per sub-block
PIXEL_SIZE = 32768    # 256x256 PSMT4 = 32768 bytes swizzled
TAIL_SIZE = 640       # CLUT data after pixels
TEX_W, TEX_H = 256, 256
CELL_W, CELL_H = 16, 16
COLS = TEX_W // CELL_W   # 16 cells per row
ROWS = TEX_H // CELL_H   # 16 cells per column

# Upload parameters (from GIF A+D header analysis):
#   TEX0: TBP0=0, TBW=4, PSM=PSMT4(0x14), 256x256
#   Upload as PSMCT32: 128 pixels wide x 64 pixels tall = 32768 bytes
DBW_CT32 = 128        # PSMCT32 upload buffer width
BW_PSMT4 = 256        # PSMT4 buffer width = TBW * 64 = 4 * 64

# VRAM simulation
VRAM_SIZE = 4 * 1024 * 1024  # 4 MB PS2 GS VRAM

# ── Stat kanji replacement map ──
# Format: (sub_block, row, col) -> text_to_render
# Each kanji occupies one 16x16 cell.
# Palette: index 0 = most opaque (text), 15 = transparent (background)
STAT_PATCHES = {
    # Sub-block 1: STR and PIE components
    (1, 5, 10): "Str",    # 力
    (1, 3,  4): "Pie",    # 信
    (1, 6,  2): "",       # 仰 -> blank
    (1, 4,  0): "",       # 心 -> blank

    # Sub-block 2: INT, VIT, AGI, LCK components
    (2, 1,  7): "Int",    # 知
    (2, 12, 13): "",      # 恵 -> blank
    (2, 4,  6): "Agi",    # 敏
    (2, 12, 15): "",      # 捷 -> blank
    (2, 4, 14): "",       # 度 -> blank
    (2, 12, 14): "Vit",   # 生
    (2, 11,  8): "",      # 命 -> blank
    (2, 13,  0): "Lck",   # 幸
    (2, 13,  1): "",      # 運 -> blank
}


def load_font():
    """Find and load a suitable font for rendering stat abbreviations."""
    font_candidates = [
        ("C:/Windows/Fonts/arialbd.ttf", 9),
        ("C:/Windows/Fonts/arial.ttf", 10),
        ("C:/Windows/Fonts/consola.ttf", 9),
        ("C:/Windows/Fonts/cour.ttf", 9),
    ]
    for fp, sz in font_candidates:
        if os.path.exists(fp):
            font = ImageFont.truetype(fp, sz)
            print(f"  Using font: {fp} size {sz}")
            return font
    font = ImageFont.load_default()
    print("  Using default font")
    return font


def render_text_cell(text, font, cell_w=CELL_W, cell_h=CELL_H):
    """Render text centered in a cell.

    Returns 2D list [row][col] of palette indices.
    0 = fully opaque (text ink), 15 = transparent (background).
    """
    if not text:
        return [[15] * cell_w for _ in range(cell_h)]

    img = Image.new("L", (cell_w, cell_h), 0)
    draw = ImageDraw.Draw(img)
    bbox = font.getbbox(text)
    if bbox:
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        if tw <= cell_w:
            ox = (cell_w - tw) // 2 - bbox[0]
        else:
            ox = -bbox[0]
        oy = max(0, (cell_h - th) // 2) - bbox[1]
        draw.text((ox, oy), text, fill=255, font=font)

    pixels = img.load()
    result = []
    for py in range(cell_h):
        row = []
        for px in range(cell_w):
            v = pixels[px, py]
            # Map: white(255) -> 0 (opaque), black(0) -> 15 (transparent)
            game_val = 15 - min(v * 15 // 255, 15)
            row.append(game_val)
        result.append(row)
    return result


# ── VRAM simulation functions ──

def vram_upload_psmct32(vram, host_data, tbp_blocks, upload_w):
    """Upload host data to VRAM using PSMCT32 addressing.

    Args:
        vram: bytearray simulating GS VRAM
        host_data: raw pixel bytes from the file
        tbp_blocks: TBP0 in 256-byte block units
        upload_w: upload buffer width in PSMCT32 pixels
    """
    base = tbp_blocks * 256
    upload_h = len(host_data) // (upload_w * 4)
    for y in range(upload_h):
        for x in range(upload_w):
            off = (y * upload_w + x) * 4
            if off + 4 > len(host_data):
                return
            wa = _psmct32_word_addr(x, y, upload_w)
            vb = base + wa * 4
            if vb + 4 <= len(vram):
                vram[vb:vb + 4] = host_data[off:off + 4]


def vram_download_psmct32(vram, tbp_blocks, upload_w, data_size):
    """Download data from VRAM back to host format using PSMCT32 addressing.

    Args:
        vram: bytearray simulating GS VRAM
        tbp_blocks: TBP0 in 256-byte block units
        upload_w: upload buffer width in PSMCT32 pixels
        data_size: total bytes to download
    Returns:
        bytearray of host-format data
    """
    base = tbp_blocks * 256
    upload_h = data_size // (upload_w * 4)
    out = bytearray(data_size)
    for y in range(upload_h):
        for x in range(upload_w):
            wa = _psmct32_word_addr(x, y, upload_w)
            vb = base + wa * 4
            off = (y * upload_w + x) * 4
            if vb + 4 <= len(vram) and off + 4 <= data_size:
                out[off:off + 4] = vram[vb:vb + 4]
    return out


def vram_read_psmt4(vram, tbp_byte, u, v, bw):
    """Read a single PSMT4 pixel from VRAM."""
    nib = _psmt4_nibble_addr(u, v, bw)
    ba = tbp_byte + nib // 2
    if ba >= len(vram):
        return 0
    bv = vram[ba]
    return (bv >> 4) & 0xF if nib & 1 else bv & 0xF


def vram_write_psmt4(vram, tbp_byte, u, v, bw, value):
    """Write a single PSMT4 pixel to VRAM."""
    nib = _psmt4_nibble_addr(u, v, bw)
    ba = tbp_byte + nib // 2
    if ba >= len(vram):
        return
    bv = vram[ba]
    if nib & 1:
        vram[ba] = (bv & 0x0F) | ((value & 0xF) << 4)
    else:
        vram[ba] = (bv & 0xF0) | (value & 0xF)


def patch_sub_block_vram(pixel_data, patches, font, sub_idx):
    """Patch a sub-block's pixel data using VRAM simulation.

    1. Upload host data to VRAM as PSMCT32 at TBP0=0
    2. For each patch: clear and write English text at PSMT4 cell coords
    3. Download from VRAM back to PSMCT32 host format

    Args:
        pixel_data: raw 32768 bytes of swizzled PSMT4 pixel data
        patches: dict of {(row, col): text} for this sub-block
        font: PIL font for rendering
        sub_idx: sub-block index (for logging)
    Returns:
        (patched_pixel_data, num_edits)
    """
    # TBP0=0 (all sub-blocks use TBP0=0 in their TEX0 register)
    tbp0_blocks = 0
    tbp0_byte = tbp0_blocks * 256

    # Allocate VRAM and upload
    vram = bytearray(VRAM_SIZE)
    vram_upload_psmct32(vram, pixel_data, tbp0_blocks, DBW_CT32)

    total_edits = 0

    for (row, col), text in sorted(patches.items()):
        # Cell pixel coordinates in PSMT4 texture space
        x0 = col * CELL_W
        y0 = row * CELL_H
        label = f"({row},{col})"

        # Count original non-zero (ink) pixels for logging
        orig_ink = 0
        for dy in range(CELL_H):
            for dx in range(CELL_W):
                val = vram_read_psmt4(vram, tbp0_byte, x0 + dx, y0 + dy, BW_PSMT4)
                if val < 15:
                    orig_ink += 1

        # Clear the cell (set all to transparent=15)
        for dy in range(CELL_H):
            for dx in range(CELL_W):
                vram_write_psmt4(vram, tbp0_byte, x0 + dx, y0 + dy, BW_PSMT4, 15)

        # Render and write English text
        cell_pixels = render_text_cell(text, font)
        edits = 0
        for dy in range(CELL_H):
            for dx in range(CELL_W):
                val = cell_pixels[dy][dx]
                if val < 15:  # Only write non-transparent pixels
                    vram_write_psmt4(vram, tbp0_byte, x0 + dx, y0 + dy, BW_PSMT4, val)
                    edits += 1

        total_edits += edits
        if text:
            print(f"    {label}: render '{text}' (orig_ink={orig_ink}, written={edits})")
        else:
            print(f"    {label}: blank (orig_ink={orig_ink})")

    # Download patched data back to host format
    patched = vram_download_psmct32(vram, tbp0_blocks, DBW_CT32, len(pixel_data))
    return bytes(patched), total_edits


def save_preview(pixel_data, path, sub_idx):
    """Save a deswizzled preview PNG of the sub-block."""
    linear = deswizzle_psmt4(pixel_data, TEX_W, TEX_H,
                              bw_psmt4=BW_PSMT4, dbw_ct32=DBW_CT32)
    img = Image.new("L", (TEX_W, TEX_H))
    for i, p in enumerate(linear[:TEX_W * TEX_H]):
        # Palette: 0=opaque(white text), 15=transparent(black bg)
        img.putpixel((i % TEX_W, i // TEX_W), 255 - p * 17)
    img.save(path)
    return img


def main():
    print("=" * 60)
    print("  R2100 Stat Label Patcher (VRAM Simulation)")
    print("  Bypass deswizzle-edit-reswizzle; work in GS VRAM space")
    print("=" * 60)
    print()

    # ── Read R2100 from PACKDATA.DIG ──
    print(f"Reading R2100 from {DIG_PATH}...")
    with open(DIG_PATH, "rb") as f:
        toc_data = f.read(TOC_ENTRIES * 12)
        so, sc, tc = struct.unpack_from("<III", toc_data, R2100_TOC_INDEX * 12)
        byte_off = so * SECTOR
        byte_size = sc * SECTOR

        print(f"  TOC: sector_offset=0x{so:X}, sector_count={sc}, type={tc}")
        print(f"  Byte offset: {byte_off}, size: {byte_size}")

        f.seek(byte_off)
        r2100 = bytearray(f.read(byte_size))
        assert len(r2100) == byte_size, f"Short read: {len(r2100)} < {byte_size}"

    # ── Parse descriptor table ──
    print("\n  Descriptor table:")
    sub_entries = []
    for i in range(NUM_SUBS):
        sub_idx, sub_size, data_off, pad = struct.unpack_from("<IIII", r2100, i * 16)
        print(f"    Sub {i}: size=0x{sub_size:X}, offset=0x{data_off:X}")
        assert sub_size == SUB_SIZE, f"Unexpected sub-block size: {sub_size}"
        sub_entries.append((sub_idx, sub_size, data_off))

    # ── Load font ──
    font = load_font()

    # ── Process each sub-block ──
    patches_applied = 0
    for blk in range(NUM_SUBS):
        sub_idx, sub_size, data_off = sub_entries[blk]
        sub_data = r2100[data_off:data_off + sub_size]

        # Split: header | pixels | tail
        header = sub_data[:HDR_SIZE]
        pixel_raw = sub_data[HDR_SIZE:HDR_SIZE + PIXEL_SIZE]
        tail = sub_data[HDR_SIZE + PIXEL_SIZE:]

        assert len(pixel_raw) == PIXEL_SIZE
        assert len(tail) == TAIL_SIZE

        # Collect patches for this sub-block
        sub_patches = {(r, c): txt for (sb, r, c), txt in STAT_PATCHES.items() if sb == blk}
        if not sub_patches:
            continue

        print(f"\n  Sub-block {blk}: {len(sub_patches)} patches (VRAM simulation)")

        # Patch using VRAM simulation
        patched_pixels, edits = patch_sub_block_vram(
            bytes(pixel_raw), sub_patches, font, blk
        )
        patches_applied += len(sub_patches)
        print(f"    Total pixel edits: {edits}")

        # Verify: round-trip the original to make sure we can compare
        # Deswizzle the patched result and save preview
        preview_path = os.path.join(PREVIEW_DIR, f"r2100_sub{blk}_vram_patched.png")
        save_preview(patched_pixels, preview_path, blk)
        print(f"    Preview: {preview_path}")

        # Verify patched data is same size
        assert len(patched_pixels) == PIXEL_SIZE, \
            f"Patched pixel size mismatch: {len(patched_pixels)} != {PIXEL_SIZE}"

        # Check that unmodified areas are preserved
        # (upload->download round-trip for unpatched bytes)
        orig_rt = patch_sub_block_vram.__module__  # just a dummy -- let's do a real check
        vram_check = bytearray(VRAM_SIZE)
        vram_upload_psmct32(vram_check, bytes(pixel_raw), 0, DBW_CT32)
        orig_roundtrip = vram_download_psmct32(vram_check, 0, DBW_CT32, PIXEL_SIZE)
        rt_mismatches = sum(1 for a, b in zip(pixel_raw, orig_roundtrip) if a != b)
        if rt_mismatches == 0:
            print(f"    VRAM upload/download round-trip: PASS")
        else:
            print(f"    VRAM upload/download round-trip: FAIL ({rt_mismatches} mismatches)")

        # Reassemble sub-block
        new_sub = bytes(header) + patched_pixels + bytes(tail)
        assert len(new_sub) == SUB_SIZE

        # Write back into r2100
        r2100[data_off:data_off + SUB_SIZE] = new_sub

    # ── Write output ──
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "wb") as f:
        f.write(r2100)

    print(f"\n  Total patches applied: {patches_applied}")
    print(f"  Output: {OUTPUT_PATH} ({len(r2100)} bytes)")
    print("\n" + "=" * 60)
    print("DONE!")
    print("=" * 60)


if __name__ == "__main__":
    main()
