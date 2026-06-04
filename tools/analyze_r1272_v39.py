"""
Extract R1272 from v39 ISO, deswizzle, analyze every tile position,
and save a gridded PNG.
"""
import struct, os, sys, json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from psmt4_deswizzle import deswizzle_psmt4
from PIL import Image, ImageDraw, ImageFont

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ISO_PATH = os.path.join(BASE, "build", "BUSIN0_EN_v39_bw256_real.iso")
OUT_DIR = os.path.join(BASE, "build", "textures_to_edit")
os.makedirs(OUT_DIR, exist_ok=True)

SECTOR = 2048
TOC_ENTRIES = 2883
OUTLIER_INDICES = {1370, 2100}
TARGET_RID = 1272

# ---- Step 1: Find PACKDATA in ISO ----
print(f"Opening ISO: {ISO_PATH}")
iso_data = open(ISO_PATH, "rb").read()

# Read PVD at sector 16
pvd = iso_data[16*SECTOR : 17*SECTOR]
root_lba = struct.unpack_from('<I', pvd, 158)[0]
root_size = struct.unpack_from('<I', pvd, 166)[0]
root_dir = iso_data[root_lba*SECTOR : root_lba*SECTOR + root_size]

pack_lba = None
pos = 0
while pos < len(root_dir):
    rec_len = root_dir[pos]
    if rec_len == 0:
        break
    name_len = root_dir[pos + 32]
    name = root_dir[pos + 33:pos + 33 + name_len].decode('ascii', errors='replace')
    if 'PACKDATA' in name:
        pack_lba = struct.unpack_from('<I', root_dir, pos + 2)[0]
        pack_size = struct.unpack_from('<I', root_dir, pos + 10)[0]
        print(f"PACKDATA found: LBA={pack_lba}, size={pack_size:,} bytes")
        break
    pos += rec_len

if pack_lba is None:
    print("ERROR: PACKDATA not found in ISO")
    sys.exit(1)

pack_offset = pack_lba * SECTOR

# ---- Step 2: Read TOC entry 1272 ----
toc_data = iso_data[pack_offset : pack_offset + TOC_ENTRIES * 12]
toc = []
for i in range(TOC_ENTRIES):
    so, sc, tc = struct.unpack_from('<III', toc_data, i * 12)
    toc.append((so, sc, tc))

so, sc, tc = toc[TARGET_RID]
r_offset = pack_offset + so * SECTOR
r_size = sc * SECTOR
print(f"R{TARGET_RID}: sector_offset=0x{so:X}, sectors={sc}, type={tc}")
print(f"  File offset: 0x{r_offset:X}, size: {r_size} bytes")

r_data = iso_data[r_offset : r_offset + r_size]

# ---- Step 3: Parse R1272 structure ----
# Type-01 resource: has a sub-header with offset table
# For the font atlas bin: header=192 bytes, pixels=65536 bytes (256x512 PSMT4), palette=64 bytes
# But the raw file has a 16-byte outer container wrapping the .bin content
# Let's check the type code first
print(f"  Type code: {tc}")
print(f"  First 32 bytes: {r_data[:32].hex()}")

# Type-01 raw files have a 16-byte container header
# Then the .bin content starts
# .bin for R1272: 192-byte GIF header + 65536 pixel bytes + 64 palette bytes = 65792
# Total raw: 16 + 65792 = 65808... but may vary

# Let's find the actual structure by looking for the GIF/GS header pattern
# The GIF tag is typically at offset 0x10 in the raw
# Actually let's just try header=192, pixel_data starts at 192 or 208

# Check if there's a 16-byte container
# For type-01 raw: first 16 bytes are the sub-header with offsets
# Let's look at the sub-header
sub_header = struct.unpack_from('<IIII', r_data, 0)
print(f"  Sub-header: {sub_header}")

# Type-01 resources in extracted/packdata_resources are .bin files (container stripped)
# In the raw PACKDATA, type-01 has a 16-byte header
# The actual content starts at offset 16
# Then for R1272: 192-byte GIF header + 65536 pixel data + 64-byte palette
CONTAINER_HDR = 16
GIF_HDR = 192
TEX_W, TEX_H = 256, 512
PIXEL_BYTES = TEX_W * TEX_H // 2  # 65536
PALETTE_BYTES = 64

pixel_start = CONTAINER_HDR + GIF_HDR
pixel_data = r_data[pixel_start : pixel_start + PIXEL_BYTES]
palette_data = r_data[pixel_start + PIXEL_BYTES : pixel_start + PIXEL_BYTES + PALETTE_BYTES]

print(f"  Pixel data: {len(pixel_data)} bytes from offset 0x{pixel_start:X}")
print(f"  Palette data: {len(palette_data)} bytes")

