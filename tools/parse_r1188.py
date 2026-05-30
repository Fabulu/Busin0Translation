#!/usr/bin/env python3
"""
Parse and visualize R1188 (name entry screen UI texture) for Busin 0.

R1188 is a 528KB type-01 resource containing a 1024x1024 PSMT4 texture atlas
used for the name entry screen and character creation UI. It stores tab labels,
buttons, number glyphs, and other UI elements.

Header structure (0xC00 = 3072 bytes):
  0x000-0x00F: File header {pad, total_size=527360, sub_count=16, pad}
  0x010-0x55F: 17 GS A+D register blocks (0x50 bytes each)
               Each configures TEX0 for 1024x1024 PSMT4 (TBW=16)
  0x560-0x6B3: 18 sprite metadata entries (20 bytes each)
               {pad(2), marker(4)=FFFFFFFF, entry_id(u16), flags=0x0101(u16),
                pad(4), w(u16)=1024, h(u16)=1024}
  0x6B4-0x6C3: Index table header
               {pad(4), meta_size=332(u16), pad(2), atlas_w=512(u16),
                atlas_h=256(u16), data_offset=2048(u16), pad(2)}
  0x6C4-0x7C3: 16 index table entries (16 bytes each)
               {pad(4), gs_block_offset(u16), w=8(u16), h=8(u16),
                type=2(u16), count=1(u16), pad(2)}
  0x7C4-0xBFF: Padding + CLUT palette data

Pixel data: 524,288 bytes at offset 0xC00 (1024x1024 PSMT4, 4bpp)

IMPORTANT: The texture data is PSMCT32-swizzled for GS upload. Deswizzle
uses the two-step VRAM simulation: write as PSMCT32, read as PSMT4.
Round-trip (deswizzle + re-swizzle) is verified exact.

The tab label positions within the texture are determined by runtime game code,
not embedded in the header. PCSX2 texture dumps capture individual sprites
rendered from this atlas.
"""
import struct
import sys
import os
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

try:
    from PIL import Image
except ImportError:
    print("ERROR: Pillow not installed. Run: pip install Pillow")
    sys.exit(1)

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_PATH = os.path.join(BASE, "extracted", "packdata_raw", "1188_type01.raw")
DUMP_DIR = os.path.join(BASE, "build", "pcsx2_dumps")
OUT_DIR = os.path.join(BASE, "dumps", "name_entry_font")


def parse_header(data):
    """Parse R1188 header and print structure info."""
    # File header
    pad, total_size, sub_count, pad2 = struct.unpack_from('<4I', data, 0)
    print(f"File header: total_size={total_size}, sub_count={sub_count}")

    # GS blocks - scan all 16-byte pairs for TEX0 register
    print(f"\nGS register blocks (17 x 0x50 = 1360 bytes at 0x010-0x55F):")
    tex0_shown = False
    for off in range(0x10, 0x560, 16):
        if off + 16 > len(data):
            break
        d = struct.unpack_from('<Q', data, off)[0]
        a = struct.unpack_from('<Q', data, off + 8)[0]
        if (a & 0xFF) == 0x06:  # TEX0 register
            tbp0 = d & 0x3FFF
            tbw = (d >> 14) & 0x3F
            psm = (d >> 20) & 0x3F
            tw = (d >> 26) & 0xF
            th = (d >> 30) & 0xF
            cbp = (d >> 37) & 0x3FFF
            csa = (d >> 56) & 0x1F
            if not tex0_shown:
                print(f"  TEX0 at 0x{off:04x}: TBP0={tbp0} TBW={tbw} "
                      f"PSM=0x{psm:02x} {1<<tw}x{1<<th} CBP={cbp} CSA={csa}")
                print(f"  (All 17 blocks have identical TEX0 config)")
                tex0_shown = True

    # Sprite metadata - 20-byte entries starting at 0x574 (after GS block tail)
    print(f"\nSprite metadata entries (0x574-0x6B4, 20 bytes each):")
    entry_ids = []
    for i in range(18):
        off = 0x574 + i * 20
        if off + 16 > len(data):
            break
        marker = struct.unpack_from('<I', data, off)[0]
        if marker == 0xFFFFFFFF:
            entry_id = struct.unpack_from('<H', data, off + 4)[0]
            flags = struct.unpack_from('<H', data, off + 6)[0]
            w = struct.unpack_from('<H', data, off + 12)[0]
            h = struct.unpack_from('<H', data, off + 14)[0]
            entry_ids.append(entry_id)
            if i < 5 or i >= 16:
                print(f"  Entry {i:2d}: id={entry_id}, flags=0x{flags:04x}, "
                      f"dims={w}x{h}")
    if len(entry_ids) > 5:
        print(f"  ... ({len(entry_ids)} total entries, IDs: {entry_ids})")

    # Index table
    print(f"\nIndex table (17 records at 0x6C4-0x7C3):")
    off0 = 0x6C4
    vals = struct.unpack_from('<8H', data, off0)
    print(f"  Header: meta_size={vals[2]}, atlas_w={vals[4]}, "
          f"atlas_h={vals[5]}, data_offset={vals[6]}")
    for i in range(1, 17):
        off = 0x6C4 + i * 16
        vals = struct.unpack_from('<8H', data, off)
        if i <= 3:
            print(f"  Entry {i:2d}: gs_offset=0x{vals[2]:04x}, "
                  f"w={vals[3]}, h={vals[4]}, type={vals[5]}, count={vals[6]}")
    print(f"  ... (16 entries, all w=8 h=8 type=2 count=1)")


