import struct
from collections import Counter

exe_path = r"C:\Programmieren\wizardrytranslation\extracted_busin1\SLUS_202.59"
with open(exe_path, "rb") as f:
    exe_data = f.read()

# Found ABCDEFGHIJ...Z at 0x4A284C and 0x4A2928
# Let's examine the full area around these

print("=== Area around 0x4A2800 ===")
off = 0x4A2800
while off < 0x4A2A00:
    vals = [struct.unpack("<H", exe_data[off+k*2:off+k*2+2])[0] for k in range(20)]
    text = ""
    for v in vals:
        if 0x20 <= v < 0x7F:
            text += chr(v)
        elif v == 0:
            text += "."
        elif v == 0xFFF9:
            text += "#"
        elif v == 0xFFFF:
            text += "|"
        elif v == 0xFFFE:
            text += "~"
        else:
            text += f"<{v:04X}>"
    print(f"  0x{off:06X}: {text}")
    off += 40

# Now examine the 0x4B418E area
print("\n=== Area around 0x4B4100 ===")
off = 0x4B4100
while off < 0x4B4400:
    vals = [struct.unpack("<H", exe_data[off+k*2:off+k*2+2])[0] for k in range(20)]
    text = ""
    for v in vals:
        if 0x20 <= v < 0x7F:
            text += chr(v)
        elif v == 0:
            text += "."
        elif v == 0xFFF9:
            text += "#"
        elif v == 0xFFFF:
            text += "|"
        elif v == 0xFFFE:
            text += "~"
        else:
            text += f"<{v:04X}>"
    print(f"  0x{off:06X}: {text}")
    off += 40

# Let's look at the area 0x4A2800 more carefully - dump raw uint16 values
print("\n=== 0x4A2800-0x4A2A00 raw uint16 ===")
off = 0x4A2800
while off < 0x4A2A00:
    vals = [struct.unpack("<H", exe_data[off+k*2:off+k*2+2])[0] for k in range(10)]
    print(f"  0x{off:06X}: {' '.join(f'{v:04X}' for v in vals)}")
    off += 20

# Also examine 0x491BD2 which had ABCDEEFGHIIJKLMMNOPQ
print("\n=== Area around 0x491B00 ===")
off = 0x491B00
while off < 0x491E00:
    vals = [struct.unpack("<H", exe_data[off+k*2:off+k*2+2])[0] for k in range(20)]
    text = ""
    for v in vals:
        if 0x20 <= v < 0x7F:
            text += chr(v)
        elif v == 0:
            text += "."
        elif v >= 0xFF00:
            text += f"<{v:04X}>"
        else:
            text += f"[{v:03X}]"
    print(f"  0x{off:06X}: {text}")
    off += 40

print("\nDone part 6.")
