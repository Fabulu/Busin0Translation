#!/usr/bin/env python3
"""Search for intro text - examine loaded data structures and PACKDATA index."""
import zipfile
import struct
import sys
sys.stdout.reconfigure(encoding='utf-8')

z = zipfile.ZipFile('C:/Programmieren/wizardrytranslation/ramdumps/intro.p2s', 'r')
ram = z.read('eeMemory.bin')

# === Approach: Find what PACKDATA resources are loaded ===
# The PACKDATA.DIG TOC is loaded into RAM. Find it and decode resource indices.
# We know PACKDATA reference is at 0x00504B48 and 0x0050AD48
# Let's examine those areas for TOC data

print("=== PACKDATA loading context ===")
for addr in [0x00504B40, 0x0050AD40]:
    print(f"\nAt 0x{addr:08X}:")
    for i in range(0, 128, 16):
        row = ram[addr+i:addr+i+16]
        hex_part = ' '.join(f'{b:02x}' for b in row)
        ascii_part = ''.join(chr(b) if 32 <= b < 127 else '.' for b in row)
        print(f"  {addr+i:08X}: {hex_part}  {ascii_part}")

# === Look for pointers to text data ===
# If the game has a text display function active, there should be pointers
# to text strings in RAM. Let's look for structures with pointers into
# the MSG data area (0x00E10000-0x00E30000)
print("\n=== Pointers to MSG area ===")
msg_area_start = 0x00E10000
msg_area_end = 0x00E30000
ptr_count = 0
for offset in range(0, len(ram) - 4, 4):
    val = struct.unpack_from('<I', ram, offset)[0]
    if msg_area_start <= val < msg_area_end:
        ptr_count += 1
if ptr_count > 0:
    print(f"  {ptr_count} pointers found into MSG area")

# === Let's look for the actual intro script/event data ===
# Games typically have an event/script system that triggers text display
# Search for distinctive byte patterns near known text areas
# Let's check what's near the "される" hits we found earlier

print("\n=== MSG data area scan ===")
# Find the boundaries of MSG data
# We know sareru was found at 0x00E16E67, 0x00E174A3, etc.
# Let's scan the area 0x00E10000-0x00E30000 for MSG-format messages
msg_region = ram[0x00E10000:0x00E30000]
# Count 0xFFFF occurrences (message terminators)
ffff_count = 0
pos = 0
while True:
    pos = msg_region.find(b'\xff\xff', pos)
    if pos < 0: break
    ffff_count += 1
    pos += 2
print(f"  0xFFFF count in 0xE10000-0xE30000: {ffff_count}")

# === Actually, let's think differently ===
# The intro might not use the MSG system at ALL
# It might use a script file that directly references SJIS codes
# and renders them using a dedicated intro font

# Let's search for regions that contain SEQUENTIAL data that could be
# font glyph indices for the intro
# The intro has ~25 chars. If stored as uint16, that's 50 bytes.

# What if the text is stored as an index into a SJIS-ordered font?
# Japanese fonts are often ordered by SJIS code
# In SJIS, hiragana starts at 0x82A0, katakana at 0x8340
# If the font is SJIS-ordered, the "index" would be (sjis_code - base)

# そ = SJIS 0x82BB, offset from 0x82A0 = 0x1B = 27
# の = SJIS 0x82CC, offset from 0x82A0 = 0x2C = 44

# Let's try this mapping for the hiragana/katakana parts:
sentence = '\u305d\u306e\u60b2\u60e8\u306a\u6226\u4e89\u306f\u30d0\u30f3\u30af\u30a9\u30fc\u306e\u6226\u5f79\u3068\u4eba\u3005\u306b\u8a18\u61b6\u3055\u308c\u308b\u3002'

