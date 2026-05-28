"""Search the EXE for instructions that reference the font width table address."""
import struct
import rabbitizer

exe = open('extracted/SLPM_653.78', 'rb').read()

# ELF mapping: file offset 0x80 -> vaddr 0x00100000
P_OFFSET = 0x80
P_VADDR = 0x00100000

def file_to_vaddr(foff):
    return P_VADDR + (foff - P_OFFSET)

# Look for the lbu instruction pattern: lbu $v0, -0x2340($v0) = 0x9042DCC0
# This references address 0x004EDCC0 (from lui 0x4E + offset -0x2340)
# which is likely a CLZ (count leading zeros) lookup table, not a font table

# Let's search for references to known font-related addresses
# First, find all 'lui' instructions that load common base addresses
print("Searching for font-related patterns...")

# Look for instructions near string "font" or width-related constants
# Common font width table patterns: loading a base address then indexing by glyph ID

# Search for specific patterns in the binary
# Font width tables often have entries like 0x0C, 0x0E, 0x10 (pixel widths)

# Let's look for lui instructions loading addresses in the data segment
# The EXE data segment likely starts after text
# Segment 0: filesz=0x3FDC80 so data goes to around 0x4FDC80 in vaddr space

# Search for "font" string in the binary
font_refs = []
for i in range(len(exe) - 4):
    if exe[i:i+4].lower() == b'font':
        context = exe[max(0,i-16):i+32]
        font_refs.append((i, context))
        if len(font_refs) > 20:
            break

print(f"\nFound {len(font_refs)} 'font' string references:")
for off, ctx in font_refs:
    vaddr = file_to_vaddr(off) if off >= P_OFFSET else off
    printable = ''.join(chr(b) if 32 <= b < 127 else '.' for b in ctx)
    print(f"  file 0x{off:06X} (vaddr 0x{vaddr:08X}): {printable}")

# Search for "width" string
width_refs = []
for i in range(len(exe) - 5):
    if exe[i:i+5].lower() == b'width':
        context = exe[max(0,i-16):i+32]
        width_refs.append((i, context))
        if len(width_refs) > 20:
            break

print(f"\nFound {len(width_refs)} 'width' string references:")
for off, ctx in width_refs:
    vaddr = file_to_vaddr(off) if off >= P_OFFSET else off
    printable = ''.join(chr(b) if 32 <= b < 127 else '.' for b in ctx)
    print(f"  file 0x{off:06X} (vaddr 0x{vaddr:08X}): {printable}")

# Also search for MSG-related strings
for needle in [b'.msg', b'MSG', b'glyph', b'char_w', b'FONT', b'.fnt']:
    refs = []
    for i in range(len(exe) - len(needle)):
        if exe[i:i+len(needle)] == needle:
            context = exe[max(0,i-8):i+40]
            refs.append((i, context))
            if len(refs) > 5:
                break
    if refs:
        print(f"\nFound {len(refs)} '{needle.decode()}' references:")
        for off, ctx in refs:
            vaddr = file_to_vaddr(off) if off >= P_OFFSET else off
            printable = ''.join(chr(b) if 32 <= b < 127 else '.' for b in ctx)
            print(f"  file 0x{off:06X} (vaddr 0x{vaddr:08X}): {printable}")
