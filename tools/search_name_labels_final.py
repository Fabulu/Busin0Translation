#!/usr/bin/env python3
"""Final summary of name entry screen label locations.

FINDINGS:
=========

Name Entry Screen Data Layout in EXE (SLPM_653.78):
---------------------------------------------------

1. PRESET NAMES (LE uint16 glyph sequences, FFFF terminated):
   0x3C93B0: エミーリア (female default name)
   0x3C93C0: リュート   (male default name)
   - These use MSG glyph map IDs

2. KANA CHARACTER GRID (LE uint16 per column, 6 columns):
   0x3C9A38-0x3C9D50: Grid of MSG glyph IDs arranged in columns:
     Col 0: hiragana (そ,た,ち,つ,て,と,な,に,ぬ,ね,の,は,ひ,ふ,ほ,ま)
     Col 1: hiragana continued
     Col 2: katakana (ク,ケ,コ,サ,シ,ス,セ,ソ,タ,チ,ツ,ト,ナ,ニ,...)
     Col 3: katakana continued
     Col 4: kanji (名,盗,武,炎,算,人,心,頼,落,...)
     Col 5: kanji continued

3. ALPHANUMERIC GRID (LE uint16):
   0x3CA690-0x3CA770: ASCII-0x20 mapped glyph IDs (0-55)
     Full grid: !\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVW
     Second half with blanks (60) for disabled cells

4. MODE INDEX TABLE (LE uint16):
   0x3CA770: {0, 2, 1, FFFF, 4, FFFF, 5, 6, 7, 8, 9, 10}
   Maps tab positions to mode IDs

5. TAB/BUTTON LABEL GLYPH IDs (LE uint32):
   0x3C9DA0: 6400 (0x1900)  = Tab label 0 (likely カナ)
   0x3C9DA4: 6401 (0x1901)  = Tab label 1 (likely かな)
   0x3C9DA8: 6402 (0x1902)  = Tab label 2 (likely 英数)
   0x3C9DAC: 6403 (0x1903)  = Tab label 3 (likely 記号)
   0x3C9DB0: 6404 (0x1904)  = Tab label 4 (unknown)
   [FFFF padding]
   0x3C9DEC: 6405 (0x1905)  = Button 0 (likely 決定)
   0x3C9DF0: 6406 (0x1906)  = Button 1 (likely 男名)
   0x3C9DF4: 6407 (0x1907)  = Button 2 (likely 女名)
   0x3C9DF8: 6408 (0x1908)  = Button 3 (1文字消す?)
   0x3C9DFC: 6409 (0x1909)  = Button 4 (全消去?)

   Additional groups for other screens:
   0x3C9E18: 6410-6412 (0x190A-0x190C)
   0x3C9E50+: 6656-6668 (0x1A00-0x1A0C)
   0x3C9F00+: 6912-6924 (0x1B00-0x1B0C)
   0x3C9FB0+: 7168-7177 (0x1C00-0x1C09)

6. FONT RESOURCES:
   Resource ID 0x04A4 and 0x04A5 are the font resources
   loaded for the name entry screen. These contain the glyph
   bitmaps that IDs 6400+ map to. These are loaded at runtime
   into the glyph table at VA 0x4EBBEC.

7. KANA CHARACTER CELL STRUCTS (0x20-byte each):
   0x3C96F0-0x3C99B0: Each struct has glyph IDs 1193-1214
   from the name entry's own font system (IDs 1193+)
   These map to the bitmap glyphs in resources 0x04A4/0x04A5.

8. POINTER TABLES:
   0x3C99B0-0x3C9A08: 22 LE uint32 pointers to kana char structs
   0x3C9600-0x3C96E4: Symbol/kanji bitmap offset pairs (offset, page)

9. CODE REFERENCES:
   0x1ED0E0 (VA 0x2ED060): Name entry init function
   0x1F2700 (VA 0x2F2680): Grid cell rendering
   0x1FAF40 (VA 0x2FAEC0): Alphanumeric grid reference
   0x1FB774 (VA 0x2FB6F4): Mode index table reference
"""

print(__doc__)

import struct, json
exe = open('extracted/SLPM_653.78', 'rb').read()
gmap = json.load(open('data/msg_glyph_map.json', encoding='utf-8'))

# Print the definitive table
print("DEFINITIVE TAB LABEL DATA:")
print("=" * 60)

# Tab labels (first group)
print("\nTab labels at 0x3C9DA0 (LE uint32):")
for off in [0x3C9DA0, 0x3C9DA4, 0x3C9DA8, 0x3C9DAC, 0x3C9DB0]:
    v = struct.unpack_from('<I', exe, off)[0]
    print("  0x%06X: glyph %d (0x%04X)" % (off, v, v))

# Button labels (second group)
print("\nButton labels at 0x3C9DEC (LE uint32):")
for off in [0x3C9DEC, 0x3C9DF0, 0x3C9DF4, 0x3C9DF8, 0x3C9DFC]:
    v = struct.unpack_from('<I', exe, off)[0]
    print("  0x%06X: glyph %d (0x%04X)" % (off, v, v))

# Extra labels
print("\nExtra labels at 0x3C9E18:")
for off in [0x3C9E18, 0x3C9E1C, 0x3C9E24]:
    v = struct.unpack_from('<I', exe, off)[0]
    print("  0x%06X: glyph %d (0x%04X)" % (off, v, v))
