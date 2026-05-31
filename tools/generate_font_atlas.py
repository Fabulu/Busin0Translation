import sys, io, os, json, struct
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from PIL import Image, ImageFont, ImageDraw

# Config
ATLAS_W, ATLAS_H = 256, 540
CELL_W, CELL_H = 12, 12
COLS = 21
ROWS = ATLAS_H // CELL_H  # 45 rows -> 945 cells (IDs 0-944), covers up to glyph 931
ORIGINAL = "extracted/packdata_resources/1272_type01.bin"
OUTPUT_BIN = "build/english_font_atlas.bin"
OUTPUT_PNG = "build/english_font_atlas_preview.png"

os.makedirs("build", exist_ok=True)

# Load original header (192 bytes) and palette (last 64 bytes)
orig = open(ORIGINAL, "rb").read()
header = bytearray(orig[:192])
palette = orig[192:256]  # last 64 bytes
print(f"Original: {len(orig)} bytes, header={len(header)}, palette={len(palette)}")

# Patch TEX0 TH field if atlas extends beyond 512 pixels
# TEX0_1 register is at header offset 0x50 (8-byte value)
# TH is bits 30-33; TH=9 means 2^9=512, TH=10 means 2^10=1024
if ATLAS_H > 512:
    tex0 = struct.unpack_from('<Q', header, 0x50)[0]
    old_th = (tex0 >> 30) & 0xF
    new_th = 10  # 2^10 = 1024, enough for 540 rows
    tex0 = (tex0 & ~(0xF << 30)) | (new_th << 30)
    struct.pack_into('<Q', header, 0x50, tex0)
    print(f"  Patched TEX0 TH: {old_th} -> {new_th} (2^{new_th}={2**new_th} pixels)")
header = bytes(header)

# Load glyph table
glyph_table = json.load(open("data/english_glyph_table.json", encoding="utf-8"))

# Reverse: glyph_slot -> character
slot_to_char = {v: k for k, v in glyph_table.items()}
print(f"Glyph table: {len(glyph_table)} chars, {len(slot_to_char)} unique slots")

# Find a good font
font = None
for fp in ["C:/Windows/Fonts/consola.ttf", "C:/Windows/Fonts/arial.ttf", 
           "C:/Windows/Fonts/cour.ttf", "C:/Windows/Fonts/lucon.ttf"]:
    if os.path.exists(fp):
        font = ImageFont.truetype(fp, 10)
        print(f"Using font: {fp}")
        break
if font is None:
    font = ImageFont.load_default()
    print("Using default font")

# Create atlas image (white = transparent, black = opaque in preview)
atlas = Image.new("L", (ATLAS_W, ATLAS_H), 0)  # black background
draw = ImageDraw.Draw(atlas)

# Render each character in its glyph slot
for slot, char in slot_to_char.items():
    col = slot % COLS
    row = slot // COLS
    x = col * CELL_W
    y = row * CELL_H
    
    if x + CELL_W > ATLAS_W or y + CELL_H > ATLAS_H:
        continue
    
    # Render character centered in cell
    try:
        bbox = font.getbbox(char)
        if bbox:
            cw = bbox[2] - bbox[0]
            ch = bbox[3] - bbox[1]
            ox = x + max(0, (CELL_W - cw) // 2) - bbox[0]
            oy = y + max(0, (CELL_H - ch) // 2) - bbox[1]
            draw.text((ox, oy), char, fill=255, font=font)
    except:
        pass

# ---- MENU TILE INJECTION ----
# Render English menu labels into glyph slots 683-931
try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from render_menu_tiles import load_menu_tiles
    menu_tiles = load_menu_tiles()
    for glyph_id, tile_pixels in menu_tiles.items():
        col = glyph_id % COLS
        row = glyph_id // COLS
        x0 = col * CELL_W
        y0 = row * CELL_H
        if x0 + CELL_W > ATLAS_W or y0 + CELL_H > ATLAS_H:
            continue
        # Write grayscale pixels into the atlas image
        # tile_pixels are 0-255 (0=black/bg, 255=white/text) -- same as atlas convention
        for dy in range(CELL_H):
            for dx in range(CELL_W):
                val = tile_pixels[dy * CELL_W + dx]
                atlas.putpixel((x0 + dx, y0 + dy), val)
    print(f"  Injected {len(menu_tiles)} menu tiles into atlas")
except ImportError as e:
    print(f"  WARNING: render_menu_tiles not found ({e}), skipping menu tiles")
except Exception as e:
    print(f"  WARNING: menu tile injection failed: {e}")
# ---- END MENU TILE INJECTION ----

# Save preview
atlas.save(OUTPUT_PNG)
print(f"Preview saved: {OUTPUT_PNG}")

# Convert to game's 4bpp format
# Game format: 15 = transparent (background), 0 = fully opaque
# Our atlas: 0 = background (black), 255 = character (white)
# So invert and quantize to 4 bits

# The atlas is stored as pages of 128x128 at 128px width (linear, no swizzle)
# Each page: 128x128 pixels = 8192 4bpp bytes
# For 256x540: full pages cover 256x512 (8 pages), plus 28 extra rows in pages 8-9
# We allocate enough bytes for ceil(540/128)=5 page-rows x 2 columns = 10 pages
FULL_PAGE_ROWS = (ATLAS_H + 127) // 128  # ceil(540/128) = 5
TOTAL_PAGES = FULL_PAGE_ROWS * 2          # 10 pages
pixel_data_size = TOTAL_PAGES * 128 * 128 // 2  # 10 * 8192 = 81920 bytes at 4bpp
pixel_data = bytearray(pixel_data_size)

# Process each pixel
atlas_pixels = list(atlas.getdata())
for y in range(ATLAS_H):
    for x in range(ATLAS_W):
        # Get pixel value (0-255)
        val = atlas_pixels[y * ATLAS_W + x]

        # Convert: 255 (white/character) -> 0 (opaque), 0 (black/bg) -> 15 (transparent)
        game_val = 15 - min(val * 15 // 255, 15)

        # Calculate position in the linear 128-wide page layout
        # Pages are 128x128, arranged 2 columns x N rows
        page_col = x // 128
        page_row = y // 128
        page_idx = page_row * 2 + page_col
        local_x = x % 128
        local_y = y % 128

        # Linear position within the page
        pixel_offset = page_idx * 128 * 128 + local_y * 128 + local_x

        # Pack as 4bpp (2 pixels per byte, low nibble = first pixel)
        byte_offset = pixel_offset // 2
        if byte_offset < len(pixel_data):
            if pixel_offset % 2 == 0:
                pixel_data[byte_offset] = (pixel_data[byte_offset] & 0xF0) | (game_val & 0x0F)
            else:
                pixel_data[byte_offset] = (pixel_data[byte_offset] & 0x0F) | ((game_val & 0x0F) << 4)

# Trim trailing empty pages -- only keep data up to last non-empty byte
# But ensure we keep at least the original 65536 bytes for compatibility
min_size = 65536  # original 256x512 size
actual_size = max(min_size, pixel_data_size)
# Pad pixel_data to actual_size if needed (already >= min_size)

# Assemble: header + pixel data + palette
output = header + bytes(pixel_data[:actual_size]) + palette
print(f"Font atlas size: {len(output)} bytes (header={len(header)}, pixels={actual_size}, palette={len(palette)})")

with open(OUTPUT_BIN, "wb") as f:
    f.write(output)
print(f"Font atlas binary: {OUTPUT_BIN} ({len(output)} bytes)")
print("DONE!")