# ---- Step 4: Deswizzle ----
print("Deswizzling PSMT4 (bw_psmt4=256, dbw_ct32=256)...")
pixels = deswizzle_psmt4(pixel_data, TEX_W, TEX_H, bw_psmt4=256, dbw_ct32=256)
print(f"  Got {len(pixels)} deswizzled pixels")

# ---- Step 5: Build visualization image ----
# Create grayscale image (invert: 0=opaque -> white text, 15=transparent -> black bg)
img = Image.new("L", (TEX_W, TEX_H), 0)
for y in range(TEX_H):
    for x in range(TEX_W):
        pv = pixels[y * TEX_W + x]
        # 0 = fully opaque text -> white (255)
        # 15 = transparent bg -> black (0)
        img.putpixel((x, y), (15 - pv) * 17)

# ---- Step 6: Analyze each tile ----
CELL_W, CELL_H = 12, 12
COLS = 21
ROWS = TEX_H // CELL_H  # 42
TOTAL_CELLS = COLS * ROWS  # 882

print(f"\nGrid: {COLS} cols x {ROWS} rows = {TOTAL_CELLS} cells")

# Load glyph table to know which positions have English chars
glyph_table = json.load(open(os.path.join(BASE, "data", "english_glyph_table.json"), encoding="utf-8"))
english_slots = set(glyph_table.values())

# Load menu_labels.csv to know which positions have menu tiles
menu_glyph_ids = set()
with open(os.path.join(BASE, "data", "menu_labels.csv"), encoding="utf-8") as f:
    import csv
    reader = csv.DictReader(f)
    for row in reader:
        g1 = row.get('glyph_id_1', '').strip()
        g2 = row.get('glyph_id_2', '').strip()
        if g1 and g1 != '0':
            try: menu_glyph_ids.add(int(g1))
            except: pass
        if g2 and g2 != '0':
            try: menu_glyph_ids.add(int(g2))
            except: pass

print(f"English glyph slots from glyph_table: {len(english_slots)}")
print(f"Menu glyph IDs from menu_labels.csv: {len(menu_glyph_ids)}")
print(f"  Menu IDs range: {min(menu_glyph_ids)}-{max(menu_glyph_ids)}")

# Analyze each cell
cell_data = {}  # glyph_id -> {'ink_count', 'category'}
empty_cells = []
english_cells = []
kanji_cells = []
patched_cells = []  # English or menu

for gid in range(TOTAL_CELLS):
    col = gid % COLS
    row = gid // COLS
    x0 = col * CELL_W
    y0 = row * CELL_H

    if x0 + CELL_W > TEX_W or y0 + CELL_H > TEX_H:
        cell_data[gid] = {'ink_count': 0, 'category': 'OUT_OF_BOUNDS'}
        continue

    # Count non-zero, non-15 pixels (actual content)
    ink_count = 0
    total_nonbg = 0
    for dy in range(CELL_H):
        for dx in range(CELL_W):
            pv = pixels[(y0 + dy) * TEX_W + (x0 + dx)]
            if pv != 15:  # not transparent
                total_nonbg += 1
            if pv != 0 and pv != 15:  # partial ink
                ink_count += 1
            if pv == 0:  # fully opaque
                total_nonbg += 0  # already counted above if != 15

    # Recount: any pixel that is NOT 15 (transparent bg) is "ink"
    ink = 0
    for dy in range(CELL_H):
        for dx in range(CELL_W):
            pv = pixels[(y0 + dy) * TEX_W + (x0 + dx)]
            if pv != 15:
                ink += 1

    # Categorize
    if ink == 0:
        cat = 'EMPTY'
        empty_cells.append(gid)
    elif gid in english_slots or gid in menu_glyph_ids:
        cat = 'ENGLISH'
        english_cells.append(gid)
    else:
        # Has content but not in our English/menu lists -> likely original kanji
        cat = 'KANJI'
        kanji_cells.append(gid)

    cell_data[gid] = {'ink_count': ink, 'category': cat}

# ---- Step 7: Report ----
print(f"\n{'='*60}")
print(f"R1272 v39 TILE ANALYSIS REPORT")
print(f"{'='*60}")
print(f"Total cells: {TOTAL_CELLS}")
print(f"  ENGLISH: {len(english_cells)}")
print(f"  KANJI:   {len(kanji_cells)}")
print(f"  EMPTY:   {len(empty_cells)}")

print(f"\n--- Positions 0-94 (ASCII range) ---")
ascii_english = [g for g in range(95) if cell_data.get(g, {}).get('category') == 'ENGLISH']
ascii_kanji = [g for g in range(95) if cell_data.get(g, {}).get('category') == 'KANJI']
ascii_empty = [g for g in range(95) if cell_data.get(g, {}).get('category') == 'EMPTY']
print(f"  English: {len(ascii_english)} / 95")
print(f"  Kanji:   {len(ascii_kanji)}")
print(f"  Empty:   {len(ascii_empty)}")
if ascii_kanji:
    print(f"  KANJI positions in ASCII range: {ascii_kanji}")
