"""
Check which modified type-02 resources have trailing data after last FFFF
that would be LOST by inject_and_patch.
"""
import struct, os

os.chdir('C:/Programmieren/wizardrytranslation')

orig_dir = 'extracted/packdata_raw'
built_dir = 'build/packdata_resources'

print("Resources with trailing data after last FFFF in Section 0:")
print("="*80)

affected = []

for f in sorted(os.listdir(built_dir)):
    if not f.endswith('.raw') or '_type02' not in f:
        continue
    idx = int(f.split('_')[0])
    bp = os.path.join(built_dir, f)
    op = os.path.join(orig_dir, f)
    if not os.path.exists(op):
        continue

    o = open(op, 'rb').read()
    b = open(bp, 'rb').read()
    if o == b:
        continue

    # Parse original Section 0
    o_sec0_size = struct.unpack_from('<I', o, 0x14)[0]
    o_sec0_off = struct.unpack_from('<I', o, 0x18)[0]
    o_sec0 = o[o_sec0_off:o_sec0_off + o_sec0_size]

    n_words = len(o_sec0) // 2
    words = [struct.unpack_from('>H', o_sec0, i*2)[0] for i in range(n_words)]

    # Find last FFFF
    last_ffff = -1
    for i in range(n_words):
        if words[i] == 0xFFFF:
            last_ffff = i

    if last_ffff >= 0:
        trailing = n_words - (last_ffff + 1)
        if trailing > 0:
            trail_words = words[last_ffff + 1:]
            affected.append((idx, trailing, trail_words))
            print(f"\n  R{idx:04d}: {trailing} trailing words after last FFFF")
            print(f"    Words: {[f'0x{w:04X}' for w in trail_words[:20]]}")

            # Check: did the built version preserve them?
            b_sec0_size = struct.unpack_from('<I', b, 0x14)[0]
            b_sec0_off = struct.unpack_from('<I', b, 0x18)[0]
            b_sec0 = b[b_sec0_off:b_sec0_off + b_sec0_size]
            b_n = len(b_sec0) // 2
            b_words = [struct.unpack_from('>H', b_sec0, i*2)[0] for i in range(b_n)]

            # Find last FFFF in built
            b_last_ffff = -1
            for i in range(b_n):
                if b_words[i] == 0xFFFF:
                    b_last_ffff = i

            b_trailing = b_n - (b_last_ffff + 1) if b_last_ffff >= 0 else 0
            if b_trailing == 0 and trailing > 0:
                print(f"    *** TRAILING DATA LOST IN BUILT VERSION! ***")
            elif b_trailing == trailing:
                print(f"    Trailing data preserved in built version")
            else:
                print(f"    Built has {b_trailing} trailing words (vs {trailing} original)")

print(f"\n\n{'='*80}")
print(f"Total resources with trailing data: {len(affected)}")
