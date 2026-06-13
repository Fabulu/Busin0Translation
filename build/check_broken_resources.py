"""
Deep dive into the 4 broken resources to understand the exact nature of the corruption.
"""
import struct, os, sys
os.chdir('C:/Programmieren/wizardrytranslation')

SECTOR = 2048

def dump_resource_info(idx, orig_path, built_path):
    orig = open(orig_path, 'rb').read()
    built = open(built_path, 'rb').read()

    print(f"\n{'='*70}")
    print(f"R{idx:04d}: orig={len(orig)} bytes, built={len(built)} bytes")
    print(f"{'='*70}")

    # Parse headers
    for name, data in [("ORIGINAL", orig), ("BUILT", built)]:
        hdr = struct.unpack_from('<IIII', data, 0)
        sec2_size = struct.unpack_from('<I', data, 0x14)[0]
        sec2_off = struct.unpack_from('<I', data, 0x18)[0]

        # Parse sec2 groups
        sec2 = data[sec2_off:sec2_off + sec2_size]
        n_words = len(sec2) // 2
        groups = []
        start = 0
        for i in range(n_words):
            w = struct.unpack_from('>H', sec2, i*2)[0]
            if w == 0xFFFF:
                groups.append((start, i))
                start = i + 1

        print(f"\n  {name}:")
        print(f"    Total payload: {hdr[1]}")
        print(f"    Sec2 size: {sec2_size} bytes ({sec2_size//2} words)")
        print(f"    Sec2 offset: 0x{sec2_off:X}")
        print(f"    Sec2 groups: {len(groups)}")
        if groups:
            print(f"    Last group ends at word {groups[-1][1]} (FFFF at word {groups[-1][1]})")
            print(f"    Words after last FFFF: {n_words - (groups[-1][1] + 1)}")

# Check R1348 in detail - it has 84 issues
for idx in [1202, 1203, 1208, 1209, 1348]:
    orig_path = f'extracted/packdata_raw/{idx:04d}_type02.raw'
    built_path = f'build/packdata_resources/{idx:04d}_type02.raw'
    if os.path.exists(orig_path) and os.path.exists(built_path):
        dump_resource_info(idx, orig_path, built_path)

# Now check: are these the original issues or did they exist before patching?
print(f"\n\n{'='*70}")
print("Checking if ORIGINAL resources also have these issues:")
print(f"{'='*70}")

sys.path.insert(0, 'tools')
from patch_section1_offsets import verify_patched

for idx in [1202, 1203, 1208, 1209, 1348]:
    orig_path = f'extracted/packdata_raw/{idx:04d}_type02.raw'
    if os.path.exists(orig_path):
        # Verify original against itself
        issues, text_ops, name_ops = verify_patched(orig_path, orig_path)
        if issues:
            print(f"  R{idx:04d} ORIGINAL: {len(issues)} issues!")
            for iss in issues[:5]:
                print(f"    {iss}")
            if len(issues) > 5:
                print(f"    ... and {len(issues)-5} more")
        else:
            print(f"  R{idx:04d} ORIGINAL: clean")
