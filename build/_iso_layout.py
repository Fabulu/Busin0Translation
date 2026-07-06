"""List ISO files in LBA order; show overflow landing zone around PACKDATA."""
import struct, sys, os

def list_files(path):
    files = []
    with open(path, 'rb') as f:
        f.seek(16 * 2048)
        pvd = f.read(2048)
        vol_space = struct.unpack_from('<I', pvd, 80)[0]
        root_lba = struct.unpack_from('<I', pvd, 158)[0]
        root_size = struct.unpack_from('<I', pvd, 166)[0]
        f.seek(root_lba * 2048)
        dir_data = f.read(root_size)
        pos = 0
        while pos < len(dir_data):
            rl = dir_data[pos]
            if rl == 0:
                nxt = ((pos // 2048) + 1) * 2048
                if nxt >= len(dir_data):
                    break
                pos = nxt
                continue
            lba = struct.unpack_from('<I', dir_data, pos+2)[0]
            size = struct.unpack_from('<I', dir_data, pos+10)[0]
            flags = dir_data[pos+25]
            nl = dir_data[pos+32]
            nm = dir_data[pos+33:pos+33+nl].decode('ascii', errors='replace')
            if nl == 1 and dir_data[pos+33] == 0:
                nm = '.'
            elif nl == 1 and dir_data[pos+33] == 1:
                nm = '..'
            else:
                nm = nm.split(';')[0]
            is_dir = bool(flags & 0x02)
            if nm not in ('.', '..'):
                files.append((nm, lba, size, is_dir))
            pos += rl
    return vol_space, root_lba, files

def secs(size):
    return (size + 2047) // 2048

def report(path, label):
    vol_space, root_lba, files = list_files(path)
    print("="*90)
    print(f"  {label}: {path}")
    print(f"  vol_space={vol_space} sectors  root_lba={root_lba}  file_size_on_disk={os.path.getsize(path)}")
    print("="*90)
    files_sorted = sorted(files, key=lambda x: x[1])
    for nm, lba, size, is_dir in files_sorted:
        end_lba = lba + secs(size)
        print(f"  LBA {lba:>8d} .. {end_lba:>8d}  ({secs(size):>7d} sec)  size={size:>12d}  {'DIR ' if is_dir else 'FILE'}  {nm}")
    return vol_space, root_lba, files_sorted

orig = r'C:\programmieren\wizardrytranslation\Busin 0 - Wizardry Alternative Neo (Japan) (v2.01).iso'
v139 = r'C:\programmieren\wizardrytranslation\build\BUSIN0_EN_v139.iso'

vs1, rl1, f1 = report(orig, 'ORIGINAL/PRISTINE')
print()
vs2, rl2, f2 = report(v139, 'v139 BUILD')

# Map by name
d1 = {n:(l,s,d) for n,l,s,d in f1}
d2 = {n:(l,s,d) for n,l,s,d in f2}

print("\n" + "="*90)
print("  DIFF: per-file LBA/size (orig vs v139)")
print("="*90)
allnames = sorted(set(d1) | set(d2), key=lambda n: d1.get(n,d2.get(n))[0])
for n in allnames:
    a = d1.get(n); b = d2.get(n)
    if a is None:
        print(f"  ONLY-v139: {n} LBA={b[0]} size={b[1]}")
    elif b is None:
        print(f"  ONLY-orig: {n} LBA={a[0]} size={a[1]}")
    else:
        la,sa,_=a; lb,sb,_=b
        flag = ""
        if la!=lb: flag += f" LBA {la}->{lb}"
        if sa!=sb: flag += f" SIZE {sa}->{sb} (delta {sb-sa})"
        print(f"  {n:16s} {flag if flag else 'identical'}")

# PACKDATA overflow landing zone (in v139)
print("\n" + "="*90)
print("  OVERFLOW LANDING ZONE (v139)")
print("="*90)
pk_l, pk_s, _ = d2['PACKDATA.DIG']
pk_end = pk_l + secs(pk_s)
print(f"  PACKDATA.DIG (v139): LBA {pk_l} .. {pk_end} (size {pk_s}, {secs(pk_s)} sectors)")

orig_pk_l, orig_pk_s, _ = d1['PACKDATA.DIG']
orig_pk_end = orig_pk_l + secs(orig_pk_s)
print(f"  PACKDATA.DIG (orig): LBA {orig_pk_l} .. {orig_pk_end} (size {orig_pk_s}, {secs(orig_pk_s)} sectors)")
overflow = pk_end - orig_pk_end
print(f"  Overflow tail spills from LBA {orig_pk_end} .. {pk_end}  ({overflow} sectors)")
print(f"  (The build keeps directory LBAs from orig but writes a longer PACKDATA blob)")

print("\n  Files in original layout that the overflow tail overwrites:")
for n,l,s,dr in f1:
    e = l + secs(s)
    # any file starting in the overflow window or overlapping it
    if l >= orig_pk_end and l < pk_end:
        print(f"    OVERWRITTEN-START: {n} orig LBA {l}..{e} (overflow ends {pk_end})")
    elif l < orig_pk_end and e > orig_pk_end and n != 'PACKDATA.DIG':
        print(f"    overlaps?: {n} {l}..{e}")
