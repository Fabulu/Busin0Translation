import struct

# Look more carefully at BUSIN 0 font descriptor structure
b0_path = r"C:\Programmieren\wizardrytranslation\extracted\SLPM_653.78"
with open(b0_path, "rb") as f:
    b0_data = f.read()

exe_path = r"C:\Programmieren\wizardrytranslation\extracted_busin1\SLUS_202.59"
with open(exe_path, "rb") as f:
    exe_data = f.read()

# BUSIN 0 font descriptors at 0x3C0700 - dump more entries to understand the structure
print("=== BUSIN 0 Font Descriptors (0x3C0700) - all entries ===")
print("Format: 28 bytes each, LE uint32 x 7")
print("Known: field0 has width-like values (0x22=34, 0x21=33, 0x24=36, 0x2B=43)")
print("       field1 has height/pitch? (0x10=16, 0x20=32)")
print()

off = 0x3C0700
entry_count = 0
while True:
    chunk = b0_data[off:off+28]
    vals = struct.unpack("<7I", chunk)
    # Stop when we hit something that doesn't look like a descriptor
    if vals[0] == 0 and vals[1] == 0:
        break
    if entry_count > 20:
        break
    # Parse the packed fields
    v0 = vals[0]
    # v0 seems packed: low 16 bits and high 16 bits
    v0_lo = v0 & 0xFFFF
    v0_hi = (v0 >> 16) & 0xFFFF
    v1_lo = vals[1] & 0xFFFF
    v1_hi = (vals[1] >> 16) & 0xFFFF
    print(f"  Entry {entry_count} @0x{off:06X}: "
          f"[{v0_hi:04X}:{v0_lo:04X}] [{v1_hi:04X}:{v1_lo:04X}] "
          f"[{vals[2]:08X}] [{vals[3]:08X}] [{vals[4]:08X}] [{vals[5]:08X}] [{vals[6]:08X}]")
    off += 28
    entry_count += 1

print(f"\nTotal B0 descriptor entries: {entry_count}")
print(f"End of descriptors at: 0x{off:06X}")

# Now look at glyph table
print(f"\n=== BUSIN 0 Glyph Table (0x3C0870) ===")
off = 0x3C0870
count = 0
while off + 2 <= len(b0_data):
    val = struct.unpack("<H", b0_data[off:off+2])[0]
    if count < 100:
        print(f"  [{count:4d}] 0x{val:04X} ({val})")
    if val == 0xFFFF:  # possible terminator
        if count > 50:
            print(f"  ... possible terminator at [{count}]")
            break
    count += 1
    off += 2
    if count > 5000:
        print(f"  ... stopped at {count} entries")
        break

print(f"\nTotal glyph table entries scanned: {count}")

# Now search BUSIN 1 more specifically
# The BUSIN 0 descriptor has: 0x0002 in high word of first field
# Look for similar patterns in BUSIN 1
print("\n\n=== BUSIN 1: Search for font descriptors with 0x0002 prefix ===")
pattern = b'\x02\x00'  # LE 0x0002
hits_0002 = []
for off in range(0x3B0000, min(0x4D0000, len(exe_data)) - 28):
    # Check for packed value like BUSIN 0: 0x00XX0002
    val = struct.unpack("<I", exe_data[off:off+4])[0]
    hi = (val >> 16) & 0xFFFF
    lo = val & 0xFFFF
    if lo == 2 and 0x10 <= hi <= 0x40:
        # This looks like it could be a font descriptor first field
        # Check second field similarly
        val2 = struct.unpack("<I", exe_data[off+4:off+8])[0]
        hi2 = (val2 >> 16) & 0xFFFF
        lo2 = val2 & 0xFFFF
        if lo2 in (0x10, 0x20, 0x30, 0x40, 0x50, 0x60, 0x70, 0x80) and hi2 <= 0x100:
            hits_0002.append(off)

print(f"Found {len(hits_0002)} potential font descriptor entries")
for h in hits_0002[:30]:
    vals = struct.unpack("<7I", exe_data[h:h+28])
    print(f"  0x{h:06X}: {' '.join(f'{v:08X}' for v in vals)}")

# Also search wider - the BUSIN 1 EXE is larger, descriptors might be elsewhere
print("\n=== BUSIN 1: Wider search (0x000000-0x4CE1A0) ===")
hits_wide = []
for off in range(0, len(exe_data) - 28, 4):
    val = struct.unpack("<I", exe_data[off:off+4])[0]
    hi = (val >> 16) & 0xFFFF
    lo = val & 0xFFFF
    if lo == 2 and 0x10 <= hi <= 0x40:
        val2 = struct.unpack("<I", exe_data[off+4:off+8])[0]
        hi2 = (val2 >> 16) & 0xFFFF
        lo2 = val2 & 0xFFFF
        if lo2 in (0x10, 0x20, 0x30, 0x40, 0x50, 0x60, 0x70, 0x80) and hi2 <= 0x100:
            # Check if third field looks like color/flags (80808080)
            v3 = struct.unpack("<I", exe_data[off+12:off+16])[0]
            if v3 == 0x80808080:
                hits_wide.append(off)

print(f"Found {len(hits_wide)} matches with 80808080 color field")
for h in hits_wide[:30]:
    vals = struct.unpack("<7I", exe_data[h:h+28])
    print(f"  0x{h:06X}: {' '.join(f'{v:08X}' for v in vals)}")

# Broader: search for 80808080 pattern anywhere in expected range
print("\n=== BUSIN 1: Search for 0x80808080 in font data range ===")
magic = struct.pack("<I", 0x80808080)
hits_magic = []
for off in range(0x3B0000, min(0x4D0000, len(exe_data))):
    if exe_data[off:off+4] == magic:
        hits_magic.append(off)

print(f"Found {len(hits_magic)} occurrences of 80808080")
for h in hits_magic[:40]:
    # Show context: 12 bytes before and 16 after
    ctx_start = max(0, h - 12)
    ctx = exe_data[ctx_start:h+16]
    print(f"  0x{h:06X}: [-12] {ctx.hex()}")

# Search entire EXE for 80808080
print("\n=== BUSIN 1: Search entire EXE for 0x80808080 ===")
all_magic = []
for off in range(0, len(exe_data) - 4):
    if exe_data[off:off+4] == magic:
        all_magic.append(off)
print(f"Total 80808080 occurrences: {len(all_magic)}")
for h in all_magic[:50]:
    print(f"  0x{h:06X}")

# The 0x3B8A44 hit looked interesting - had ASCII-like values
# Let's look at that area more carefully
print("\n=== Interesting area near 0x3B8A44 ===")
off = 0x3B8A00
for i in range(20):
    vals = [struct.unpack("<H", exe_data[off+j*2:off+j*2+2])[0] for j in range(10)]
    ascii_str = ""
    for v in vals:
        if 0x20 <= v < 0x7F:
            ascii_str += chr(v)
        else:
            ascii_str += "."
    print(f"  0x{off:06X}: {[f'{v:04X}' for v in vals]}  '{ascii_str}'")
    off += 20

print("\nDone part 2.")
