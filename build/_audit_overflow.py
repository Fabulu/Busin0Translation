"""AUDIT ONLY: compare orig vs built ISO directory extents, detect overlaps."""
import struct, math, os

SECTOR = 2048
ORIG = 'Busin 0 - Wizardry Alternative Neo (Japan) (v2.01).iso'
BUILT = 'build/BUSIN0_EN_v139.iso'

def dirents(path):
    with open(path, 'rb') as f:
        f.seek(16 * SECTOR)
        pvd = f.read(SECTOR)
        vol_space = struct.unpack_from('<I', pvd, 80)[0]
        root_lba = struct.unpack_from('<I', pvd, 158)[0]
        root_size = struct.unpack_from('<I', pvd, 166)[0]
        f.seek(root_lba * SECTOR)
        root = f.read(root_size)
    ents = []
    pos = 0
    while pos < len(root):
        rl = root[pos]
        if rl == 0:
            nxt = ((pos // SECTOR) + 1) * SECTOR
            if nxt >= len(root):
                break
            pos = nxt
            continue
        lba = struct.unpack_from('<I', root, pos + 2)[0]
        size = struct.unpack_from('<I', root, pos + 10)[0]
        flags = root[pos + 25]
        nl = root[pos + 32]
        nm = root[pos + 33:pos + 33 + nl]
        if nl == 1 and nm[0] in (0, 1):
            name = '.' if nm[0] == 0 else '..'
        else:
            name = nm.decode('ascii', 'replace').split(';')[0]
        ents.append({'name': name, 'lba': lba, 'size': size,
                     'sectors': math.ceil(size / SECTOR),
                     'end': lba + math.ceil(size / SECTOR), 'dir': bool(flags & 2)})
        pos += rl
    return vol_space, root_lba, ents

def report(path, label):
    vol, root_lba, ents = dirents(path)
    fsize = os.path.getsize(path)
    print(f"\n=== {label}: {path} ===")
    print(f"  file size = {fsize} bytes = {fsize//SECTOR} sectors")
    print(f"  PVD vol_space = {vol} sectors; root_lba={root_lba}")
    files = [e for e in ents if e['name'] not in ('.', '..')]
    files.sort(key=lambda e: e['lba'])
    for e in files:
        print(f"  {e['name']:14s} LBA={e['lba']:>9d} size={e['size']:>12d} "
              f"sectors={e['sectors']:>7d} end_lba={e['end']:>9d}")
    # overlap check (sorted by lba)
    print("  -- overlap check --")
    overlaps = []
    for i in range(len(files) - 1):
        a, b = files[i], files[i + 1]
        if a['end'] > b['lba']:
            ov = a['end'] - b['lba']
            overlaps.append((a['name'], b['name'], ov))
            print(f"  !! OVERLAP: {a['name']} (end {a['end']}) into {b['name']} "
                  f"(start {b['lba']}) by {ov} sectors")
    if not overlaps:
        print("  no overlaps among directory files")
    # file extent past EOF?
    for e in files:
        if e['end'] * SECTOR > fsize:
            print(f"  !! {e['name']} extends past EOF: end_lba {e['end']} "
                  f"({e['end']*SECTOR} bytes) > file {fsize}")
    print(f"  vol_space ({vol}) vs file sectors ({fsize//SECTOR}): "
          f"{'OK' if vol == fsize//SECTOR else 'MISMATCH'}")
    return vol, root_lba, files

ov, orl, of = report(ORIG, 'ORIGINAL')
bv, brl, bf = report(BUILT, 'BUILT v139')

print("\n=== per-file orig vs built (by name) ===")
od = {e['name']: e for e in of}
bd = {e['name']: e for e in bf}
for name in sorted(set(od) | set(bd)):
    o = od.get(name); b = bd.get(name)
    if not o:
        print(f"  {name}: ONLY in built  LBA={b['lba']} size={b['size']}")
        continue
    if not b:
        print(f"  {name}: ONLY in orig  LBA={o['lba']} size={o['size']}")
        continue
    dl = b['lba'] - o['lba']
    ds = b['size'] - o['size']
    flag = '' if (dl == 0 and ds == 0) else '  <-- CHANGED'
    print(f"  {name:14s} dLBA={dl:+d} dSize={ds:+d}{flag}")
