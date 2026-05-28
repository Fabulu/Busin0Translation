#!/usr/bin/env python3
"""Follow up on the SJIS hit and explore more approaches."""
import zipfile
import struct

z = zipfile.ZipFile('C:/Programmieren/wizardrytranslation/ramdumps/intro.p2s', 'r')
ram = z.read('eeMemory.bin')

# === Examine area around the SJIS hit at 0x004F8E70 ===
print("=== Context around 0x004F8E70 ===")
pos = 0x004F8E70
ctx = ram[pos-64:pos+128]
print(f"Hex dump:")
for i in range(0, len(ctx), 16):
    addr = pos - 64 + i
    hex_part = ' '.join(f'{b:02x}' for b in ctx[i:i+16])
    ascii_part = ''.join(chr(b) if 32 <= b < 127 else '.' for b in ctx[i:i+16])
    print(f"  {addr:08X}: {hex_part}  {ascii_part}")

# Try decoding as SJIS
try:
    decoded = ctx.decode('shift-jis', errors='replace')
    print(f"\nSJIS decode: {decoded}")
except:
    pass

# === Search for ALL occurrences of 82bb82cc (その) ===
print("\n=== All occurrences of 'その' (SJIS) ===")
target = b'\x82\xbb\x82\xcc'
pos = 0
count = 0
while count < 50:
    pos = ram.find(target, pos)
    if pos < 0: break
    # Check what follows - is it 悲惨 (94df8e53)?
    following = ram[pos+4:pos+8]
    following_hex = following.hex()
    # Check if next bytes look like more SJIS
    try:
        extended = ram[pos:pos+20].decode('shift-jis', errors='replace')
    except:
        extended = ''
    if '悲' in extended or '戦' in extended or following_hex.startswith('94df') or following_hex.startswith('8e53'):
        print(f"  0x{pos:08X}: {ram[pos:pos+30].hex()}  -> {extended}")
    count += 1
    pos += 1

# === Try a completely different approach: search for the sentence as individual ===
# Shift-JIS character codes stored as 32-bit values (one char per word)
print("\n=== SJIS chars as 32-bit values ===")
sentence = 'その悲惨な戦争はバンクォーの戦役と人々に記憶される。'
sjis_chars = []
for ch in sentence:
    sjis_chars.append(int.from_bytes(ch.encode('shift-jis'), 'big'))
print(f"SJIS char values: {[f'0x{v:04X}' for v in sjis_chars[:10]]}")

# Try each char stored as uint32 LE, search for first 3 chars
# その悲 = 0x82BB, 0x82CC, 0x94DF
for word_size in [4]:  # 32-bit per char
    pattern = b''
    for v in sjis_chars[:3]:
        pattern += struct.pack('<I', v)
    pos = ram.find(pattern)
    if pos >= 0:
        print(f"  32-bit LE first 3 chars: FOUND at 0x{pos:08X}")

    pattern = b''
    for v in sjis_chars[:3]:
        pattern += struct.pack('>I', v)
    pos = ram.find(pattern)
    if pos >= 0:
        print(f"  32-bit BE first 3 chars: FOUND at 0x{pos:08X}")

# === What about the game using its own character index? ===
# The font for the intro might be a different font texture.
# Let's look for any reference to intro/opening files loaded in memory

print("\n=== Searching for file path strings in RAM ===")
for keyword in [b'intro', b'INTRO', b'opening', b'OPENING', b'narr', b'NARR', b'event', b'EVENT', b'story', b'STORY', b'msg', b'MSG', b'font', b'FONT', b'text', b'TEXT']:
    pos = 0
    count = 0
    while count < 5:
        pos = ram.find(keyword, pos)
        if pos < 0: break
        ctx = ram[max(0,pos-4):pos+40]
        # Only show if it looks like a path/filename
        printable = sum(1 for b in ctx if 32 <= b < 127)
        if printable > len(ctx) * 0.5:
            text = ctx.decode('ascii', errors='replace')
            print(f"  '{keyword.decode()}' at 0x{pos:08X}: {text}")
        pos += 1
        count += 1

# === Look for the GS.bin VRAM more carefully ===
print("\n=== GS.bin structure ===")
gs = z.read('GS.bin')
# The first bytes of GS.bin in PCSX2 savestate typically have register state + VRAM
print(f"GS.bin first 64 bytes: {gs[:64].hex()}")
print(f"GS.bin size: {len(gs)}")

# PCSX2 GS savestates: typically registers then 4MB VRAM
# Look for text patterns in VRAM portion
vram_offset = len(gs) - 4*1024*1024  # Last 4MB is usually VRAM
if vram_offset >= 0:
    vram = gs[vram_offset:]
    print(f"Potential VRAM at offset 0x{vram_offset:X}, size {len(vram)}")
    # Search VRAM for SJIS text
    target = b'\x82\xbb\x82\xcc'  # その
    pos = vram.find(target)
    if pos >= 0:
        print(f"  SJIS 'sono' in VRAM at offset 0x{pos:08X}")
else:
    print(f"  VRAM offset calculation negative: {vram_offset}")

# === Let's look for the rendering data structure ===
# PS2 games often have a text display struct with:
# - pointer to string data
# - x, y position
# - color, size parameters
# The text is centered on screen, so x would be ~320 (middle of 640)
# Let's search for float 320.0 or int 320 near text-related areas
print("\n=== Looking for text rendering structs ===")
target_x = struct.pack('<f', 320.0)
target_y = struct.pack('<f', 200.0)  # rough y position
pos = 0
count = 0
while count < 20:
    pos = ram.find(target_x, pos)
    if pos < 0: break
    # Check if nearby bytes have y coordinate
    region = ram[pos-16:pos+32]
    vals = []
    for i in range(0, len(region)-3, 4):
        fv = struct.unpack_from('<f', region, i)[0]
        vals.append(fv)
    # Look for reasonable screen coordinates
    has_y = any(100 < v < 400 for v in vals if v != 320.0)
    if has_y:
        # Check if there's a pointer nearby (PS2 addresses are 0x00xxxxxx - 0x02000000)
        ptrs = []
        for i in range(0, len(region)-3, 4):
            iv = struct.unpack_from('<I', region, i)[0]
            if 0x00100000 < iv < 0x02000000:
                ptrs.append((i, iv))
        if ptrs:
            print(f"  x=320.0 at 0x{pos:08X}, floats: {[f'{v:.1f}' for v in vals]}")
            for off, ptr in ptrs:
                print(f"    ptr at +{off}: 0x{ptr:08X}")
    pos += 4
    count += 1

print("\n=== Done ===")
