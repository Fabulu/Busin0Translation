#!/usr/bin/env python3
"""Search for intro text - try completely different approaches."""
import zipfile
import struct
import sys
sys.stdout.reconfigure(encoding='utf-8')

z = zipfile.ZipFile('C:/Programmieren/wizardrytranslation/ramdumps/intro.p2s', 'r')
ram = z.read('eeMemory.bin')

# The intro text characters that are MISSING from the MSG glyph map:
# 悲, 惨, 争, 役, 々, 憶
# This suggests the intro uses a DIFFERENT text system or glyph set.

# Maybe the intro text is in PACKDATA files loaded into RAM.
# Let's look at what data is loaded by searching for known PACKDATA file signatures.

# === Approach 1: The intro might use Shift-JIS directly via a different font system ===
# Some PS2 games have TWO font systems: one for in-game MSG, another for cutscenes
# The cutscene system might use SJIS directly

# Let's search more broadly for ANY Shift-JIS text in RAM
# Look for high-frequency SJIS byte pairs (starting with 0x82-0x84, 0x88-0x9F, 0xE0-0xEF)
print("=== Scanning for Shift-JIS text regions ===")
sjis_density = []
for offset in range(0, len(ram), 4096):
    block = ram[offset:offset+4096]
    sjis_count = 0
    i = 0
    while i < len(block) - 1:
        b1 = block[i]
        b2 = block[i+1] if i+1 < len(block) else 0
        # Check if this looks like a SJIS double-byte char
        if (0x81 <= b1 <= 0x9F or 0xE0 <= b1 <= 0xEF) and (0x40 <= b2 <= 0xFC and b2 != 0x7F):
            sjis_count += 1
            i += 2
        else:
            i += 1
    if sjis_count > 50:  # High density of SJIS chars
        sjis_density.append((offset, sjis_count))

sjis_density.sort(key=lambda x: -x[1])
print(f"Top SJIS-dense regions (count > 50):")
for offset, count in sjis_density[:20]:
    # Try decoding
    block = ram[offset:offset+200]
    try:
        decoded = block.decode('shift-jis', errors='replace')
        # Show first non-garbage part
        clean = decoded[:80]
        print(f"  0x{offset:08X}: {count} chars - {repr(clean)}")
    except:
        print(f"  0x{offset:08X}: {count} chars")

# === Approach 2: Look for the sentence stored with some per-character header ===
# Maybe each displayed character has (sjis_code, x_pos, y_pos, alpha, ...)
# Search for SJIS code of そ (0x82BB) followed by coordinate-like values
print("\n=== Searching for SJIS-with-coordinates pattern ===")
sono_sjis = 0x82BB
for stride in [8, 12, 16, 20, 24, 28, 32]:
    # Search for そ SJIS at stride intervals followed by の
    no_sjis = 0x82CC
    for endian in ['<', '>']:
        # Try as uint16
        target1 = struct.pack(f'{endian}H', sono_sjis)
        pos = 0
        count = 0
        while count < 50:
            pos = ram.find(target1, pos)
            if pos < 0: break
            # Check if の follows at stride
            if pos + stride + 1 < len(ram):
                next_val = struct.unpack_from(f'{endian}H', ram, pos + stride)[0]
                if next_val == no_sjis:
                    # Check 3rd char too (悲 = 0x94DF)
                    hi_sjis = 0x94DF
                    third = struct.unpack_from(f'{endian}H', ram, pos + 2*stride)[0] if pos + 2*stride + 1 < len(ram) else 0
                    if third == hi_sjis:
                        print(f"  MATCH stride={stride} endian={endian} at 0x{pos:08X}")
                        # Dump all chars at this stride
                        for i in range(15):
                            off = pos + i * stride
                            if off + stride <= len(ram):
                                word = struct.unpack_from(f'{endian}H', ram, off)[0]
                                extra = ram[off+2:off+stride].hex()
                                try:
                                    ch = struct.pack(f'{endian}H', word).decode('shift-jis', errors='replace')
                                except:
                                    ch = '?'
                                print(f"    [{i}] 0x{word:04X} ({ch}) extra={extra}")
            pos += 2
            count += 1

# === Approach 3: Maybe it's stored as a different glyph ID mapping ===
# The intro font might have its own glyph table loaded into RAM
# Search for a table that maps SJIS codes to glyph positions or vice versa
print("\n=== Looking for SJIS-to-glyph conversion tables ===")
# A conversion table would have monotonically increasing SJIS codes
# Hiragana SJIS: 0x82A0 (あ) to 0x82F1 (ん) = contiguous
# Search for a uint16 array containing 0x82A0, 0x82A2, 0x82A4... (hiragana)
hiragana_start = struct.pack('<H', 0x82A0)  # あ
pos = 0
count = 0
while count < 30:
    pos = ram.find(hiragana_start, pos)
    if pos < 0: break
    # Check if next values are sequential hiragana
    vals = [struct.unpack_from('<H', ram, pos + i*2)[0] for i in range(5) if pos + i*2 + 1 < len(ram)]
    # Hiragana SJIS: あ=82A0, い=82A2, う=82A4, え=82A6, お=82A8
    if len(vals) >= 5 and vals[1] == 0x82A2 and vals[2] == 0x82A4:
        print(f"  Hiragana table at 0x{pos:08X}: {[f'0x{v:04X}' for v in vals]}")
        # Dump more
        more = [struct.unpack_from('<H', ram, pos + i*2)[0] for i in range(20) if pos + i*2 + 1 < len(ram)]
        print(f"    Full: {[f'0x{v:04X}' for v in more]}")
    pos += 2
    count += 1

# === Approach 4: Check the GS VRAM for text texture data ===
print("\n=== Analyzing GS.bin VRAM for font textures ===")
gs = z.read('GS.bin')
# The GS.bin typically starts with register dump, then VRAM
# PCSX2 GS savestate format: first some bytes of register state, then 4MB VRAM
# Let's look for the header to find where VRAM starts
header = gs[:100]
print(f"GS header: {header[:40].hex()}")

# Search for repeating patterns that might be font glyph bitmaps
# A 16x16 font glyph in 4bpp would be 128 bytes per glyph
# Look for structured repetitive data
# Actually, let's just check if any part of GS has SJIS text
for enc in ['shift-jis']:
    for word in ['\u60b2\u60e8', '\u6226\u5f79', '\u30d0\u30f3\u30af']:
        target = word.encode(enc)
        pos = gs.find(target)
        if pos >= 0:
            print(f"  SJIS '{word}' in GS at 0x{pos:08X}")

print("\n=== Done ===")
