import struct

ATLAS_PATH = r"C:\Programmieren\wizardrytranslation\extracted\packdata_resources\1272_type01.bin"

with open(ATLAS_PATH, "rb") as f:
    data = f.read()

print(f"File size: {len(data)} bytes")
print(f"\nHeader (first 192 bytes) as 16-bit LE words:")
for i in range(0, 192, 2):
    val = struct.unpack_from("<H", data, i)[0]
    if val != 0:
        print(f"  offset {i:3d} (0x{i:02x}): 0x{val:04x} ({val})")

print(f"\nHeader (first 192 bytes) as 32-bit LE words:")
for i in range(0, 192, 4):
    val = struct.unpack_from("<I", data, i)[0]
    if val != 0:
        print(f"  offset {i:3d} (0x{i:02x}): 0x{val:08x} ({val})")

print(f"\nRaw header hex dump:")
for i in range(0, 192, 16):
    hexes = " ".join(f"{data[i+j]:02x}" for j in range(16))
    ascii_repr = "".join(chr(data[i+j]) if 32 <= data[i+j] < 127 else "." for j in range(16))
    print(f"  {i:3d}: {hexes}  {ascii_repr}")