if ascii_empty:
    print(f"  EMPTY positions in ASCII range: {ascii_empty}")

print(f"\n--- Positions 95-682 (middle range) ---")
mid_english = [g for g in range(95, 683) if cell_data.get(g, {}).get('category') == 'ENGLISH']
mid_kanji = [g for g in range(95, 683) if cell_data.get(g, {}).get('category') == 'KANJI']
mid_empty = [g for g in range(95, 683) if cell_data.get(g, {}).get('category') == 'EMPTY']
print(f"  English: {len(mid_english)}")
print(f"  Kanji:   {len(mid_kanji)}")
print(f"  Empty:   {len(mid_empty)}")
if mid_english:
    print(f"  English positions: {mid_english}")

print(f"\n--- Positions 683-866 (menu tile range) ---")
menu_english = [g for g in range(683, 867) if cell_data.get(g, {}).get('category') == 'ENGLISH']
menu_kanji = [g for g in range(683, 867) if cell_data.get(g, {}).get('category') == 'KANJI']
menu_empty = [g for g in range(683, 867) if cell_data.get(g, {}).get('category') == 'EMPTY']
print(f"  English: {len(menu_english)}")
print(f"  Kanji:   {len(menu_kanji)}")
print(f"  Empty:   {len(menu_empty)}")
if menu_kanji:
    print(f"  KANJI positions in menu range: {menu_kanji}")

print(f"\n--- Positions 867-881 (tail range) ---")
tail_english = [g for g in range(867, TOTAL_CELLS) if cell_data.get(g, {}).get('category') == 'ENGLISH']
tail_kanji = [g for g in range(867, TOTAL_CELLS) if cell_data.get(g, {}).get('category') == 'KANJI']
tail_empty = [g for g in range(867, TOTAL_CELLS) if cell_data.get(g, {}).get('category') == 'EMPTY']
print(f"  English: {len(tail_english)}")
print(f"  Kanji:   {len(tail_kanji)}")
print(f"  Empty:   {len(tail_empty)}")

print(f"\n--- ALL kanji positions in 95-682 ---")
if mid_kanji:
    # Group into ranges for readability
    print(f"  Count: {len(mid_kanji)}")
    # Show first/last 20
    if len(mid_kanji) <= 60:
        for i, gid in enumerate(mid_kanji):
            ink = cell_data[gid]['ink_count']
            print(f"  [{gid:3d}] ink={ink:3d} (row={gid//COLS}, col={gid%COLS})")
    else:
        print(f"  First 30:")
        for gid in mid_kanji[:30]:
            ink = cell_data[gid]['ink_count']
            print(f"    [{gid:3d}] ink={ink:3d}")
        print(f"  ... ({len(mid_kanji) - 60} more) ...")
        print(f"  Last 30:")
        for gid in mid_kanji[-30:]:
            ink = cell_data[gid]['ink_count']
            print(f"    [{gid:3d}] ink={ink:3d}")
else:
    print("  NONE - all positions are English or empty!")

# ---- Step 8: Save gridded PNG ----
# Scale up 3x for visibility
SCALE = 3
grid_w = TEX_W * SCALE
grid_h = TEX_H * SCALE
grid_img = img.resize((grid_w, grid_h), Image.NEAREST).convert("RGB")
draw = ImageDraw.Draw(grid_img)

# Color-code cells by category
for gid in range(TOTAL_CELLS):
    col = gid % COLS
    row = gid // COLS
    x0 = col * CELL_W * SCALE
    y0 = row * CELL_H * SCALE

    cat = cell_data.get(gid, {}).get('category', 'EMPTY')
    if cat == 'ENGLISH':
        # Green tint on border
        color = (0, 200, 0)
    elif cat == 'KANJI':
        # Red tint on border
        color = (255, 60, 60)
    else:
        # Gray for empty
        color = (80, 80, 80)

    # Draw cell border
    draw.rectangle([x0, y0, x0 + CELL_W * SCALE - 1, y0 + CELL_H * SCALE - 1], outline=color)

# Save
out_path = os.path.join(OUT_DIR, "R1272_v39_gridded.png")
grid_img.save(out_path)
print(f"\nGridded PNG saved: {out_path}")
print(f"  Green borders = ENGLISH, Red borders = KANJI, Gray borders = EMPTY")

# Also save a 1x version for reference
out_path_1x = os.path.join(OUT_DIR, "R1272_v39_raw.png")
img.save(out_path_1x)
print(f"Raw PNG saved: {out_path_1x}")

print("\nDone!")
