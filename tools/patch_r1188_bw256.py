#!/usr/bin/env python3
"""
Step 3.7: R1188 stat label patches at bw_psmt4=256.

Reads the output of Step 3.6 (patch_r1188_comprehensive.py), patches stat
label kanji glyphs using VRAM simulation with PSMT4 tbw=256 (matching the
game's TBW=4 for glyph readback), and writes back to the same file.

The comprehensive patcher's Phase 4 uses GLYPH_TBW=128, which may produce
misaligned pixels when the game reads glyphs at TBW=4 (=256 PSMT4 pixels).
This script applies the same VRAM simulation technique but with tbw=256.

Architecture:
  1. Load the patched R1188 host data (PSMCT32 upload format)
  2. Upload to simulated VRAM using PSMCT32 addressing at ATLAS_TBP
  3. For each stat label kanji:
     a. Clear the 20x20 glyph area using PSMT4 addressing at glyph's TBP, tbw=256
     b. Render English letter and write pixels at the same PSMT4 addresses
  4. Download from VRAM back to PSMCT32 host format
  5. Write back to the same file (preserving header and sector alignment)
"""
import sys
import os

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("ERROR: Pillow not installed. Run: pip install Pillow")
    sys.exit(1)

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "tools"))

from psmt4_deswizzle import _psmt4_nibble_addr, _psmct32_word_addr

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
RAW_PATH = os.path.join(BASE, "build", "packdata_resources", "1188_type01.raw")
SECTOR = 2048
HEADER_SIZE = 0xC00 + 0x10   # 3072-byte GIF header + 16-byte outer container
TEX_W = 1024
TEX_H = 1024
PIXEL_BYTES = TEX_W * TEX_H // 2   # 524288

ATLAS_TBP = 0x2840            # GS TBP0 for R1188 upload (256-byte blocks)
DBW_CT32 = 512                 # PSMCT32 upload buffer width
GLYPH_TBW = 256               # PSMT4 buffer width for glyph readback (TBW=4)
VRAM_BLOCK_UNIT = 64           # Each vram_block = 64 bytes

GLYPH_W = 20
GLYPH_H = 20

VRAM_SIZE = 4 * 1024 * 1024   # PS2 GS VRAM = 4MB

# ---------------------------------------------------------------------------
# Stat label glyph definitions
#
# Each entry: (label, english_char, u_pixel, v_pixel, vram_block)
#
# The game reads these glyphs from VRAM using PSMT4 addressing:
#   TBP0 = vram_block (in 64-byte units)
#   TBW  = 4 (= 256 PSMT4 pixels)
#   pixel coords: (u_pixel, v_pixel) to (u_pixel+19, v_pixel+19)
#
# Shared glyphs:
#   力 (STR sole, VIT 3rd): both map to same VRAM bytes -> rendered as 'S'/'T'
#   度 (AGI 3rd, LCK 3rd): both map to same VRAM bytes -> rendered as 'I'
# ---------------------------------------------------------------------------
STAT_GLYPHS = [
    # STR = 力
    ("STR",   "S",  1, 60, 0xA450),
    # INT = 知 + 恵
    ("INT-1", "I",  1, 66, 0xA270),
    ("INT-2", "Q",  0, 84, 0xA480),
    # PIE = 信 + 仰 + 心
    ("PIE-1", "P",  0, 62, 0xA328),
    ("PIE-2", "I",  1, 67, 0xA490),
    ("PIE-3", "E",  0, 64, 0xA380),
    # VIT = 生 + 命 + 力(shared with STR)
    ("VIT-1", "V",  0, 85, 0xA7E8),
    ("VIT-2", "I",  4, 70, 0xA758),
    # AGI = 敏 + 速 + 度(shared with LCK)
    ("AGI-1", "A",  0, 74, 0xA3D0),
    ("AGI-2", "G",  0, 86, 0xA7F0),
    ("AGI-3", "I",  0, 82, 0xA410),
    # LCK = 幸 + 運 + 度(shared with AGI)
    ("LCK-1", "L",  0, 87, 0xA7F8),
    ("LCK-2", "C",  0, 88, 0xA800),
]


# ---------------------------------------------------------------------------
# Font rendering
# ---------------------------------------------------------------------------

