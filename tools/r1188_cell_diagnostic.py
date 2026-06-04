#!/usr/bin/env python3
"""
R1188 Cell Diagnostic Tool
==========================
Visually maps R1188 glyph cells for the 13 stat label kanji glyphs.

For each glyph ID, reads its cell data from the EXE's Cell Data Page Table,
converts VRAM_block to a pixel position in the deswizzled atlas, and extracts
the glyph at multiple cell sizes and BASE_VRAM offsets.

Output:
  build/textures_to_edit/R1188_glyph_{id}_{name}.png  (individual cells)
  build/textures_to_edit/R1188_stat_cells_composite.png (all 13 side by side)
  build/textures_to_edit/R1188_cell_size_comparison.png (size sweep)
  build/textures_to_edit/R1188_base_vram_comparison.png (base VRAM sweep)
"""
import sys
import os
import struct

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

from psmt4_deswizzle import deswizzle_psmt4, _psmt4_nibble_addr

# ---------------------------------------------------------------------------
# Paths & constants
# ---------------------------------------------------------------------------
RAW_PATH   = os.path.join(BASE, "extracted", "packdata_raw", "1188_type01.raw")
BIN_PATH   = os.path.join(BASE, "extracted", "packdata_resources", "1188_type01.bin")
EXE_PATH   = os.path.join(BASE, "extracted", "SLPM_653.78")
OUT_DIR    = os.path.join(BASE, "build", "textures_to_edit")

TEX_W      = 1024
TEX_H      = 1024
DBW_CT32   = 512
BW_PSMT4   = 1024
HEADER_RAW = 0xC10
HEADER_BIN = 0xC00

# Page table at file offset 0x3DB180: 50 entries x 8 bytes
PAGE_TABLE_OFFSET = 0x3DB180
PAGE_TABLE_COUNT  = 50

# VA base for the EXE (file offset = VA - 0x100000 + 0x80 ... but we use
# the known relationship: VA 0x4DB100 -> file 0x3DB180)
VA_TO_FILE_DELTA  = 0x3DB180 - 0x4DB100  # = -0x100080 + 0x100

# The 13 stat label glyph IDs and their kanji names
STAT_GLYPHS = [
    (346,  "STR_chikara"),   # 力
    (535,  "INT_chi"),       # 知
    (717,  "INT_e"),         # 恵
    (308,  "PIE_shin"),      # 信
    (354,  "PIE_kou"),       # 仰
    (320,  "PIE_kokoro"),    # 心
    (718,  "VIT_sei"),       # 生
    (696,  "VIT_mei"),       # 命
    (582,  "AGI_bin"),       # 敏
    (719,  "AGI_soku"),      # 速
    (590,  "AGI_LCK_do"),   # 度 (shared)
    (720,  "LCK_kou"),      # 幸
    (721,  "LCK_un"),       # 運
]

# BASE_VRAM candidates to test
BASE_VRAM_CANDIDATES = [
    (0xA000, "0xA000"),
    (0xA100, "0xA100_TBP0x2840"),
    (0xA140, "0xA140_current"),
]

# Cell sizes to test
CELL_SIZES = [16, 20, 24, 32]


