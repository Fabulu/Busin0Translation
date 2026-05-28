#!/usr/bin/env python3
"""Deep search for intro narration text in RAM - glyph ID approach."""
import zipfile
import struct
import os

z = zipfile.ZipFile('C:/Programmieren/wizardrytranslation/ramdumps/intro.p2s', 'r')
ram = z.read('eeMemory.bin')

# The intro text: その悲惨な戦争はバンクォーの戦役と人々に記憶される。
# In our MSG glyph system, characters map to glyph IDs.
# But the intro might use a DIFFERENT glyph mapping.

# Let's try something different: search for Shift-JIS codes stored as 16-bit LE values
# In Shift-JIS: そ=0x82BB の=0x82CC 悲=0x94DF 惨=0x8E53
# But maybe the game stores the raw SJIS bytes differently

# Actually let's try: what if each SJIS character is stored as two bytes but
# the game processes them in a custom way?

# First, let's look for the Shift-JIS byte sequence of the FULL sentence
sentence = 'その悲惨な戦争はバンクォーの戦役と人々に記憶される。'
sjis = sentence.encode('shift-jis')
print(f"Full sentence SJIS ({len(sjis)} bytes): {sjis.hex()}")

# Search for any 4+ byte substring
for start in range(0, len(sjis) - 3):
    for length in [4, 6, 8]:
        if start + length > len(sjis):
            break
        fragment = sjis[start:start+length]
        pos = ram.find(fragment)
        if pos >= 0:
            print(f"  SJIS fragment at byte {start}, len {length}: FOUND at 0x{pos:08X}")
            print(f"    fragment: {fragment.hex()}")
            ctx = ram[max(0,pos-8):pos+length+8]
            print(f"    context: {ctx.hex()}")

# Try EUC-JP
print("\n=== EUC-JP fragments ===")
eucjp = sentence.encode('euc-jp')
print(f"Full sentence EUC-JP ({len(eucjp)} bytes): {eucjp.hex()}")
for start in range(0, len(eucjp) - 3):
    for length in [4, 6]:
        if start + length > len(eucjp):
            break
        fragment = eucjp[start:start+length]
        pos = ram.find(fragment)
        if pos >= 0:
            print(f"  EUC-JP fragment at byte {start}, len {length}: FOUND at 0x{pos:08X}")

# Try UTF-16LE character by character with gaps
print("\n=== UTF-16LE fragments ===")
for i in range(len(sentence) - 1):
    pair = sentence[i:i+2]
    u16le = pair.encode('utf-16-le')
    pos = ram.find(u16le)
    if pos >= 0:
        # Could be coincidence for 4 bytes, but check for more context
        longer = sentence[i:i+4] if i+4 <= len(sentence) else sentence[i:i+2]
        u16le_long = longer.encode('utf-16-le')
        pos2 = ram.find(u16le_long)
        if pos2 >= 0:
            print(f"  UTF16LE '{longer}' ({len(longer)} chars): FOUND at 0x{pos2:08X}")
            ctx = ram[pos2:pos2+len(u16le_long)+16]
            print(f"    hex: {ctx.hex()}")

# === Maybe it's stored with 4-byte aligned characters? ===
print("\n=== 4-byte aligned SJIS search ===")
# Some PS2 games pad each SJIS char to 4 bytes (2 SJIS bytes + 2 padding)
chars_sjis = []
for ch in sentence:
    chars_sjis.append(ch.encode('shift-jis'))

# Try with 0x00 padding after each 2-byte char
padded = b''
for c in chars_sjis[:5]:  # first 5 chars: その悲惨な
    padded += c + b'\x00\x00'
pos = ram.find(padded)
if pos >= 0:
    print(f"  Padded SJIS: FOUND at 0x{pos:08X}")
else:
    # Try just 1 byte padding
    padded = b''
    for c in chars_sjis[:5]:
        padded += c + b'\x00'
    pos = ram.find(padded)
    if pos >= 0:
        print(f"  1-byte padded SJIS: FOUND at 0x{pos:08X}")

# === Check if the text could be stored as glyph indices ===
# Let's check what glyph indices our known font uses
# Load the glyph map if available
print("\n=== Checking for known glyph map ===")
glyph_map_path = 'C:/Programmieren/wizardrytranslation/build/glyph_map.txt'
if os.path.exists(glyph_map_path):
    with open(glyph_map_path, 'r', encoding='utf-8') as f:
        content = f.read()
    print(f"  glyph_map.txt exists, {len(content)} bytes")
    # Parse it to find glyph IDs for our characters
    glyph_ids = {}
    for line in content.split('\n'):
        if line.strip():
            parts = line.strip().split('\t')
            if len(parts) >= 2:
                try:
                    gid = int(parts[0])
                    char = parts[1]
                    if char in sentence:
                        glyph_ids[char] = gid
                except:
                    pass
    if glyph_ids:
        print(f"  Found glyph IDs for: {glyph_ids}")
        # Try searching for these IDs as uint16 LE sequence
        ids_for_sentence = []
        for ch in sentence:
            if ch in glyph_ids:
                ids_for_sentence.append(glyph_ids[ch])
            else:
                ids_for_sentence.append(None)
        print(f"  Glyph ID sequence: {ids_for_sentence}")

        # Search for first few known IDs in sequence
        known = [(i, v) for i, v in enumerate(ids_for_sentence) if v is not None]
        if len(known) >= 3:
            # Build search pattern from first 3 known consecutive
            for j in range(len(known)-2):
                if known[j+1][0] == known[j][0]+1 and known[j+2][0] == known[j][0]+2:
                    i0, v0 = known[j]
                    i1, v1 = known[j+1]
                    i2, v2 = known[j+2]
                    # Try as uint16 LE
                    pattern = struct.pack('<HHH', v0, v1, v2)
                    pos = 0
                    count = 0
                    while count < 5:
                        pos = ram.find(pattern, pos)
                        if pos < 0: break
                        ctx_before = ram[max(0,pos-10):pos]
                        ctx_after = ram[pos+6:pos+20]
                        vals_before = [struct.unpack_from('<H', ctx_before, k)[0] for k in range(0, len(ctx_before)-1, 2)]
                        vals_after = [struct.unpack_from('<H', ctx_after, k)[0] for k in range(0, len(ctx_after)-1, 2)]
                        print(f"  Pattern [{v0},{v1},{v2}] (chars {i0}-{i2}) at 0x{pos:08X}")
                        print(f"    before: {vals_before}")
                        print(f"    after: {vals_after}")
                        pos += 2
                        count += 1
    else:
        print("  No matching glyph IDs found in map")
else:
    print("  No glyph_map.txt found")
    # Check alternative paths
    for p in ['build/glyph_table.bin', 'build/font_table.bin']:
        fp = f'C:/Programmieren/wizardrytranslation/{p}'
        if os.path.exists(fp):
            print(f"  Found: {fp}")

# === Search PACKDATA for intro files ===
print("\n=== Checking for intro-related files in working dirs ===")
for root, dirs, files in os.walk('C:/Programmieren/wizardrytranslation/build'):
    for f in files:
        fl = f.lower()
        if 'intro' in fl or 'opening' in fl or 'op_' in fl or 'narr' in fl:
            fp = os.path.join(root, f)
            print(f"  {fp} ({os.path.getsize(fp)} bytes)")
    # Don't recurse too deep
    if root.count(os.sep) > 6:
        dirs.clear()

print("\n=== Done ===")
