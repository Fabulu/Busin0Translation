"""
Verify the v9 ISO's file layout integrity.
Check that PACKDATA, BSN2_0.DSI, and EXE don't overlap and are correct.
Also check if the EXE patches could cause a VIF crash.
"""
import struct, os

os.chdir('C:/Programmieren/wizardrytranslation')
SECTOR = 2048

iso_path = 'build/BUSIN0_EN_v9.iso'

with open(iso_path, 'rb') as iso:
    # Read PVD
    iso.seek(16 * SECTOR)
    pvd = iso.read(SECTOR)
    root_lba = struct.unpack_from('<I', pvd, 158)[0]
    root_size = struct.unpack_from('<I', pvd, 166)[0]
    vol_size = struct.unpack_from('<I', pvd, 80)[0]
    print(f"Volume size: {vol_size} sectors ({vol_size*SECTOR:,} bytes)")

    # Read directory
    iso.seek(root_lba * SECTOR)
    root_dir = iso.read(root_size)
    entries = []
    pos = 0
    while pos < len(root_dir):
        rec_len = root_dir[pos]
        if rec_len == 0:
            break
        name_len = root_dir[pos + 32]
        name = root_dir[pos + 33:pos + 33 + name_len].decode('ascii', errors='replace')
        lba = struct.unpack_from('<I', root_dir, pos + 2)[0]
        size = struct.unpack_from('<I', root_dir, pos + 10)[0]
        lba_be = struct.unpack_from('>I', root_dir, pos + 6)[0]
        size_be = struct.unpack_from('>I', root_dir, pos + 14)[0]
        end_lba = lba + (size + SECTOR - 1) // SECTOR
        entries.append({
            'name': name, 'lba': lba, 'size': size, 'end': end_lba,
            'lba_be': lba_be, 'size_be': size_be
        })
        pos += rec_len

    # Print file layout
    print(f"\nISO File Layout:")
    print(f"{'Name':<20} {'LBA':>10} {'End LBA':>10} {'Size':>15} {'LE=BE?':>8}")
    for e in sorted(entries, key=lambda x: x['lba']):
        le_be_match = "OK" if (e['lba'] == e['lba_be'] and e['size'] == e['size_be']) else "MISMATCH"
        print(f"  {e['name']:<18} {e['lba']:>10} {e['end']:>10} {e['size']:>15,} {le_be_match:>8}")

    # Check for overlaps
    sorted_entries = sorted(entries, key=lambda x: x['lba'])
    print(f"\nOverlap check:")
    for i in range(len(sorted_entries) - 1):
        a = sorted_entries[i]
        b = sorted_entries[i+1]
        if a['end'] > b['lba'] and a['name'] != b['name']:
            print(f"  OVERLAP: {a['name']} (end={a['end']}) overlaps {b['name']} (start={b['lba']})")
        else:
            gap = b['lba'] - a['end']
            if gap < 0:
                print(f"  OVERLAP: {a['name']} -> {b['name']} by {-gap} sectors")

    # Verify PACKDATA content at its declared start
    pack = [e for e in entries if 'PACKDATA' in e['name']][0]
    iso.seek(pack['lba'] * SECTOR)
    pack_hdr = iso.read(64)
    print(f"\nPACKDATA header (first 64 bytes): {pack_hdr[:32].hex()}")

    # Verify BSN2_0.DSI content at its declared start
    bsn = [e for e in entries if 'BSN2_0' in e['name']]
    if bsn:
        bsn = bsn[0]
        iso.seek(bsn['lba'] * SECTOR)
        bsn_hdr = iso.read(64)
        print(f"BSN2_0.DSI header (first 64 bytes): {bsn_hdr[:32].hex()}")

        # Check if BSN2_0 data looks like audio or like PACKDATA overflow
        # Audio data typically starts with a specific header or is immediately non-zero
        # PACKDATA overflow would look like resource data

        # Also read what's at the ORIGINAL BSN2_0 position (LBA 426020)
        iso.seek(426020 * SECTOR)
        old_bsn_pos = iso.read(64)
        print(f"Data at original BSN2_0 LBA 426020: {old_bsn_pos[:32].hex()}")

    # Now check the EXE patches specifically
    exe = [e for e in entries if 'SLPM' in e['name']][0]
    print(f"\nEXE Analysis:")
    print(f"  LBA: {exe['lba']}, size: {exe['size']:,}")

    # Read the EXE
    iso.seek(exe['lba'] * SECTOR)
    exe_data = iso.read(exe['size'])

    # Check the patched regions from build_v9.py comparison
    # Diffs were at: 0x363B78, 0x363C3C, 0x363EF8, 0x363FBC (SJIS string patches)
    # 0x3C289E, 0x3C28E6 (menu struct patches)
    # 0x3DB180 (single byte)
    # 0x3DDCA7-0x3DDCBD, etc (more SJIS patches)

    # Check if EXE at 0x363B78 region looks reasonable
    # These offsets are relative to file start; EXE loads at 0x100000 virtual
    for off in [0x363B78, 0x3C289E, 0x3DB180, 0x3DDCA7]:
        if off < len(exe_data):
            chunk = exe_data[off:off+16]
            print(f"  EXE[0x{off:06X}]: {chunk.hex()} = {chunk}")

    # Read original EXE for comparison
    orig_iso = 'Busin 0 - Wizardry Alternative Neo (Japan) (v2.01).iso'
    if os.path.exists(orig_iso):
        with open(orig_iso, 'rb') as f:
            f.seek(16 * SECTOR)
            pvd2 = f.read(SECTOR)
            rlba2 = struct.unpack_from('<I', pvd2, 158)[0]
            rsize2 = struct.unpack_from('<I', pvd2, 166)[0]
            f.seek(rlba2 * SECTOR)
            rdir2 = f.read(rsize2)
            p = 0
            while p < len(rdir2):
                rl = rdir2[p]
                if rl == 0:
                    break
                nl = rdir2[p + 32]
                nm = rdir2[p + 33:p + 33 + nl].decode('ascii', errors='replace')
                if 'SLPM' in nm:
                    elba = struct.unpack_from('<I', rdir2, p + 2)[0]
                    esz = struct.unpack_from('<I', rdir2, p + 10)[0]
                    f.seek(elba * SECTOR)
                    orig_exe = f.read(esz)
                    for off in [0x363B78, 0x3C289E, 0x3DB180, 0x3DDCA7]:
                        if off < len(orig_exe):
                            chunk = orig_exe[off:off+16]
                            print(f"  ORIG[0x{off:06X}]: {chunk.hex()} = {chunk}")
                    break
                p += rl
