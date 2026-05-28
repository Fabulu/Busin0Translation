#!/usr/bin/env python3
"""Search for ELF in ISO and search the ENTIRE disc for intro text."""
import struct
import sys
sys.stdout.reconfigure(encoding='utf-8')

iso_path = 'C:/Programmieren/wizardrytranslation/Busin 0 - Wizardry Alternative Neo (Japan) (v2.01).iso'

# Read the ISO filesystem to find file locations
# ISO 9660 primary volume descriptor is at sector 16 (0x8000)
with open(iso_path, 'rb') as f:
    f.seek(0x8000)
    pvd = f.read(2048)

# Check PVD
print(f"PVD identifier: {pvd[1:6]}")
root_dir_record = pvd[156:156+34]
root_lba = struct.unpack_from('<I', root_dir_record, 2)[0]
root_size = struct.unpack_from('<I', root_dir_record, 10)[0]
print(f"Root dir: LBA={root_lba}, size={root_size}")

# Read root directory
with open(iso_path, 'rb') as f:
    f.seek(root_lba * 2048)
    root_dir = f.read(root_size)

# Parse directory entries
print("\n=== Root directory entries ===")
pos = 0
files = []
while pos < len(root_dir):
    rec_len = root_dir[pos]
    if rec_len == 0:
        # Pad to next sector
        pos = ((pos // 2048) + 1) * 2048
        if pos >= len(root_dir):
            break
        continue
    ext_attr_len = root_dir[pos + 1]
    lba = struct.unpack_from('<I', root_dir, pos + 2)[0]
    size = struct.unpack_from('<I', root_dir, pos + 10)[0]
    flags = root_dir[pos + 25]
    name_len = root_dir[pos + 32]
    name = root_dir[pos + 33:pos + 33 + name_len].decode('ascii', errors='replace')
    is_dir = (flags & 2) != 0
    print(f"  {name:30s} LBA={lba:8d} size={size:12d} {'DIR' if is_dir else 'FILE'}")
    files.append((name, lba, size, is_dir))
    pos += rec_len

# Find and read the ELF file (SLPM_653.78)
print("\n=== Reading ELF file ===")
for name, lba, size, is_dir in files:
    if 'SLPM' in name or 'SLPS' in name:
        print(f"Reading {name} from LBA {lba}, size {size}")
        with open(iso_path, 'rb') as f:
            f.seek(lba * 2048)
            elf_data = f.read(size)
        print(f"ELF size: {len(elf_data)} bytes ({len(elf_data)/1024/1024:.1f} MB)")

        # Search for text in ELF
        sentence = '\u305d\u306e\u60b2\u60e8\u306a\u6226\u4e89\u306f\u30d0\u30f3\u30af\u30a9\u30fc\u306e\u6226\u5f79\u3068\u4eba\u3005\u306b\u8a18\u61b6\u3055\u308c\u308b\u3002'

        for enc in ['shift-jis', 'euc-jp', 'utf-16-le', 'utf-16-be', 'utf-8']:
            try:
                target = sentence.encode(enc)
                fpos = elf_data.find(target)
                if fpos >= 0:
                    print(f"  FOUND ({enc}) at ELF+0x{fpos:08X}!")
            except:
                pass

        # Search for individual words
        for word_name, word in [('hisan', '\u60b2\u60e8'), ('seneki', '\u6226\u5f79'),
                                ('bankuoo', '\u30d0\u30f3\u30af\u30a9\u30fc'),
                                ('kioku', '\u8a18\u61b6'), ('sensou', '\u6226\u4e89'),
                                ('hitobito', '\u4eba\u3005'),
                                ('sono', '\u305d\u306e')]:
            for enc in ['shift-jis']:
                try:
                    target = word.encode(enc)
                    fpos = 0
                    count = 0
                    while count < 10:
                        fpos = elf_data.find(target, fpos)
                        if fpos < 0:
                            break
                        ctx = elf_data[max(0,fpos-10):fpos+len(target)+30]
                        try:
                            decoded = ctx.decode('shift-jis', errors='replace')
                        except:
                            decoded = ''
                        print(f"  '{word_name}' in ELF at +0x{fpos:08X}: {decoded[:60]}")
                        fpos += 1
                        count += 1
                except:
                    pass

        break

# === Also search in the entire ISO for the sentence ===
print("\n=== Searching entire ISO for 'seneki' (SJIS) ===")
target = '\u6226\u5f79'.encode('shift-jis')
with open(iso_path, 'rb') as f:
    chunk_size = 10 * 1024 * 1024
    offset = 0
    while True:
        # Read with overlap to avoid missing matches at boundaries
        f.seek(max(0, offset - 10))
        chunk = f.read(chunk_size + 20)
        if len(chunk) <= 20:
            break
        search_start = 10 if offset > 0 else 0
        pos = search_start
        while True:
            pos = chunk.find(target, pos)
            if pos < 0:
                break
            abs_pos = offset - (10 if offset > 0 else 0) + pos
            ctx = chunk[max(0,pos-20):pos+24]
            try:
                decoded = ctx.decode('shift-jis', errors='replace')
                print(f"  ISO 0x{abs_pos:08X}: {decoded[:60]}")
            except:
                print(f"  ISO 0x{abs_pos:08X}: {ctx.hex()}")
            pos += 1
        offset += chunk_size

print("\n=== Done ===")
