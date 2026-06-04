#!/usr/bin/env python3
"""
R1188 Glyph Position Finder - VRAM-based mapping for all cell types.

KEY FINDING: The deswizzled 1024x1024 atlas and the cell rendering use DIFFERENT
PSMT4 buffer widths (TBW=16 vs TBW=4). This means a cell's pixels are SCATTERED
across the deswizzled atlas. There is NO simple rectangular region in the atlas
that corresponds to a single cell.

CORRECT PATCHING APPROACH: Write directly to VRAM at each cell's absolute VRAM
address, exactly as patch_r1188_comprehensive.py does. The cell's U,V fields are
pixel coordinates in the PSMT4 readback from the cell's VRAM block address.

This script:
1. Reads cell data from the EXE for all stat/tab/sidebar labels
2. Renders each cell from the 4MB VRAM buffer (showing what the GS actually sees)
3. Outputs the VRAM-based mapping info needed for patching
"""
import sys
import os
import struct
import json

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "tools"))

from psmt4_deswizzle import (
    deswizzle_psmt4, _psmt4_nibble_addr, _psmct32_word_addr,
    make_rgba_image_4bit
)

try:
    from PIL import Image
except ImportError:
    print("ERROR: Pillow not installed")
    sys.exit(1)

# ---- Constants (same as patch_r1188_comprehensive.py) ----
BIN_PATH = os.path.join(BASE, "extracted", "packdata_resources", "1188_type01.bin")
RAW_PATH = os.path.join(BASE, "extracted", "packdata_raw", "1188_type01.raw")
EXE_PATH = os.path.join(BASE, "extracted", "SLPM_653.78")
DEBUG_DIR = os.path.join(BASE, "build", "textures_to_edit")

TEX_W, TEX_H = 1024, 1024
HEADER_BIN, HEADER_RAW = 0xC00, 0xC10
DBW_CT32 = 512

ATLAS_TBP = 0x2840       # GS TBP0 for upload (256-byte blocks)
VRAM_BLOCK_UNIT = 64      # Cell vram_blk values are in 64-byte units
GLYPH_TBW = 128           # Any TBW >= 128 works for small U,V (<128)
VRAM_SIZE = 4 * 1024 * 1024

# EXE offsets
PAGE_TABLE_OFF = 0x3DB180
EXE_VA_BASE = 0x100000 - 0x80

# ---- Cell definitions from EXE ----
# Stat label glyphs (individual kanji composing stat names)
STAT_GLYPH_IDS = {
    346: ("STR",      "Strength", "力"),
    535: ("INT1",     "IQ",       "知"),
    717: ("INT2",     "IQ",       "恵"),
    308: ("PIE1",     "Piety",    "信"),
    354: ("PIE2",     "Piety",    "仰"),
    320: ("PIE3",     "Piety",    "心"),
    718: ("VIT1",     "Vitality", "生"),
    696: ("VIT2",     "Vitality", "命"),
    582: ("AGI1",     "Agility",  "敏"),
    719: ("AGI2",     "Agility",  "捷"),
    590: ("AGI3",     "Agi/Luck", "度"),
    720: ("LCK1",     "Luck",     "幸"),
    721: ("LCK2",     "Luck",     "運"),
}

TAB_GLYPH_IDS = {
    0x1900: ("Kana",   "カナ"),
    0x1901: ("Hira",   "かな"),
    0x1902: ("ABC",    "英数"),
    0x1903: ("Sym",    "記号"),
    0x1905: ("OK",     "決定"),
    0x1906: ("M", "男名"),
    0x1907: ("F", "女名"),
    0x1908: ("Delete", "削除"),
    0x1909: ("Clear",  "全消"),
}

SIDEBAR_GLYPH_IDS = {
    511: ("Gender1", "Gender", "性"),
    512: ("Gender2", "Gender", "別"),
    504: ("Class1",  "Class",  "職"),
    517: ("Class2",  "Class",  "業"),
    513: ("Race1",   "Race",   "種"),
    514: ("Race2",   "Race",   "族"),
    515: ("Align1",  "Align",  "属"),
    516: ("Align2",  "Align",  "性"),
}


def read_cell_data(exe_data, glyph_id):
    page = glyph_id >> 8
    cell = glyph_id & 0xFF
    off = PAGE_TABLE_OFF + page * 8
    desc_idx, cell_ptr_va = struct.unpack_from('<II', exe_data, off)
    cell_ptr_file = cell_ptr_va - EXE_VA_BASE
    entry_off = cell_ptr_file + cell * 8
    u, v, w, flag = struct.unpack_from('BBBB', exe_data, entry_off)
    vram_blk, gs_cfg = struct.unpack_from('<HH', exe_data, entry_off + 4)
    return {'u': u, 'v': v, 'w': w, 'flag': flag,
            'vram_blk': vram_blk, 'gs_cfg': gs_cfg, 'desc_idx': desc_idx}