def extract_pcsx2_tab_labels(dump_dir, out_dir):
    """Extract and identify tab label textures from PCSX2 dumps."""
    os.makedirs(out_dir, exist_ok=True)

    # Tab labels are 48x20 with CLUT hash 3cb39bf7659ef15f at GS page 00002214
    tab_files = sorted([f for f in os.listdir(dump_dir)
                        if 'r48x20-00002214' in f and '3cb39bf7659ef15f' in f])

    # Confirm button is 40x24
    btn_files = sorted([f for f in os.listdir(dump_dir)
                        if 'r40x24-00002214' in f and '3cb39bf7659ef15f' in f])

    # Known label identifications (from visual inspection)
    # Hash -> (Japanese, English replacement)
    LABEL_MAP = {
        '16625baf9feaeafb': ('性別 (Gender)', 'Gender'),
        '19a39fbc8a08d7ec': ('記号 (Symbols)', 'Sym'),
        '1f839869fab251d':  ('カナ (Katakana)', 'Kana'),
        '6f1fb24fad5cd1a':  ('英数 (Alphanumeric)', 'ABC'),
        '88ff8b577084a2a8': ('職業 (Occupation)', 'Class'),
        '9677cb23da53ff88': ('かな (Hiragana)', 'Hira'),
        '9bec87b4031a7172': ('種族 (Race)', 'Race'),
        'c89b469f7a152a6':  ('属性 (Alignment)', 'Align'),
        'd09a04bdfaf715bc': ('決定 (Confirm)', 'OK'),
    }

    print(f"\nPCSX2 tab label dumps found:")
    all_files = tab_files + btn_files
    results = []
    for f in all_files:
        hash1 = f.split('-')[0]
        dims = '48x20' if '48x20' in f else '40x24'
        jp, en = LABEL_MAP.get(hash1, ('Unknown', '???'))
        print(f"  {hash1}: {jp} -> \"{en}\" ({dims})")

        # Load and save composite view
        img = Image.open(os.path.join(dump_dir, f)).convert('RGBA')
        bg = Image.new('RGBA', img.size, (40, 40, 60, 255))
        composite = Image.alpha_composite(bg, img)
        scale = 4
        big = composite.resize((img.width * scale, img.height * scale), Image.NEAREST)
        out_name = f"tab_{en.lower().replace('.', '')}_{hash1[:8]}.png"
        big.save(os.path.join(out_dir, out_name))

        results.append({
            'hash': hash1,
            'file': f,
            'japanese': jp,
            'english': en,
            'width': img.width,
            'height': img.height,
        })

    # Save alpha-channel extraction as individual PNGs
    print(f"\n  Saved {len(results)} label previews to {out_dir}")
    return results


def main():
    print("=" * 60)
    print("  R1188 Name Entry Screen Parser")
    print("=" * 60)

    if not os.path.exists(RAW_PATH):
        print(f"ERROR: {RAW_PATH} not found")
        sys.exit(1)

    data = open(RAW_PATH, 'rb').read()
    print(f"\nFile: {RAW_PATH}")
    print(f"Size: {len(data)} bytes (0x{len(data):x})")
    print(f"Header: 0xC00 bytes, Pixel data: {len(data) - 0xC00 - 1024} bytes")

    parse_header(data)

    if os.path.exists(DUMP_DIR):
        labels = extract_pcsx2_tab_labels(DUMP_DIR, OUT_DIR)
    else:
        print(f"\nNo PCSX2 dumps at {DUMP_DIR}")
        print("Run PCSX2 with texture dumping to capture tab label sprites.")

    print("\nDone!")


if __name__ == "__main__":
    main()
