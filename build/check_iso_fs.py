"""Check ISO 9660 filesystem structure for consistency."""
import struct
import sys

def parse_iso(path, label):
    print(f"\n{'='*80}")
    print(f"  ISO: {label}")
    print(f"{'='*80}")

    with open(path, 'rb') as f:
        # ---- PVD at sector 16 ----
        f.seek(16 * 2048)
        pvd = f.read(2048)

        vd_type = pvd[0]
        vd_id = pvd[1:6]
        vd_ver = pvd[6]
        print(f"\nPrimary Volume Descriptor (sector 16):")
        print(f"  Type: {vd_type}  ID: {vd_id}  Version: {vd_ver}")

        sys_id = pvd[8:40].decode('ascii', errors='replace').strip()
        vol_id = pvd[40:72].decode('ascii', errors='replace').strip()
        print(f'  System ID: "{sys_id}"')
        print(f'  Volume ID: "{vol_id}"')

        vol_space_le = struct.unpack_from('<I', pvd, 80)[0]
        vol_space_be = struct.unpack_from('>I', pvd, 84)[0]
        print(f"  Volume Space Size: {vol_space_le} sectors (LE), {vol_space_be} (BE)")

        set_size = struct.unpack_from('<H', pvd, 120)[0]
        seq_num = struct.unpack_from('<H', pvd, 124)[0]
        block_size = struct.unpack_from('<H', pvd, 128)[0]
        print(f"  Set Size: {set_size}  Seq#: {seq_num}  Block Size: {block_size}")

        pt_size_le = struct.unpack_from('<I', pvd, 132)[0]
        pt_size_be = struct.unpack_from('>I', pvd, 136)[0]
        print(f"  Path Table Size: {pt_size_le} bytes (LE), {pt_size_be} (BE)")

        l_table_lba = struct.unpack_from('<I', pvd, 140)[0]
        l_table_opt = struct.unpack_from('<I', pvd, 144)[0]
        m_table_lba = struct.unpack_from('>I', pvd, 148)[0]
        m_table_opt = struct.unpack_from('>I', pvd, 152)[0]
        print(f"  L-Table LBA: {l_table_lba} (optional: {l_table_opt})")
        print(f"  M-Table LBA: {m_table_lba} (optional: {m_table_opt})")

        # Root directory record at offset 156
        root_rec = pvd[156:190]
        root_lba = struct.unpack_from('<I', root_rec, 2)[0]
        root_size = struct.unpack_from('<I', root_rec, 10)[0]
        print(f"  Root Dir LBA: {root_lba}  Size: {root_size} bytes")

        pub_id = pvd[318:446].decode('ascii', errors='replace').strip()
        prep_id = pvd[446:574].decode('ascii', errors='replace').strip()
        app_id = pvd[574:702].decode('ascii', errors='replace').strip()
        if pub_id: print(f'  Publisher: "{pub_id}"')
        if prep_id: print(f'  Preparer: "{prep_id}"')
        if app_id: print(f'  Application: "{app_id}"')

        # ---- Check for SVD at sector 17+ ----
        print(f"\nChecking for additional Volume Descriptors:")
        for sec in range(17, 25):
            f.seek(sec * 2048)
            vd = f.read(2048)
            vd_t = vd[0]
            if vd_t == 255:
                print(f"  Sector {sec}: VD Set Terminator")
                break
            elif vd_t == 2:
                svd_root = vd[156:190]
                svd_root_lba = struct.unpack_from('<I', svd_root, 2)[0]
                svd_root_size = struct.unpack_from('<I', svd_root, 10)[0]
                # Check SVD path tables too
                svd_l_table = struct.unpack_from('<I', vd, 140)[0]
                svd_m_table = struct.unpack_from('>I', vd, 148)[0]
                svd_pt_size = struct.unpack_from('<I', vd, 132)[0]
                print(f"  Sector {sec}: Supplementary VD!")
                print(f"    Root LBA={svd_root_lba} Size={svd_root_size}")
                print(f"    L-Table={svd_l_table} M-Table={svd_m_table} PT-Size={svd_pt_size}")
            elif vd_t == 0:
                boot_sys = vd[7:39].decode('ascii', errors='replace').strip()
                print(f"  Sector {sec}: Boot Record (sys={boot_sys})")
            elif vd_t == 1:
                print(f"  Sector {sec}: Another PVD?!")
            else:
                print(f"  Sector {sec}: Unknown VD type {vd_t}")

        # ---- Parse root directory ----
        print(f"\nRoot Directory entries (LBA {root_lba}, {root_size} bytes):")
        f.seek(root_lba * 2048)
        dir_data = f.read(root_size)

        entries = []
        pos = 0
        while pos < len(dir_data):
            rec_len = dir_data[pos]
            if rec_len == 0:
                next_sec = ((pos // 2048) + 1) * 2048
                if next_sec >= len(dir_data):
                    break
                pos = next_sec
                continue

            rec = dir_data[pos:pos+rec_len]
            ext_attr_len = rec[1]
            lba = struct.unpack_from('<I', rec, 2)[0]
            lba_be = struct.unpack_from('>I', rec, 6)[0]
            size = struct.unpack_from('<I', rec, 10)[0]
            size_be = struct.unpack_from('>I', rec, 14)[0]
            flags = rec[25]
            name_len = rec[32]
            name_bytes = rec[33:33+name_len]

            if name_len == 1 and name_bytes[0] == 0:
                name = '.'
            elif name_len == 1 and name_bytes[0] == 1:
                name = '..'
            else:
                name = name_bytes.decode('ascii', errors='replace')
                if ';' in name:
                    name_clean = name[:name.index(';')]
                else:
                    name_clean = name
                name = name_clean

            is_dir = bool(flags & 0x02)
            entry_type = 'DIR' if is_dir else 'FILE'

            # Check LE/BE consistency
            lba_ok = "ok" if lba == lba_be else f"MISMATCH BE={lba_be}"
            size_ok = "ok" if size == size_be else f"MISMATCH BE={size_be}"

            print(f"  {entry_type:4s}  LBA={lba:>8d} ({lba_ok})  Size={size:>12d} ({size_ok})  ExtAttr={ext_attr_len}  Name=\"{name}\"")
            entries.append((name, lba, size, is_dir, ext_attr_len))

            pos += rec_len

        # ---- Parse L-Table (path table) ----
        print(f"\nL-Table (Path Table) at LBA {l_table_lba}, size {pt_size_le}:")
        f.seek(l_table_lba * 2048)
        pt_data = f.read(pt_size_le)

        pt_pos = 0
        pt_idx = 1
        while pt_pos < len(pt_data):
            if pt_pos + 8 > len(pt_data):
                break
            name_len_pt = pt_data[pt_pos]
            ext_attr_pt = pt_data[pt_pos+1]
            extent_lba = struct.unpack_from('<I', pt_data, pt_pos+2)[0]
            parent_dir = struct.unpack_from('<H', pt_data, pt_pos+6)[0]

            if name_len_pt == 0:
                break

            pt_name_bytes = pt_data[pt_pos+8:pt_pos+8+name_len_pt]
            if name_len_pt == 1 and pt_name_bytes[0] == 0:
                pt_name = '<root>'
            else:
                pt_name = pt_name_bytes.decode('ascii', errors='replace')

            print(f"  [{pt_idx}] Parent={parent_dir}  LBA={extent_lba:>8d}  ExtAttr={ext_attr_pt}  Name=\"{pt_name}\"")

            pt_pos += 8 + name_len_pt
            if name_len_pt % 2 == 1:
                pt_pos += 1
            pt_idx += 1

        # ---- Parse M-Table too ----
        print(f"\nM-Table (Path Table BE) at LBA {m_table_lba}, size {pt_size_le}:")
        f.seek(m_table_lba * 2048)
        mpt_data = f.read(pt_size_le)

        pt_pos = 0
        pt_idx = 1
        while pt_pos < len(mpt_data):
            if pt_pos + 8 > len(mpt_data):
                break
            name_len_pt = mpt_data[pt_pos]
            ext_attr_pt = mpt_data[pt_pos+1]
            extent_lba = struct.unpack_from('>I', mpt_data, pt_pos+2)[0]  # BE!
            parent_dir = struct.unpack_from('>H', mpt_data, pt_pos+6)[0]  # BE!

            if name_len_pt == 0:
                break

            pt_name_bytes = mpt_data[pt_pos+8:pt_pos+8+name_len_pt]
            if name_len_pt == 1 and pt_name_bytes[0] == 0:
                pt_name = '<root>'
            else:
                pt_name = pt_name_bytes.decode('ascii', errors='replace')

            print(f"  [{pt_idx}] Parent={parent_dir}  LBA={extent_lba:>8d}  ExtAttr={ext_attr_pt}  Name=\"{pt_name}\"")

            pt_pos += 8 + name_len_pt
            if name_len_pt % 2 == 1:
                pt_pos += 1
            pt_idx += 1

        # ---- Check SYSTEM.CNF ----
        print(f"\nSYSTEM.CNF check:")
        for name, lba, size, is_dir, _ in entries:
            if 'SYSTEM' in name.upper() and 'CNF' in name.upper():
                f.seek(lba * 2048)
                cnf = f.read(min(size, 4096))
                cnf_text = cnf.decode('ascii', errors='replace')
                print(f"  Found SYSTEM.CNF at LBA {lba}:")
                for line in cnf_text.strip().split('\n'):
                    print(f"    {line.strip()}")
                if 'PACKDATA' in cnf_text.upper():
                    print(f"  ** SYSTEM.CNF references PACKDATA! **")
                else:
                    print(f"  (no PACKDATA reference)")

        # ---- Check for duplicate PACKDATA entries ----
        packdata_entries = [(n,l,s) for n,l,s,d,_ in entries if 'PACKDATA' in n.upper()]
        print(f"\nPACKDATA entries in root directory: {len(packdata_entries)}")
        for n,l,s in packdata_entries:
            print(f'  Name="{n}"  LBA={l}  Size={s} ({s/1024/1024:.1f} MB)')

        return {
            'root_lba': root_lba, 'root_size': root_size,
            'l_table': l_table_lba, 'm_table': m_table_lba,
            'pt_size': pt_size_le, 'vol_space': vol_space_le,
            'entries': entries
        }


orig = r'C:\Programmieren\wizardrytranslation\Busin 0 - Wizardry Alternative Neo (Japan) (v2.01).iso'
mega = r'C:\Programmieren\wizardrytranslation\build\TEST_mega_zero.iso'

r1 = parse_iso(orig, 'ORIGINAL')
r2 = parse_iso(mega, 'MEGA_ZERO')

# Compare
print(f"\n{'='*80}")
print(f"  COMPARISON: ORIGINAL vs MEGA_ZERO")
print(f"{'='*80}")
for key in ['root_lba', 'root_size', 'l_table', 'm_table', 'pt_size', 'vol_space']:
    v1, v2 = r1[key], r2[key]
    match = 'OK' if v1 == v2 else 'MISMATCH!'
    print(f"  {key}: orig={v1}  mega={v2}  [{match}]")

print(f"\nDirectory entry comparison:")
max_len = max(len(r1['entries']), len(r2['entries']))
for i in range(max_len):
    if i >= len(r1['entries']):
        n2, l2, s2, d2, x2 = r2['entries'][i]
        print(f"  [{i}] EXTRA in mega_zero: \"{n2}\" LBA={l2} Size={s2}")
        continue
    if i >= len(r2['entries']):
        n1, l1, s1, d1, x1 = r1['entries'][i]
        print(f"  [{i}] MISSING in mega_zero: \"{n1}\" LBA={l1} Size={s1}")
        continue

    n1, l1, s1, d1, x1 = r1['entries'][i]
    n2, l2, s2, d2, x2 = r2['entries'][i]
    diffs = []
    if n1 != n2: diffs.append(f"name {n1}!={n2}")
    if l1 != l2: diffs.append(f"LBA {l1}!={l2}")
    if s1 != s2: diffs.append(f"size {s1}!={s2}")
    if d1 != d2: diffs.append(f"type mismatch")
    if diffs:
        print(f'  [{i}] "{n1}" vs "{n2}": {" | ".join(diffs)}')
    else:
        print(f'  [{i}] "{n1}": identical')

# Also check the v9 build ISO
v9 = r'C:\Programmieren\wizardrytranslation\build\BUSIN0_EN_v9.iso'
import os
if os.path.exists(v9):
    r3 = parse_iso(v9, 'BUSIN0_EN_v9')
    print(f"\n{'='*80}")
    print(f"  COMPARISON: ORIGINAL vs v9 BUILD")
    print(f"{'='*80}")
    for key in ['root_lba', 'root_size', 'l_table', 'm_table', 'pt_size', 'vol_space']:
        v1, v2 = r1[key], r3[key]
        match = 'OK' if v1 == v2 else 'MISMATCH!'
        print(f"  {key}: orig={v1}  v9={v2}  [{match}]")

    print(f"\nDirectory entry comparison (orig vs v9):")
    max_len = max(len(r1['entries']), len(r3['entries']))
    for i in range(max_len):
        if i >= len(r1['entries']):
            n2, l2, s2, d2, x2 = r3['entries'][i]
            print(f"  [{i}] EXTRA in v9: \"{n2}\" LBA={l2} Size={s2}")
            continue
        if i >= len(r3['entries']):
            n1, l1, s1, d1, x1 = r1['entries'][i]
            print(f"  [{i}] MISSING in v9: \"{n1}\" LBA={l1} Size={s1}")
            continue

        n1, l1, s1, d1, x1 = r1['entries'][i]
        n2, l2, s2, d2, x2 = r3['entries'][i]
        diffs = []
        if n1 != n2: diffs.append(f"name {n1}!={n2}")
        if l1 != l2: diffs.append(f"LBA {l1}!={l2}")
        if s1 != s2: diffs.append(f"size {s1}!={s2}")
        if d1 != d2: diffs.append(f"type mismatch")
        if diffs:
            print(f'  [{i}] "{n1}" vs "{n2}": {" | ".join(diffs)}')
        else:
            print(f'  [{i}] "{n1}": identical')
