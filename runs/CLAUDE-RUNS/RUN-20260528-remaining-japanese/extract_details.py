#!/usr/bin/env python3
"""Show the 6 Japanese + 1 mixed messages in R38, and check EXE at 0x3F9678."""
import struct, os, sys, json, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

OUT = "C:/Programmieren/wizardrytranslation/runs/CLAUDE-RUNS/RUN-20260528-remaining-japanese"

# Load glyph map
glyph_map = json.load(open("C:/Programmieren/wizardrytranslation/data/msg_glyph_map.json", encoding="utf-8"))
glyph_to_char = {}
for i in range(95):
    glyph_to_char[i] = chr(i + 0x20)

def decode_msg(msg):
    decoded = ""
    for g in msg:
        if g == 0xFFFE:
            decoded += "\\n"
        elif g >= 0xFB00:
            decoded += f"[{g:04X}]"
        elif g < 95:
            decoded += glyph_to_char.get(g, "?")
        else:
            ch = glyph_map.get(str(g), None)
            decoded += ch if ch else f"<{g}>"
    return decoded

# Parse R38
r38 = open(os.path.join(OUT, "r38_from_iso.bin"), "rb").read()
payload = r38[16:16 + struct.unpack_from("<I", r38, 4)[0]]

messages = []
current = []
for i in range(0, len(payload) - 1, 2):
    w = struct.unpack_from(">H", payload, i)[0]
    if w == 0xFFFF:
        messages.append(current)
        current = []
    else:
        current.append(w)
if current:
    messages.append(current)

print("=" * 70)
print("  R38: Non-English Messages")
print("=" * 70)
for mi, msg in enumerate(messages):
    if not msg:
        continue
    jp_g = sum(1 for g in msg if 95 <= g < 0xFB00)
    if jp_g == 0:
        continue
    ascii_g = sum(1 for g in msg if g < 95)
    tag = "MIXED" if ascii_g > 0 else "JAPANESE"
    print(f"\n  MSG {mi} [{tag}] ({len(msg)} glyphs, {ascii_g} ASCII, {jp_g} JP):")
    print(f"    Raw IDs: {msg}")
    print(f"    Decoded: {decode_msg(msg)}")

# Check EXE at 0x3F9678
print("\n" + "=" * 70)
print("  EXE: Check 0x3F9678")
print("=" * 70)
exe = open(os.path.join(OUT, "exe_from_iso.bin"), "rb").read()
offset = 0x3F9678
chunk = exe[offset:offset+32]
print(f"  Hex: {chunk.hex()}")
try:
    sjis = chunk.split(b'\x00')[0].decode('shift_jis')
    print(f"  SJIS: {sjis}")
except:
    print(f"  ASCII: {chunk.split(b'\x00')[0]}")

# Also check original patched EXE for comparison
print(f"\n  Context around 0x3F9678 (+-32 bytes):")
for off in range(offset - 32, offset + 64, 16):
    chunk = exe[off:off+16]
    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
    print(f"    0x{off:06X}: {chunk.hex()} | {ascii_str}")
