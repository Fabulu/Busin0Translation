#!/usr/bin/env python3
"""Final approach: search for the text in PACKDATA.DIG resources and check EXE."""
import zipfile
import struct
import sys
import os
sys.stdout.reconfigure(encoding='utf-8')

z1 = zipfile.ZipFile('C:/Programmieren/wizardrytranslation/ramdumps/intro.p2s', 'r')
ram = z1.read('eeMemory.bin')

# === Check the PACKDATA.DIG file ===
dig_path = 'C:/Programmieren/wizardrytranslation/build/PACKDATA.DIG'
if os.path.exists(dig_path):
    with open(dig_path, 'rb') as f:
        dig = f.read()
    print(f"PACKDATA.DIG size: {len(dig)} bytes ({len(dig)/1024/1024:.1f} MB)")

    # Search the entire DIG for our text
    sentence = '\u305d\u306e\u60b2\u60e8\u306a\u6226\u4e89\u306f\u30d0\u30f3\u30af\u30a9\u30fc\u306e\u6226\u5f79\u3068\u4eba\u3005\u306b\u8a18\u61b6\u3055\u308c\u308b\u3002'

    for enc in ['shift-jis', 'euc-jp', 'utf-16-le', 'utf-16-be', 'utf-8']:
        try:
            target = sentence.encode(enc)
            pos = dig.find(target)
            if pos >= 0:
                print(f"  FULL SENTENCE ({enc}) in DIG at 0x{pos:08X}")
        except:
            pass

    # Search for individual distinctive words
    for word in ['\u60b2\u60e8', '\u6226\u5f79', '\u30d0\u30f3\u30af\u30a9\u30fc', '\u8a18\u61b6']:
        for enc in ['shift-jis', 'euc-jp', 'utf-16-le']:
            try:
                target = word.encode(enc)
                pos = 0
                count = 0
                while count < 5:
                    pos = dig.find(target, pos)
                    if pos < 0:
                        break
                    print(f"  '{word}' ({enc}) in DIG at 0x{pos:08X}")
                    # Show context
                    ctx = dig[max(0,pos-10):pos+len(target)+10]
                    print(f"    hex: {ctx.hex()}")
                    pos += 1
                    count += 1
            except:
                pass

# === Check the game executable (ELF) ===
print("\n=== Searching game EXE in RAM ===")
# PS2 ELF is typically loaded at 0x00100000
# The intro text might be hardcoded in the EXE
# Let's search the code section (0x00100000-0x00500000)
exe_region = ram[0x00100000:0x00500000]

for word in ['\u60b2\u60e8', '\u6226\u5f79', '\u30d0\u30f3\u30af']:
    for enc in ['shift-jis', 'euc-jp', 'utf-16-le']:
        try:
            target = word.encode(enc)
            pos = exe_region.find(target)
            if pos >= 0:
                abs_pos = 0x00100000 + pos
                print(f"  '{word}' ({enc}) in EXE at 0x{abs_pos:08X}")
                ctx = exe_region[max(0,pos-10):pos+len(target)+20]
                print(f"    hex: {ctx.hex()}")
        except:
            pass

# === Check if there's a separate ELF file ===
elf_files = []
for root, dirs, files in os.walk('C:/Programmieren/wizardrytranslation'):
    for f in files:
        if f.lower().endswith(('.elf', '.bin')) and 'busin' in f.lower():
            elf_files.append(os.path.join(root, f))
    if root.count(os.sep) > 5:
        dirs.clear()
print(f"\nELF files found: {elf_files}")

# === Let's look more carefully at all text/string data in the game ===
# The intro narration MUST be somewhere. Let's check PACKDATA.DIG thoroughly.
# Search for ALL SJIS text blocks in PACKDATA.DIG
if os.path.exists(dig_path):
    print("\n=== SJIS text blocks in PACKDATA.DIG ===")
    # Scan every 4KB block for SJIS text density
    sjis_blocks = []
    for offset in range(0, len(dig), 4096):
        block = dig[offset:offset+4096]
        # Try to decode as SJIS and count Japanese chars
        try:
            decoded = block.decode('shift-jis', errors='ignore')
            jp_count = sum(1 for c in decoded if ord(c) > 0x3000)
            if jp_count > 50:
                sjis_blocks.append((offset, jp_count, decoded[:100]))
        except:
            pass

    sjis_blocks.sort(key=lambda x: -x[1])
    print(f"  Found {len(sjis_blocks)} blocks with >50 JP chars")
    for offset, count, text in sjis_blocks[:20]:
        print(f"  0x{offset:08X}: {count} JP chars")
        print(f"    {text[:80]}")

    # Specifically search for 戦役 (seneki) - a rare compound
    for enc in ['shift-jis']:
        target = '\u6226\u5f79'.encode(enc)
        pos = 0
        count = 0
        while count < 20:
            pos = dig.find(target, pos)
            if pos < 0:
                break
            ctx = dig[max(0,pos-20):pos+24]
            try:
                decoded = ctx.decode('shift-jis', errors='replace')
                print(f"  'seneki' at DIG 0x{pos:08X}: {decoded}")
            except:
                print(f"  'seneki' at DIG 0x{pos:08X}: {ctx.hex()}")
            pos += 1
            count += 1

# === Check if text data is in the ISO directly ===
print("\n=== Looking for ISO/disc image ===")
for root, dirs, files in os.walk('C:/Programmieren/wizardrytranslation'):
    for f in files:
        if f.lower().endswith(('.iso', '.img', '.bin', '.cue')):
            fp = os.path.join(root, f)
            sz = os.path.getsize(fp)
            if sz > 100*1024*1024:  # > 100MB, probably the disc
                print(f"  {fp} ({sz/1024/1024:.0f} MB)")
    if root.count(os.sep) > 4:
        dirs.clear()

print("\n=== Done ===")