print("\n=== SJIS-offset glyph indices ===")
for ch in sentence:
    sjis = ch.encode('shift-jis')
    if len(sjis) == 2:
        code = struct.unpack('>H', sjis)[0]
        # Various possible bases
        if 0x8240 <= code <= 0x82FF:
            idx = code - 0x8240
            print(f"  {ch}: SJIS=0x{code:04X}, idx_from_8240={idx}")
        elif 0x8340 <= code <= 0x83FF:
            idx = code - 0x8340 + 96  # after hiragana block
            print(f"  {ch}: SJIS=0x{code:04X}, idx_from_8340+96={idx}")
        elif 0x8140 <= code <= 0x81FF:
            idx = code - 0x8140
            print(f"  {ch}: SJIS=0x{code:04X}, idx_from_8140={idx}")
        else:
            print(f"  {ch}: SJIS=0x{code:04X}, (kanji range)")

# === Try: what if characters are stored as JIS X 0208 row-cell encoding? ===
# JIS X 0208 assigns each char a (row, cell) pair
# SJIS can be converted to JIS row-cell
print("\n=== JIS row-cell encoding ===")
def sjis_to_jis(sjis_hi, sjis_lo):
    if sjis_hi >= 0xE0:
        sjis_hi -= 0x40
    row = (sjis_hi - 0x81) * 2 + 1
    if sjis_lo >= 0x80:
        sjis_lo -= 1
    if sjis_lo >= 0x9E:
        row += 1
        cell = sjis_lo - 0x9E + 1
    else:
        cell = sjis_lo - 0x3F
    return row, cell

for ch in sentence:
    sjis = ch.encode('shift-jis')
    if len(sjis) == 2:
        row, cell = sjis_to_jis(sjis[0], sjis[1])
        linear = (row - 1) * 94 + (cell - 1)
        print(f"  {ch}: JIS row={row} cell={cell}, linear={linear}")

# Now search for a sequence of these JIS linear indices
print("\n=== Searching for JIS linear index sequences ===")
jis_indices = []
for ch in sentence:
    sjis = ch.encode('shift-jis')
    if len(sjis) == 2:
        row, cell = sjis_to_jis(sjis[0], sjis[1])
        linear = (row - 1) * 94 + (cell - 1)
        jis_indices.append(linear)

# Try first 5 chars as uint16 LE
if len(jis_indices) >= 5:
    pattern = struct.pack('<5H', *jis_indices[:5])
    print(f"  First 5 JIS linear as uint16 LE: {pattern.hex()}")
    pos = ram.find(pattern)
    if pos >= 0:
        print(f"    FOUND at 0x{pos:08X}!")
    else:
        print(f"    not found")

    # Try as uint8
    if all(v < 256 for v in jis_indices[:5]):
        pattern = bytes(jis_indices[:5])
        print(f"  First 5 JIS linear as uint8: {pattern.hex()}")
        pos = ram.find(pattern)
        if pos >= 0:
            print(f"    FOUND at 0x{pos:08X}!")

# === Let's also check: is the text maybe in a separate data area? ===
# Search for any readable text block that ISN'T SJIS but uses some other encoding
print("\n=== Large zero-separated regions ===")
# Some games store text as null-terminated SJIS strings in a block
# Let's find blocks of SJIS strings
for region_start in range(0, len(ram), 0x10000):
    region = ram[region_start:region_start+0x10000]
    # Count null-terminated strings
    null_strings = region.split(b'\x00')
    sjis_strings = 0
    for s in null_strings:
        if len(s) >= 4:
            try:
                decoded = s.decode('shift-jis')
                # Check if it's actually Japanese
                has_jp = any(ord(c) > 0x3000 for c in decoded)
                if has_jp:
                    sjis_strings += 1
            except:
                pass
    if sjis_strings > 10:
        print(f"  0x{region_start:08X}: {sjis_strings} SJIS strings")
        # Show first few
        count = 0
        for s in null_strings:
            if len(s) >= 4 and count < 5:
                try:
                    decoded = s.decode('shift-jis')
                    if any(ord(c) > 0x3000 for c in decoded):
                        print(f"    {repr(decoded[:60])}")
                        count += 1
                except:
                    pass

print("\n=== Done ===")
