#!/usr/bin/env python3
"""Search save state RAM for intro narration text in various encodings."""
import zipfile
import struct
import sys
import os

os.chdir("C:/Programmieren/wizardrytranslation")

z = zipfile.ZipFile('ramdumps/intro.p2s', 'r')
ram = z.read('eeMemory.bin')
print(f"RAM size: {len(ram)} bytes ({len(ram)/1024/1024:.1f} MB)")

# === 1. Search for key Japanese words in multiple encodings ===
print("\n=== Encoding Search ===")
words = ['\u30d0\u30f3\u30af\u30a9\u30fc', '\u60b2\u60e8', '\u6226\u4e89', '\u6226\u5f79', '\u8a18\u61b6', '\u4eba\u3005']
# バンクォー, 悲惨, 戦争, 戦役, 記憶, 人々
for word in words:
    for enc in ['shift-jis', 'euc-jp', 'utf-16-le', 'utf-16-be', 'utf-8']:
        try:
            target = word.encode(enc)
            pos = 0
            while True:
                pos = ram.find(target, pos)
                if pos < 0:
                    break
                ctx = ram[max(0, pos-8):pos+len(target)+8]
                print(f"  {word} ({enc}): FOUND at 0x{pos:08X}")
                print(f"    hex: {ctx.hex()}")
                pos += 1
        except:
            pass

# === 2. Search for shorter katakana sequences ===
print("\n=== Short Katakana Search ===")
# バン = first two chars
for enc in ['shift-jis', 'euc-jp', 'utf-16-le', 'utf-16-be']:
    try:
        target = '\u30d0\u30f3'.encode(enc)
        pos = 0
        count = 0
        while count < 3:
            pos = ram.find(target, pos)
            if pos < 0:
                break
            ctx = ram[max(0, pos-4):pos+len(target)+12]
            print(f"  BaN ({enc}): at 0x{pos:08X} hex={ctx.hex()}")
            pos += 1
            count += 1
    except:
        pass

# === 3. Search for the full sentence fragment in Shift-JIS ===
print("\n=== Full Sentence Search ===")
sentence = '\u305d\u306e\u60b2\u60e8\u306a\u6226\u4e89'
# その悲惨な戦争
for enc in ['shift-jis', 'euc-jp', 'utf-16-le', 'utf-16-be', 'utf-8']:
    try:
        target = sentence.encode(enc)
        pos = ram.find(target)
        if pos >= 0:
            print(f"  ({enc}): FOUND at 0x{pos:08X}")
            ctx = ram[pos:pos+80]
            print(f"    hex: {ctx.hex()}")
            try:
                print(f"    decoded: {ctx.decode(enc, errors='replace')}")
            except:
                pass
        else:
            print(f"  ({enc}): not found")
    except Exception as e:
        print(f"  ({enc}): error {e}")

# === 4. Search IOP memory too ===
print("\n=== IOP Memory Search ===")
iop = z.read('iopMemory.bin')
print(f"IOP size: {len(iop)} bytes")
for word in ['\u30d0\u30f3\u30af\u30a9\u30fc', '\u6226\u4e89', '\u6226\u5f79']:
    for enc in ['shift-jis', 'euc-jp', 'utf-16-le', 'utf-16-be']:
        try:
            target = word.encode(enc)
            pos = iop.find(target)
            if pos >= 0:
                print(f"  {word} ({enc}): FOUND at 0x{pos:08X}")
        except:
            pass

# === 5. Look at GS.bin structure ===
print("\n=== GS.bin Analysis ===")
gs = z.read('GS.bin')
print(f"GS.bin size: {len(gs)} bytes ({len(gs)/1024/1024:.1f} MB)")
# GS memory is VRAM - check for text patterns there too
for word in ['\u30d0\u30f3\u30af\u30a9\u30fc', '\u6226\u4e89']:
    for enc in ['shift-jis', 'utf-16-le']:
        try:
            target = word.encode(enc)
            pos = gs.find(target)
            if pos >= 0:
                print(f"  {word} ({enc}) in GS: FOUND at 0x{pos:08X}")
        except:
            pass

# === 6. Glyph-ID based search ===
# Our MSG format uses glyph IDs. Let's search for sequences that might be
# glyph IDs for this text. The glyph IDs are typically 16-bit values.
print("\n=== Glyph ID Pattern Search ===")
# Look for FFFF-terminated uint16 sequences in interesting RAM regions
for region_start in range(0x00100000, 0x02000000, 0x100000):
    region = ram[region_start:region_start+0x100000]
    # Search for 0xFFFF as potential terminator
    pos = 0
    found_count = 0
    while found_count < 3:
        ffff_le = b'\xff\xff'
        pos = region.find(ffff_le, pos)
        if pos < 0 or pos < 20:
            break
        # Check preceding uint16 LE values
        vals = []
        for i in range(10, 0, -1):
            offset = pos - i * 2
            if offset >= 0:
                v = struct.unpack_from('<H', region, offset)[0]
                vals.append(v)
        # Check if they look like glyph IDs (small positive values, mixed)
        glyph_like = sum(1 for v in vals if 10 < v < 2000)
        if glyph_like >= 6:
            abs_pos = region_start + pos
            print(f"  Potential glyph stream ending at 0x{abs_pos:08X}: {vals}")
            found_count += 1
        pos += 2

# === 7. Check for text with null-byte spacing (common in some PS2 games) ===
print("\n=== Null-spaced text search ===")
# Some games store text as ASCII/SJIS with null bytes between chars
# Try searching for そ (0x82BB in SJIS) followed by の (0x82CC) with possible gaps
sono_sjis = b'\x82\xbb\x82\xcc'  # その in SJIS
pos = ram.find(sono_sjis)
count = 0
while pos >= 0 and count < 10:
    # Check if more of the sentence follows
    ctx = ram[pos:pos+40]
    # Check if 悲惨 (0x94DF 0x8E53 in SJIS) follows nearby
    hi_sjis = '\u60b2\u60e8'.encode('shift-jis')
    if hi_sjis in ram[pos:pos+20]:
        print(f"  'sono+hisan' at 0x{pos:08X}: {ctx.hex()}")
        print(f"    extended: {ram[pos:pos+100].hex()}")
        try:
            print(f"    decoded: {ram[pos:pos+100].decode('shift-jis', errors='replace')}")
        except:
            pass
    count += 1
    pos = ram.find(sono_sjis, pos + 1)

print("\n=== Done ===")