def load_r1188():
    """Load and deswizzle R1188 atlas. Returns (linear_pixels, grayscale_palette)."""
    if os.path.exists(BIN_PATH):
        src_path = BIN_PATH
        header_size = HEADER_BIN
    else:
        src_path = RAW_PATH
        header_size = HEADER_RAW

    data = open(src_path, "rb").read()
    pixel_data = data[header_size : header_size + TEX_W * TEX_H // 2]
    print(f"  Loaded {src_path}: {len(data)} bytes, header={header_size:#x}")
    print(f"  Pixel data: {len(pixel_data)} bytes")

    print("  Deswizzling 1024x1024 PSMT4 (dbw_ct32=512)...")
    linear = deswizzle_psmt4(pixel_data, TEX_W, TEX_H,
                              bw_psmt4=BW_PSMT4, dbw_ct32=DBW_CT32)
    print(f"  Deswizzled: {len(linear)} pixels")

    # Grayscale palette for visualization
    palette = bytearray(64)
    for i in range(16):
        v = i * 17  # 0..255
        palette[i*4] = v
        palette[i*4+1] = v
        palette[i*4+2] = v
        palette[i*4+3] = 255

    return linear, palette


def read_page_table(exe_data):
    """Read the Cell Data Page Table from the EXE.
    Returns list of (desc_idx, cell_data_ptr_VA) for each page."""
    pages = []
    for i in range(PAGE_TABLE_COUNT):
        off = PAGE_TABLE_OFFSET + i * 8
        desc_idx, cell_ptr_va = struct.unpack_from("<II", exe_data, off)
        pages.append((desc_idx, cell_ptr_va))
    return pages


def va_to_file_offset(va):
    """Convert a virtual address to file offset in the EXE."""
    # Known: VA 0x4DB100 = file 0x3DB180
    # delta = file - VA = 0x3DB180 - 0x4DB100 = -0xFF_F80
    # Actually let's compute directly:
    return va + (0x3DB180 - 0x4DB100)


def read_cell_entry(exe_data, pages, glyph_id):
    """Read the cell entry for a glyph ID from the EXE.
    Returns dict with U, V, W, flag, vram_block, gs_config, and file_offset."""
    page = glyph_id >> 8
    cell = glyph_id & 0xFF

    if page >= len(pages):
        return None

    desc_idx, cell_ptr_va = pages[page]
    cell_file_off = va_to_file_offset(cell_ptr_va) + cell * 8

    if cell_file_off + 8 > len(exe_data):
        return None

    raw = exe_data[cell_file_off : cell_file_off + 8]
    u = raw[0]
    v = raw[1]
    w = raw[2]
    flag = raw[3]
    vram_block = struct.unpack_from("<H", raw, 4)[0]
    gs_config = struct.unpack_from("<H", raw, 6)[0]

    return {
        "page": page,
        "cell": cell,
        "desc_idx": desc_idx,
        "cell_ptr_va": cell_ptr_va,
        "cell_file_off": cell_file_off,
        "U": u,
        "V": v,
        "W": w,
        "flag": flag,
        "vram_block": vram_block,
        "gs_config": gs_config,
        "raw_hex": raw.hex(),
    }


def build_reverse_nibble_map():
    """Build reverse map: VRAM nibble address -> (atlas_x, atlas_y)."""
    print("  Building VRAM reverse lookup (this may take ~20s)...")
    reverse = {}
    for y in range(TEX_H):
        for x in range(TEX_W):
            nib = _psmt4_nibble_addr(x, y, BW_PSMT4)
            reverse[nib] = (x, y)
    print(f"  Reverse map: {len(reverse)} entries")
    return reverse


def cell_to_atlas_pos(u_cell, v_cell, vram_block, base_vram, reverse_map):
    """Map cell (U, V, VRAM_block) to atlas (x, y) using given BASE_VRAM."""
    local_nib = _psmt4_nibble_addr(u_cell, v_cell, 256)
    global_nib = (vram_block - base_vram) * 512 + local_nib
    return reverse_map.get(global_nib)


def extract_cell_region(linear, atlas_x, atlas_y, cell_w, cell_h,
                        u_cell, v_cell, vram_block, base_vram, reverse_map):
    """Extract a cell_w x cell_h pixel block from the atlas using VRAM mapping.

    For each pixel (dx, dy) in the cell, compute its atlas position via
    the nibble mapping. This handles swizzle boundary wrapping correctly.
    """
    pixels = []
    for dy in range(cell_h):
        row = []
        for dx in range(cell_w):
            local_nib = _psmt4_nibble_addr(u_cell + dx, v_cell + dy, 256)
            global_nib = (vram_block - base_vram) * 512 + local_nib
            pos = reverse_map.get(global_nib)
            if pos is not None:
                ax, ay = pos
                if 0 <= ax < TEX_W and 0 <= ay < TEX_H:
                    row.append(linear[ay * TEX_W + ax])
                else:
                    row.append(0)
            else:
                row.append(0)
        pixels.append(row)
    return pixels


def pixels_to_image(pixels, cell_w, cell_h, scale=4):
    """Convert pixel array (values 0-15) to a grayscale PIL Image, scaled up."""
    img = Image.new("L", (cell_w * scale, cell_h * scale), 0)
    for dy in range(cell_h):
        for dx in range(cell_w):
            v = pixels[dy][dx] * 17  # 0-15 -> 0-255
            for sy in range(scale):
                for sx in range(scale):
                    img.putpixel((dx * scale + sx, dy * scale + sy), v)
    return img


def get_font(size=12):
    """Get a font for labeling."""
    for name in [
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/consola.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
    ]:
        try:
            return ImageFont.truetype(name, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def main():
    print("=" * 60)
    print("R1188 Cell Diagnostic Tool")
    print("=" * 60)
    print()

    os.makedirs(OUT_DIR, exist_ok=True)

    # --- Load atlas ---
    print("[1] Loading R1188 atlas...")
    linear, palette = load_r1188()
    print()

    # --- Load EXE ---
    print("[2] Loading EXE and reading page table...")
    exe_data = open(EXE_PATH, "rb").read()
    pages = read_page_table(exe_data)
    print(f"  Page table: {len(pages)} entries at file offset {PAGE_TABLE_OFFSET:#x}")
    for i, (desc, ptr) in enumerate(pages):
        if ptr != 0:
            print(f"    Page {i:2d}: desc_idx={desc}, cell_data_ptr=VA {ptr:#010x} "
                  f"(file {va_to_file_offset(ptr):#010x})")
    print()

    # --- Read cell entries for all 13 stat glyphs ---
    print("[3] Reading cell entries for stat label glyphs...")
    cell_entries = []
    for glyph_id, name in STAT_GLYPHS:
        entry = read_cell_entry(exe_data, pages, glyph_id)
        if entry is None:
            print(f"  Glyph {glyph_id} ({name}): NOT FOUND")
            cell_entries.append(None)
            continue
        print(f"  Glyph {glyph_id:4d} ({name:16s}): page={entry['page']}, cell={entry['cell']:3d}, "
              f"U={entry['U']}, V={entry['V']}, W={entry['W']}, flag={entry['flag']}, "
              f"VRAM={entry['vram_block']:#06x}, gs={entry['gs_config']:#06x}, "
              f"raw={entry['raw_hex']}")
        cell_entries.append(entry)
    print()

    # --- Build reverse nibble map ---
    print("[4] Building reverse nibble map...")
    reverse_map = build_reverse_nibble_map()
    print()

    # --- For each BASE_VRAM candidate, compute atlas positions ---
    print("[5] Atlas position mapping for each BASE_VRAM candidate...")
    for base_vram, base_label in BASE_VRAM_CANDIDATES:
        print(f"\n  --- BASE_VRAM = {base_label} ---")
        for (glyph_id, name), entry in zip(STAT_GLYPHS, cell_entries):
            if entry is None:
                continue
            pos = cell_to_atlas_pos(entry["U"], entry["V"], entry["vram_block"],
                                     base_vram, reverse_map)
            if pos is not None:
                print(f"    Glyph {glyph_id:4d} ({name:16s}): atlas ({pos[0]:4d}, {pos[1]:4d})")
            else:
                print(f"    Glyph {glyph_id:4d} ({name:16s}): NO MAPPING (nibble not in atlas)")
    print()

    # --- Extract individual cells at 32x32 (default) with BASE_VRAM=0xA140 ---
    print("[6] Extracting individual 32x32 cells (BASE_VRAM=0xA140)...")
    default_base = 0xA140
    for (glyph_id, name), entry in zip(STAT_GLYPHS, cell_entries):
        if entry is None:
            continue
        pos = cell_to_atlas_pos(entry["U"], entry["V"], entry["vram_block"],
                                 default_base, reverse_map)
        if pos is None:
            print(f"  Glyph {glyph_id} ({name}): skipped (no atlas position)")
            continue
        pixels = extract_cell_region(linear, pos[0], pos[1], 32, 32,
                                      entry["U"], entry["V"], entry["vram_block"],
                                      default_base, reverse_map)
        img = pixels_to_image(pixels, 32, 32, scale=4)
        out_path = os.path.join(OUT_DIR, f"R1188_glyph_{glyph_id}_{name}.png")
        img.save(out_path)
        print(f"  Saved: {out_path}")
    print()

    # --- Composite: all 13 side by side at 32x32 ---
    print("[7] Creating composite image (all 13 stat glyphs, 32x32 each)...")
    scale = 4
    cell_sz = 32
    n = len(STAT_GLYPHS)
    label_h = 40
    comp_w = n * cell_sz * scale
    comp_h = cell_sz * scale + label_h
    composite = Image.new("RGB", (comp_w, comp_h), (30, 30, 30))
    draw = ImageDraw.Draw(composite)
    font = get_font(11)

    for i, ((glyph_id, name), entry) in enumerate(zip(STAT_GLYPHS, cell_entries)):
        x_off = i * cell_sz * scale
        if entry is None:
            continue
        pixels = extract_cell_region(linear, 0, 0, cell_sz, cell_sz,
                                      entry["U"], entry["V"], entry["vram_block"],
                                      default_base, reverse_map)
        cell_img = pixels_to_image(pixels, cell_sz, cell_sz, scale)
        composite.paste(cell_img, (x_off, 0))
        # Label
        label = f"{glyph_id}\n{name[:10]}"
        draw.text((x_off + 2, cell_sz * scale + 2), label, fill=(200, 200, 200), font=font)

    comp_path = os.path.join(OUT_DIR, "R1188_stat_cells_composite.png")
    composite.save(comp_path)
    print(f"  Saved: {comp_path}")
    print()

    # --- Cell size comparison ---
    print("[8] Cell size comparison (16, 20, 24, 32 px)...")
    n_sizes = len(CELL_SIZES)
    n_glyphs = len(STAT_GLYPHS)
    cs_scale = 3
    label_col_w = 100
    row_h = max(CELL_SIZES) * cs_scale + 5
    header_h = 30
    size_comp_w = label_col_w + n_glyphs * (max(CELL_SIZES) * cs_scale + 4)
    size_comp_h = header_h + n_sizes * (row_h + 5)
    size_comp = Image.new("RGB", (size_comp_w, size_comp_h), (20, 20, 20))
    size_draw = ImageDraw.Draw(size_comp)
    font_sm = get_font(10)

    # Column headers (glyph IDs)
    for j, (glyph_id, name) in enumerate(STAT_GLYPHS):
        x = label_col_w + j * (max(CELL_SIZES) * cs_scale + 4)
        size_draw.text((x, 2), str(glyph_id), fill=(180, 180, 255), font=font_sm)

    for row_i, csz in enumerate(CELL_SIZES):
        y_off = header_h + row_i * (row_h + 5)
        size_draw.text((4, y_off + 4), f"{csz}x{csz}px", fill=(255, 200, 100), font=font_sm)

        for j, ((glyph_id, name), entry) in enumerate(zip(STAT_GLYPHS, cell_entries)):
            if entry is None:
                continue
            x_off = label_col_w + j * (max(CELL_SIZES) * cs_scale + 4)
            pixels = extract_cell_region(linear, 0, 0, csz, csz,
                                          entry["U"], entry["V"], entry["vram_block"],
                                          default_base, reverse_map)
            cell_img = pixels_to_image(pixels, csz, csz, cs_scale)
            # Pad to uniform size
            padded = Image.new("L", (max(CELL_SIZES) * cs_scale, max(CELL_SIZES) * cs_scale), 0)
            padded.paste(cell_img, (0, 0))
            size_comp.paste(padded, (x_off, y_off))

    size_path = os.path.join(OUT_DIR, "R1188_cell_size_comparison.png")
    size_comp.save(size_path)
    print(f"  Saved: {size_path}")
    print()

    # --- BASE_VRAM comparison ---
    print("[9] BASE_VRAM comparison (3 candidates x 13 glyphs, 24x24 cells)...")
    bv_csz = 24
    bv_scale = 4
    n_bases = len(BASE_VRAM_CANDIDATES)
    bv_label_w = 160
    bv_cell_w = bv_csz * bv_scale + 4
    bv_w = bv_label_w + n_glyphs * bv_cell_w
    bv_row_h = bv_csz * bv_scale + 5
    bv_header_h = 30
    bv_h = bv_header_h + n_bases * (bv_row_h + 5)
    bv_comp = Image.new("RGB", (bv_w, bv_h), (20, 20, 20))
    bv_draw = ImageDraw.Draw(bv_comp)

    # Column headers
    for j, (glyph_id, name) in enumerate(STAT_GLYPHS):
        x = bv_label_w + j * bv_cell_w
        bv_draw.text((x, 2), str(glyph_id), fill=(180, 180, 255), font=font_sm)

    for row_i, (base_vram, base_label) in enumerate(BASE_VRAM_CANDIDATES):
        y_off = bv_header_h + row_i * (bv_row_h + 5)
        bv_draw.text((4, y_off + 4), base_label, fill=(255, 200, 100), font=font_sm)

        for j, ((glyph_id, name), entry) in enumerate(zip(STAT_GLYPHS, cell_entries)):
            if entry is None:
                continue
            x_off = bv_label_w + j * bv_cell_w
            pixels = extract_cell_region(linear, 0, 0, bv_csz, bv_csz,
                                          entry["U"], entry["V"], entry["vram_block"],
                                          base_vram, reverse_map)
            cell_img = pixels_to_image(pixels, bv_csz, bv_csz, bv_scale)
            bv_comp.paste(cell_img, (x_off, y_off))

    bv_path = os.path.join(OUT_DIR, "R1188_base_vram_comparison.png")
    bv_comp.save(bv_path)
    print(f"  Saved: {bv_path}")
    print()

    print("=" * 60)
    print("DONE. Check build/textures_to_edit/ for output images.")
    print("=" * 60)


if __name__ == "__main__":
    main()