def build_vram(pixel_data):
    """Upload R1188 to 4MB VRAM buffer at ATLAS_TBP."""
    vram = bytearray(VRAM_SIZE)
    base = ATLAS_TBP * 256
    upload_w = DBW_CT32
    upload_h = len(pixel_data) // (upload_w * 4)
    for y in range(upload_h):
        for x in range(upload_w):
            off = (y * upload_w + x) * 4
            if off + 4 > len(pixel_data):
                return vram
            wa = _psmct32_word_addr(x, y, upload_w)
            vb = base + wa * 4
            if vb + 4 <= len(vram):
                vram[vb:vb+4] = pixel_data[off:off+4]
    return vram


def read_psmt4(vram, tbp_byte, u, v, tbw=GLYPH_TBW):
    nib = _psmt4_nibble_addr(u, v, tbw)
    ba = tbp_byte + nib // 2
    if ba >= len(vram):
        return 0
    bv = vram[ba]
    return (bv >> 4) & 0xF if nib & 1 else bv & 0xF


def render_cell(vram, cell, render_w, render_h):
    """Render a cell by reading PSMT4 pixels from VRAM."""
    tbp_byte = cell['vram_blk'] * VRAM_BLOCK_UNIT
    u, v = cell['u'], cell['v']
    img = Image.new('L', (render_w, render_h), 0)
    nonzero = 0
    for dy in range(render_h):
        for dx in range(render_w):
            val = read_psmt4(vram, tbp_byte, u + dx, v + dy)
            img.putpixel((dx, dy), val * 17)
            if val > 0:
                nonzero += 1
    return img, nonzero


