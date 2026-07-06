"""AUDIT ONLY: verify relocated file DATA in built ISO matches original file data."""
import struct, math, os, hashlib

SECTOR = 2048
ORIG = 'Busin 0 - Wizardry Alternative Neo (Japan) (v2.01).iso'
BUILT = 'build/BUSIN0_EN_v139.iso'

def dirents(path):
    with open(path, 'rb') as f:
        f.seek(16 * SECTOR)
        pvd = f.read(SECTOR)
        root_lba = struct.unpack_from('<I', pvd, 158)[0]
        root_size = struct.unpack_from('<I', pvd, 166)[0]
        f.seek(root_lba * SECTOR)
        root = f.read(root_size)
    ents = {}
    pos = 0
    while pos < len(root):
        rl = root[pos]
        if rl == 0:
            nxt = ((pos // SECTOR) + 1) * SECTOR
            if nxt >= len(root): break
            pos = nxt; continue
        lba = struct.unpack_from('<I', root, pos + 2)[0]
        size = struct.unpack_from('<I', root, pos + 10)[0]
        nl = root[pos + 32]
        nm = root[pos + 33:pos + 33 + nl]
        if not (nl == 1 and nm[0] in (0, 1)):
            name = nm.decode('ascii', 'replace').split(';')[0]
            ents[name] = (lba, size)
        pos += rl
    return ents

oe = dirents(ORIG)
be = dirents(BUILT)

def md5_region(path, lba, size):
    h = hashlib.md5()
    with open(path, 'rb') as f:
        f.seek(lba * SECTOR)
        remaining = size
        while remaining > 0:
            chunk = f.read(min(remaining, 1 << 20))
            if not chunk: break
            h.update(chunk)
            remaining -= len(chunk)
    return h.hexdigest()

# For each relocated file, compare md5 of the actual file payload (size bytes)
# at orig LBA in ORIG vs new LBA in BUILT.
print("=== relocated file DATA integrity (md5 of payload) ===")
for name in sorted(oe):
    o_lba, o_size = oe[name]
    b_lba, b_size = be[name]
    if name == 'PACKDATA.DIG':
        print(f"  {name}: intended change (skip)")
        continue
    if o_size != b_size:
        print(f"  {name}: SIZE differs orig={o_size} built={b_size}")
    om = md5_region(ORIG, o_lba, o_size)
    bm = md5_region(BUILT, b_lba, b_size)
    status = 'OK' if om == bm else '!! DATA MISMATCH'
    print(f"  {name:14s} orig@{o_lba} built@{b_lba}: {status}")

# Check the PACKDATA tail region in built ISO: does PACKDATA payload actually
# fit in its directory-declared size, and what sits right after it?
print("\n=== PACKDATA tail vs BSN2_0 start in BUILT ===")
p_lba, p_size = be['PACKDATA.DIG']
p_end = p_lba + math.ceil(p_size / SECTOR)
bsn_lba, bsn_size = be['BSN2_0.DSI']
print(f"  PACKDATA end_lba={p_end}, BSN2_0 start_lba={bsn_lba}, gap={bsn_lba-p_end} sectors")

# Does the PACKDATA.DIG file on disk (build/PACKDATA_v3.DIG) match what's in ISO?
if os.path.exists('build/PACKDATA_v3.DIG'):
    dig_size = os.path.getsize('build/PACKDATA_v3.DIG')
    print(f"  build/PACKDATA_v3.DIG size={dig_size} ; ISO declares {p_size} ; "
          f"{'OK' if dig_size==p_size else 'MISMATCH'}")
    # md5 first/last sector
    with open('build/PACKDATA_v3.DIG','rb') as f:
        first = f.read(SECTOR)
        f.seek((math.ceil(dig_size/SECTOR)-1)*SECTOR)
        last = f.read(SECTOR)
    with open(BUILT,'rb') as f:
        f.seek(p_lba*SECTOR); iso_first=f.read(SECTOR)
        f.seek((p_end-1)*SECTOR); iso_last=f.read(SECTOR)
    print(f"  PACKDATA first sector in ISO matches file: {first==iso_first}")
    print(f"  PACKDATA last  sector in ISO matches file: {last==iso_last}")

# Verify the patched EXE bytes are actually in the built ISO at the new EXE LBA
print("\n=== patched EXE in ISO ===")
e_lba, e_size = be['SLPM_653.78']
patched = 'build/SLPM_653.78_patched'
if os.path.exists(patched):
    pm = md5_region_file = hashlib.md5(open(patched,'rb').read()).hexdigest()
    im = md5_region(BUILT, e_lba, e_size)
    print(f"  patched EXE md5 == ISO EXE region md5: {pm==im} (size {e_size})")
