#!/usr/bin/env python3
"""Search ISO for intro text - check ELF and other files outside PACKDATA."""
import struct
import sys
import os
sys.stdout.reconfigure(encoding='utf-8')

iso_path = 'C:/Programmieren/wizardrytranslation/Busin 0 - Wizardry Alternative Neo (Japan) (v2.01).iso'

# Read first ~50MB of ISO (typically contains ELF and small data files)
# The ELF is usually in the first few MB
print(f"Reading ISO: {iso_path}")
with open(iso_path, 'rb') as f:
    # Read first 100MB to cover everything before PACKDATA.DIG
    iso_data = f.read(100 * 1024 * 1024)

print(f"Read {len(iso_data)} bytes ({len(iso_data)/1024/1024:.1f} MB)")

# Search for the intro text
sentence = '\u305d\u306e\u60b2\u60e8\u306a\u6226\u4e89\u306f\u30d0\u30f3\u30af\u30a9\u30fc\u306e\u6226\u5f79\u3068\u4eba\u3005\u306b\u8a18\u61b6\u3055\u308c\u308b\u3002'

for enc in ['shift-jis', 'euc-jp', 'utf-16-le', 'utf-16-be', 'utf-8']:
    try:
        target = sentence.encode(enc)
        pos = iso_data.find(target)
        if pos >= 0:
            print(f"  FULL SENTENCE ({enc}) in ISO at 0x{pos:08X}")
    except:
        pass

# Search for individual words
for word_name, word in [('hisan', '\u60b2\u60e8'), ('seneki', '\u6226\u5f79'),
                        ('bankuoo', '\u30d0\u30f3\u30af\u30a9\u30fc'),
                        ('kioku', '\u8a18\u61b6'), ('sensou', '\u6226\u4e89'),
                        ('hitobito', '\u4eba\u3005')]:
    for enc in ['shift-jis', 'euc-jp', 'utf-16-le']:
        try:
            target = word.encode(enc)
            pos = 0
            count = 0
            while count < 5:
                pos = iso_data.find(target, pos)
                if pos < 0:
                    break
                ctx = iso_data[max(0,pos-20):pos+len(target)+20]
                try:
                    decoded = ctx.decode(enc, errors='replace')
                    print(f"  '{word_name}' ({enc}) at ISO 0x{pos:08X}: {decoded[:60]}")
                except:
                    print(f"  '{word_name}' ({enc}) at ISO 0x{pos:08X}: {ctx.hex()}")
                pos += 1
                count += 1
        except:
            pass

# Look for the SLPS/SLPM ELF filename
print("\n=== Looking for ELF in ISO ===")
for marker in [b'SLPS_', b'SLPM_', b'SCPS_']:
    pos = iso_data.find(marker)
    if pos >= 0:
        name = iso_data[pos:pos+20].split(b'\x00')[0].split(b';')[0]
        print(f"  Found ELF name: {name.decode('ascii', errors='replace')} at 0x{pos:08X}")

# Look for PS2 ELF header (7F 45 4C 46)
elf_sig = b'\x7fELF'
pos = 0
while True:
    pos = iso_data.find(elf_sig, pos)
    if pos < 0:
        break
    print(f"  ELF header at ISO 0x{pos:08X}")
    # Check ELF size - read program headers
    if pos + 64 < len(iso_data):
        e_phoff = struct.unpack_from('<I', iso_data, pos + 28)[0]
        e_phentsize = struct.unpack_from('<H', iso_data, pos + 42)[0]
        e_phnum = struct.unpack_from('<H', iso_data, pos + 44)[0]
        print(f"    phoff={e_phoff}, phentsize={e_phentsize}, phnum={e_phnum}")
        # Find total size from program headers
        max_end = 0
        for i in range(e_phnum):
            ph_off = pos + e_phoff + i * e_phentsize
            if ph_off + e_phentsize <= len(iso_data):
                p_offset = struct.unpack_from('<I', iso_data, ph_off + 4)[0]
                p_filesz = struct.unpack_from('<I', iso_data, ph_off + 16)[0]
                end = p_offset + p_filesz
                if end > max_end:
                    max_end = end
        print(f"    Estimated ELF size: {max_end} bytes ({max_end/1024/1024:.1f} MB)")

        # Search within the ELF for our text
        elf_data = iso_data[pos:pos+max_end]
        for word_name, word in [('hisan', '\u60b2\u60e8'), ('seneki', '\u6226\u5f79'),
                                ('bankuoo', '\u30d0\u30f3\u30af\u30a9\u30fc'),
                                ('sensou', '\u6226\u4e89')]:
            for enc in ['shift-jis', 'euc-jp', 'utf-16-le']:
                try:
                    target = word.encode(enc)
                    fpos = elf_data.find(target)
                    if fpos >= 0:
                        ctx = elf_data[max(0,fpos-20):fpos+len(target)+20]
                        try:
                            decoded = ctx.decode(enc, errors='replace')
                        except:
                            decoded = ctx.hex()
                        print(f"    '{word_name}' ({enc}) in ELF at +0x{fpos:08X}: {decoded[:60]}")
                except:
                    pass
    pos += 4

print("\n=== Done ===")