def main():
    print("=" * 60)
    print("  R1188 Glyph Position Finder (VRAM simulation)")
    print("=" * 60)

    # Load sources
    src_path = BIN_PATH if os.path.exists(BIN_PATH) else RAW_PATH
    header_size = HEADER_BIN if src_path == BIN_PATH else HEADER_RAW
    data = open(src_path, 'rb').read()
    pixel_data = data[header_size:header_size + TEX_W * TEX_H // 2]
    print(f"  R1188: {src_path}")

    exe_data = open(EXE_PATH, 'rb').read()
    print(f"  EXE: {EXE_PATH}")

    # Build VRAM
    print("  Building 4MB VRAM buffer (upload at TBP0=0x{:04X})...".format(ATLAS_TBP))
    vram = build_vram(pixel_data)

    # Deswizzle for atlas PNG
    print("  Deswizzling 1024x1024 PSMT4...")
    linear = deswizzle_psmt4(pixel_data, TEX_W, TEX_H,
                              bw_psmt4=TEX_W, dbw_ct32=DBW_CT32)

    os.makedirs(DEBUG_DIR, exist_ok=True)
    palette = bytearray(64)
    for i in range(16):
        v = i * 17
        palette[i*4:i*4+4] = bytes([v, v, v, 128])
    out_png = os.path.join(DEBUG_DIR, "R1188_original_deswizzled.png")
    img_full = make_rgba_image_4bit(linear, palette, TEX_W, TEX_H)
    img_full.save(out_png)
    print(f"  Saved: {out_png}")

    results = {}

    # ---- Process stat labels (each is a single kanji, ~20x20) ----
    print("\n  === STAT LABEL GLYPHS (20x20 per kanji) ===")
    print("  These are individual kanji cells read via PSMT4 at TBP=vram_blk*64")
    for gid, (label, stat_name, kanji) in sorted(STAT_GLYPH_IDS.items()):
        cell = read_cell_data(exe_data, gid)
        img, nz = render_cell(vram, cell, 20, 20)

        # Save debug image
        img_big = img.resize((80, 80), Image.NEAREST)
        img_big.save(os.path.join(DEBUG_DIR, f"R1188_stat_{label}_{gid}.png"))

        print(f"  {label:8s} glyph {gid:5d} {kanji}: "
              f"U={cell['u']}, V={cell['v']}, W={cell['w']}, "
              f"VRAM=0x{cell['vram_blk']:04X}, nonzero={nz}")

        results[f"stat_{label}"] = {
            "glyph_id": gid, "label": label, "stat_name": stat_name,
            "kanji": kanji,
            "cell_u": cell['u'], "cell_v": cell['v'],
            "cell_w": cell['w'], "cell_flag": cell['flag'],
            "vram_blk": cell['vram_blk'],
            "vram_byte": cell['vram_blk'] * VRAM_BLOCK_UNIT,
            "render_w": 20, "render_h": 20,
            "nonzero": nz,
            "note": "Patch via: _write_psmt4(vram, vram_blk*64, U+dx, V+dy, 128, val)"
        }

    # ---- Process tab labels (each is a pre-composed label, W=100 wide) ----
    print("\n  === TAB LABEL GLYPHS (100x20 per label) ===")
    print("  These are full-width pre-composed sprites (Japanese text)")
    for gid, (label, jp) in sorted(TAB_GLYPH_IDS.items()):
        cell = read_cell_data(exe_data, gid)
        img, nz = render_cell(vram, cell, 100, 20)

        img_big = img.resize((400, 80), Image.NEAREST)
        img_big.save(os.path.join(DEBUG_DIR, f"R1188_tab_{label}_0x{gid:04X}.png"))

        print(f"  {label:8s} glyph 0x{gid:04X} {jp}: "
              f"U={cell['u']}, V={cell['v']}, W={cell['w']}, "
              f"VRAM=0x{cell['vram_blk']:04X}, nonzero={nz}")

        results[f"tab_{label}"] = {
            "glyph_id": gid, "label": label, "japanese": jp,
            "cell_u": cell['u'], "cell_v": cell['v'],
            "cell_w": cell['w'], "cell_flag": cell['flag'],
            "vram_blk": cell['vram_blk'],
            "vram_byte": cell['vram_blk'] * VRAM_BLOCK_UNIT,
            "render_w": 100, "render_h": 20,
            "nonzero": nz,
            "note": "Patch via: _write_psmt4(vram, vram_blk*64, U+dx, V+dy, 128, val)"
        }

    # ---- Process sidebar labels (similar to stat, individual kanji) ----
    print("\n  === SIDEBAR GLYPHS (20x20 per kanji) ===")
    for gid, (label, side_name, kanji) in sorted(SIDEBAR_GLYPH_IDS.items()):
        cell = read_cell_data(exe_data, gid)
        img, nz = render_cell(vram, cell, 20, 20)

        img_big = img.resize((80, 80), Image.NEAREST)
        img_big.save(os.path.join(DEBUG_DIR, f"R1188_side_{label}_{gid}.png"))

        print(f"  {label:8s} glyph {gid:5d} {kanji}: "
              f"U={cell['u']}, V={cell['v']}, W={cell['w']}, "
              f"VRAM=0x{cell['vram_blk']:04X}, nonzero={nz}")

        results[f"side_{label}"] = {
            "glyph_id": gid, "label": label, "sidebar_name": side_name,
            "kanji": kanji,
            "cell_u": cell['u'], "cell_v": cell['v'],
            "cell_w": cell['w'], "cell_flag": cell['flag'],
            "vram_blk": cell['vram_blk'],
            "vram_byte": cell['vram_blk'] * VRAM_BLOCK_UNIT,
            "render_w": 20, "render_h": 20,
            "nonzero": nz,
            "note": "Patch via: _write_psmt4(vram, vram_blk*64, U+dx, V+dy, 128, val)"
        }

    # ---- Save results ----
    out_json = os.path.join(BASE, "data", "r1188_glyph_positions_v2.json")
    with open(out_json, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n  Results saved: {out_json}")

    # ---- Print patching reference ----
    print("\n  === PATCHING REFERENCE ===")
    print("  To patch a cell, use patch_r1188_comprehensive.py's VRAM approach:")
    print("    1. Upload R1188 to VRAM at TBP0=0x2840")
    print("    2. Write PSMT4 pixels at (vram_blk*64, U+dx, V+dy, tbw=128)")
    print("    3. Download back from VRAM")
    print()
    print("  STAT_GLYPHS = [")
    print("      # (label, eng_char, u, v, vram_block)")
    for key in sorted(results.keys()):
        if key.startswith("stat_"):
            info = results[key]
            print(f"      (\"{info['label']}\", \"?\", "
                  f"{info['cell_u']}, {info['cell_v']}, 0x{info['vram_blk']:04X}),")
    print("  ]")
    print()
    print("  TAB_GLYPHS = [")
    for key in sorted(results.keys()):
        if key.startswith("tab_"):
            info = results[key]
            print(f"      (\"{info['label']}\", \"?\", "
                  f"{info['cell_u']}, {info['cell_v']}, 0x{info['vram_blk']:04X}),  "
                  f"# {info.get('japanese', '')}")
    print("  ]")
    print()
    print("  SIDEBAR_GLYPHS = [")
    for key in sorted(results.keys()):
        if key.startswith("side_"):
            info = results[key]
            print(f"      (\"{info['label']}\", \"?\", "
                  f"{info['cell_u']}, {info['cell_v']}, 0x{info['vram_blk']:04X}),  "
                  f"# {info.get('kanji', '')}")
    print("  ]")

    print("\n  Done!")


if __name__ == "__main__":
    main()
