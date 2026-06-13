"""
Compare the working rebuild_test ISO with the v81 ISO.
Focus on: EXE differences, PACKDATA positioning in ISO, BSN2_0.DSI overlap.
"""
import struct, os

os.chdir('C:/Programmieren/wizardrytranslation')

SECTOR = 2048
ISO_SECTOR = 2048

# Check if rebuild_test ISO exists
rebuild_test = 'build/BUSIN0_EN_rebuild_test.iso'
v81 = 'build/BUSIN0_EN_v9.iso'

for path in [rebuild_test, v81]:
    if os.path.exists(path):
        print(f"{os.path.basename(path)}: {os.path.getsize(path):,} bytes")
    else:
        print(f"{path}: NOT FOUND")

if not os.path.exists(rebuild_test) or not os.path.exists(v81):
    print("Cannot compare - missing ISO(s)")
    exit()

# Read EXE from both ISOs (SLPM_653.78)
# Need to find the EXE location. Usually at a known LBA.
# Let's read the ISO filesystem to find SLPM_653.78
def find_file_in_iso(iso_path, filename):
    """Simple ISO9660 search for a file by name."""
    with open(iso_path, 'rb') as f:
        # Read Primary Volume Descriptor at sector 16
        f.seek(16 * 2048)
        pvd = f.read(2048)
        # Root directory record is at offset 156
        root_lba = struct.unpack_from('<I', pvd, 156 + 2)[0]
        root_size = struct.unpack_from('<I', pvd, 156 + 10)[0]

        # Read root directory
        f.seek(root_lba * 2048)
        dir_data = f.read(root_size)

        offset = 0
        while offset < len(dir_data):
            rec_len = dir_data[offset]
            if rec_len == 0:
                # Skip to next sector
                offset = ((offset // 2048) + 1) * 2048
                if offset >= len(dir_data):
                    break
                continue
            name_len = dir_data[offset + 32]
            name = dir_data[offset + 33:offset + 33 + name_len].decode('ascii', errors='replace')
            lba = struct.unpack_from('<I', dir_data, offset + 2)[0]
            size = struct.unpack_from('<I', dir_data, offset + 10)[0]
            if filename.upper() in name.upper():
                return lba, size
            offset += rec_len
    return None, None

# Find EXE
exe_lba_w, exe_size_w = find_file_in_iso(rebuild_test, 'SLPM_653.78')
exe_lba_b, exe_size_b = find_file_in_iso(v81, 'SLPM_653.78')
print(f"\nEXE in working: LBA={exe_lba_w}, size={exe_size_w}")
print(f"EXE in broken:  LBA={exe_lba_b}, size={exe_size_b}")

# Compare EXE data
if exe_lba_w and exe_lba_b:
    with open(rebuild_test, 'rb') as f:
        f.seek(exe_lba_w * 2048)
        exe_w = f.read(exe_size_w)
    with open(v81, 'rb') as f:
        f.seek(exe_lba_b * 2048)
        exe_b = f.read(exe_size_b)

    if exe_w == exe_b:
        print("EXE: IDENTICAL")
    else:
        diff_count = sum(1 for a, b in zip(exe_w, exe_b) if a != b)
        print(f"EXE: {diff_count} bytes differ")
        # Find first differences
        diffs = []
        for i in range(min(len(exe_w), len(exe_b))):
            if exe_w[i] != exe_b[i]:
                diffs.append(i)
                if len(diffs) >= 50:
                    break
        print(f"  First diffs at offsets: {[hex(d) for d in diffs[:20]]}")

        # Check if diffs are in the known patch regions
        # patch_exe.py patches specific offsets
        print(f"  Diff regions:")
        region_start = None
        region_count = 0
        for i in range(min(len(exe_w), len(exe_b))):
            if exe_w[i] != exe_b[i]:
                if region_start is None:
                    region_start = i
                    region_count = 1
                else:
                    region_count += 1
            else:
                if region_start is not None:
                    print(f"    0x{region_start:06X} - 0x{region_start+region_count-1:06X} ({region_count} bytes)")
                    region_start = None
                    region_count = 0
        if region_start is not None:
            print(f"    0x{region_start:06X} - 0x{region_start+region_count-1:06X} ({region_count} bytes)")

# Find PACKDATA.DIG
pd_lba_w, pd_size_w = find_file_in_iso(rebuild_test, 'PACKDATA.DIG')
pd_lba_b, pd_size_b = find_file_in_iso(v81, 'PACKDATA.DIG')
print(f"\nPACKDATA in working: LBA={pd_lba_w}, size={pd_size_w}")
print(f"PACKDATA in broken:  LBA={pd_lba_b}, size={pd_size_b}")

# Find BSN2_0.DSI
bsn_lba_w, bsn_size_w = find_file_in_iso(rebuild_test, 'BSN2_0.DSI')
bsn_lba_b, bsn_size_b = find_file_in_iso(v81, 'BSN2_0.DSI')
print(f"\nBSN2_0.DSI in working: LBA={bsn_lba_w}, size={bsn_size_w}")
print(f"BSN2_0.DSI in broken:  LBA={bsn_lba_b}, size={bsn_size_b}")

if pd_lba_w and bsn_lba_w:
    pd_end_w = pd_lba_w + (pd_size_w + 2047) // 2048
    pd_end_b = pd_lba_b + (pd_size_b + 2047) // 2048
    print(f"\nPACKDATA end sector (working): {pd_end_w}")
    print(f"PACKDATA end sector (broken):  {pd_end_b}")
    print(f"BSN2_0.DSI start sector: {bsn_lba_w}")
    if pd_end_b > bsn_lba_w:
        overlap = pd_end_b - bsn_lba_w
        print(f"\n*** PACKDATA OVERFLOWS INTO BSN2_0.DSI by {overlap} sectors ({overlap*2048} bytes)! ***")
        print(f"    This corrupts the first {overlap*2048} bytes of BSN2_0.DSI audio data!")
    else:
        print(f"  No overflow (gap = {bsn_lba_w - pd_end_b} sectors)")