def get_font(size=16):
    """Return a TrueType font for rendering into glyph cells."""
    for path in [
        "C:/Windows/Fonts/consola.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/tahoma.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]:
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def render_letter(letter, width, height, font_size=16):
    """Render a single letter as a 2D list of PSMT4 indices (0-15).

    Returns list[height][width] of integer palette indices.
    Index 0 = transparent, index 15 = max opacity.
    """
    img = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(img)
    font = get_font(font_size)

    bbox = draw.textbbox((0, 0), letter, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]

    # Shrink font if letter is too wide
    while tw > width - 1 and font_size > 8:
        font_size -= 1
        font = get_font(font_size)
        bbox = draw.textbbox((0, 0), letter, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]

    x = (width - tw) // 2 - bbox[0]
    y = (height - th) // 2 - bbox[1]
    draw.text((x, y), letter, fill=255, font=font)

    pixels = img.load()
    result = []
    for py in range(height):
        row = []
        for px in range(width):
            v = pixels[px, py]
            idx = round(v * 15 / 255)
            row.append(idx)
        result.append(row)
    return result


# ---------------------------------------------------------------------------
# VRAM simulation helpers
# ---------------------------------------------------------------------------

def vram_upload(vram, host_data, tbp_blocks, upload_w):
    """Upload host data to VRAM using PSMCT32 addressing."""
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


def vram_download(vram, tbp_blocks, upload_w, data_size):
    """Read host data back from VRAM using PSMCT32 addressing."""
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


def read_psmt4(vram, tbp_byte, u, v, tbw):
    """Read a single PSMT4 pixel from VRAM."""
    nib = _psmt4_nibble_addr(u, v, tbw)
    ba = tbp_byte + nib // 2
    if ba >= len(vram):
        return 0
    bv = vram[ba]
    return (bv >> 4) & 0xF if nib & 1 else bv & 0xF


def write_psmt4(vram, tbp_byte, u, v, tbw, value):
    """Write a single PSMT4 pixel to VRAM."""
    nib = _psmt4_nibble_addr(u, v, tbw)
    ba = tbp_byte + nib // 2
    if ba >= len(vram):
        return
    bv = vram[ba]
    if nib & 1:
        vram[ba] = (bv & 0x0F) | ((value & 0xF) << 4)
    else:
        vram[ba] = (bv & 0xF0) | (value & 0xF)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("  R1188 Stat Label Patcher (bw=256)")
    print("  Step 3.7: Patches after comprehensive patcher output")
    print("=" * 60)

    # ---- Load Step 3.6 output ----
    if not os.path.exists(RAW_PATH):
        print(f"  ERROR: {RAW_PATH} not found (run Step 3.6 first)")
        sys.exit(1)

    raw_data = open(RAW_PATH, "rb").read()
    header = raw_data[:HEADER_SIZE]
    pixel_data = raw_data[HEADER_SIZE:HEADER_SIZE + PIXEL_BYTES]

    if len(pixel_data) < PIXEL_BYTES:
        print(f"  ERROR: pixel data too short ({len(pixel_data)} < {PIXEL_BYTES})")
        sys.exit(1)

    print(f"  Input  : {RAW_PATH}")
    print(f"  Size   : {len(raw_data)} bytes (header={HEADER_SIZE}, pixels={len(pixel_data)})")

    # ---- Build VRAM ----
    print(f"  Uploading to VRAM at TBP=0x{ATLAS_TBP:04X} (dbw_ct32={DBW_CT32}) ...")
    vram = bytearray(VRAM_SIZE)
    host_data = bytearray(pixel_data)
    vram_upload(vram, host_data, ATLAS_TBP, DBW_CT32)

    # ---- Patch each stat label glyph ----
    total_edits = 0
    print(f"\n  Patching {len(STAT_GLYPHS)} stat label glyphs (tbw={GLYPH_TBW}) ...")
    print(f"  {'Label':8s} {'Eng':3s} {'(u,v)':8s} {'VRAM_blk':10s} {'Cleared':8s} {'Written':8s}")
    print(f"  {'-' * 55}")

    for label, eng_char, u, v, vram_block in STAT_GLYPHS:
        tbp_byte = vram_block * VRAM_BLOCK_UNIT

        # Count original non-zero pixels
        orig_nz = 0
        for dy in range(GLYPH_H):
            for dx in range(GLYPH_W):
                if read_psmt4(vram, tbp_byte, u + dx, v + dy, GLYPH_TBW) > 0:
                    orig_nz += 1

        # Clear the glyph area
        for dy in range(GLYPH_H):
            for dx in range(GLYPH_W):
                write_psmt4(vram, tbp_byte, u + dx, v + dy, GLYPH_TBW, 0)

        # Render and write English letter
        letter = render_letter(eng_char, GLYPH_W, GLYPH_H)
        edits = 0
        for dy in range(GLYPH_H):
            for dx in range(GLYPH_W):
                val = letter[dy][dx]
                if val > 0:
                    write_psmt4(vram, tbp_byte, u + dx, v + dy, GLYPH_TBW, val)
                    edits += 1

        total_edits += edits
        print(f"  {label:8s} '{eng_char}'  ({u:2d},{v:2d})  0x{vram_block:04X}     {orig_nz:5d}    {edits:5d}")

    # ---- Download patched host data ----
    print(f"\n  Downloading from VRAM ...")
    patched_host = vram_download(vram, ATLAS_TBP, DBW_CT32, len(host_data))

    # ---- Verify roundtrip ----
    # Re-upload and re-read each glyph to confirm pixels survived the roundtrip
    vram2 = bytearray(VRAM_SIZE)
    vram_upload(vram2, patched_host, ATLAS_TBP, DBW_CT32)

    rt_ok = True
    for label, eng_char, u, v, vram_block in STAT_GLYPHS:
        tbp_byte = vram_block * VRAM_BLOCK_UNIT
        for dy in range(GLYPH_H):
            for dx in range(GLYPH_W):
                v1 = read_psmt4(vram, tbp_byte, u + dx, v + dy, GLYPH_TBW)
                v2 = read_psmt4(vram2, tbp_byte, u + dx, v + dy, GLYPH_TBW)
                if v1 != v2:
                    rt_ok = False
                    break
            if not rt_ok:
                break
        if not rt_ok:
            break

    print(f"  Roundtrip verify: {'PASS' if rt_ok else 'FAIL'}")

    # ---- Write output ----
    out = bytearray(header) + patched_host

    # Pad to sector boundary
    remainder = len(out) % SECTOR
    if remainder:
        out += b"\x00" * (SECTOR - remainder)

    with open(RAW_PATH, "wb") as f:
        f.write(out)

    print(f"  Output : {RAW_PATH} ({len(out)} bytes, sector-aligned)")

    # ---- Save debug image ----
    debug_dir = os.path.join(BASE, "build", "textures_to_edit")
    os.makedirs(debug_dir, exist_ok=True)

    # Show what the glyphs look like when read back at tbw=256
    debug_path = os.path.join(debug_dir, "R1188_bw256_stat_glyphs.png")
    glyph_count = len(STAT_GLYPHS)
    cols = 5
    rows = (glyph_count + cols - 1) // cols
    margin = 4
    cell_w = GLYPH_W + margin
    cell_h = GLYPH_H + margin + 12  # extra for label
    img_w = cols * cell_w + margin
    img_h = rows * cell_h + margin

    img = Image.new("L", (img_w * 3, img_h * 3), 0)
    draw = ImageDraw.Draw(img)

    for idx, (label, eng_char, u, v, vram_block) in enumerate(STAT_GLYPHS):
        tbp_byte = vram_block * VRAM_BLOCK_UNIT
        col = idx % cols
        row = idx // cols
        ox = margin + col * cell_w
        oy = margin + row * cell_h

        for dy in range(GLYPH_H):
            for dx in range(GLYPH_W):
                val = read_psmt4(vram2, tbp_byte, u + dx, v + dy, GLYPH_TBW)
                # 3x zoom
                for sy in range(3):
                    for sx in range(3):
                        img.putpixel(((ox + dx) * 3 + sx, (oy + dy) * 3 + sy),
                                     val * 17)

    img.save(debug_path)
    print(f"  Debug  : {debug_path}")

    # ---- Summary ----
    print(f"\n{'=' * 60}")
    print(f"  SUMMARY")
    print(f"    Glyphs patched : {len(STAT_GLYPHS)}")
    print(f"    Pixel edits    : {total_edits}")
    print(f"    PSMT4 TBW      : {GLYPH_TBW} (game's TBW=4)")
    print(f"    Roundtrip      : {'PASS' if rt_ok else 'FAIL'}")
    print(f"{'=' * 60}")
    print("\nDone!")


if __name__ == "__main__":
    main()
