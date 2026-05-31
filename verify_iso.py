#!/usr/bin/env python3
"""Verify an ISO has all expected English patches applied."""
import struct, sys, hashlib

if len(sys.argv) < 2:
    print("Usage: python verify_iso.py <path_to_iso>")
    sys.exit(1)

iso_path = sys.argv[1]
print(f"Verifying: {iso_path}")

iso = open(iso_path, 'rb')

# Check PACKDATA size
iso.seek(16 * 2048)
pvd = iso.read(2048)
root_lba = struct.unpack_from('<I', pvd, 158)[0]
root_size = struct.unpack_from('<I', pvd, 166)[0]
iso.seek(root_lba * 2048)
root_dir = iso.read(root_size)

pack_lba = pack_size = exe_lba = None
pos = 0
while pos < len(root_dir):
    rl = root_dir[pos]
    if rl == 0: break
    nl = root_dir[pos + 32]
    nm = root_dir[pos + 33:pos + 33 + nl].decode('ascii', errors='replace')
    if 'PACKDATA' in nm:
        pack_lba = struct.unpack_from('<I', root_dir, pos + 2)[0]
        pack_size = struct.unpack_from('<I', root_dir, pos + 10)[0]
    if 'SLPM' in nm:
        exe_lba = struct.unpack_from('<I', root_dir, pos + 2)[0]
    pos += rl

passed = 0
failed = 0

# Test 1: PACKDATA size
if pack_size and pack_size > 800_000_000:
    print(f"  PASS: PACKDATA size = {pack_size:,} bytes ({pack_size//1024//1024} MB)")
    passed += 1
else:
    print(f"  FAIL: PACKDATA size = {pack_size:,} bytes (expected >800 MB)")
    failed += 1

# Test 2: R38 stat labels
if pack_lba:
    iso.seek(pack_lba * 2048 + 38 * 12)
    s, c, t = struct.unpack('<III', iso.read(12))
    iso.seek((pack_lba + s) * 2048)
    r38 = iso.read(c * 2048)
    # Find stream start
    for i in range(16, len(r38) - 1, 2):
        if struct.unpack_from('>H', r38, i)[0] == 0xFFFF:
            stream = i + 2
            break
    # Decode group 2 (STR)
    gi = 0
    gstart = stream
    r38_checks = {}
    for i in range(stream, len(r38) - 1, 2):
        if struct.unpack_from('>H', r38, i)[0] == 0xFFFF:
            glyphs = []
            p = gstart
            while p < i:
                g = struct.unpack_from('>H', r38, p)[0]
                if 33 <= g <= 90: glyphs.append(chr(g + 0x20))
                elif g == 0xFFFE: glyphs.append('/')
                else: glyphs.append(f'[{g}]')
                p += 2
            r38_checks[gi] = ''.join(glyphs)
            gi += 1
            gstart = i + 2
            if gi > 35: break

    for check_gi, expected, label in [
        (2, 'str', 'STR stat'),
        (3, 'int', 'INT stat'),
        (25, '[518]', 'Male (Mars)'),
        (26, '[349]', 'Female (Venus)'),
        (29, 'human', 'Human race'),
        (34, 'automa', 'Automata race'),
    ]:
        actual = r38_checks.get(check_gi, 'MISSING')
        if expected.lower() in actual.lower():
            print(f"  PASS: R38 GRP {check_gi} ({label}) = '{actual}'")
            passed += 1
        else:
            print(f"  FAIL: R38 GRP {check_gi} ({label}) = '{actual}' (expected '{expected}')")
            failed += 1

# Test 3: EXE patches
if exe_lba:
    iso.seek(exe_lba * 2048 + 0x3FC720)
    save_name = iso.read(7)
    if save_name == b'BUSIN 0':
        print(f"  PASS: EXE save slot = 'BUSIN 0'")
        passed += 1
    else:
        print(f"  FAIL: EXE save slot = {save_name} (expected 'BUSIN 0')")
        failed += 1

# Test 4: R1272 font atlas size
if pack_lba:
    iso.seek(pack_lba * 2048 + 1272 * 12)
    s, c, t = struct.unpack('<III', iso.read(12))
    r1272_size = c * 2048
    if r1272_size > 70000:
        print(f"  PASS: R1272 font atlas = {r1272_size} bytes (extended)")
        passed += 1
    else:
        print(f"  FAIL: R1272 font atlas = {r1272_size} bytes (expected >70000)")
        failed += 1

# Calculate ISO hash (first 1MB for speed)
iso.seek(0)
h = hashlib.md5(iso.read(1024*1024)).hexdigest()
print(f"\n  ISO hash (first 1MB): {h}")
print(f"\n  Results: {passed} PASS, {failed} FAIL")
if failed == 0:
    print("  ALL CHECKS PASSED - ISO is correctly patched")
else:
    print("  SOME CHECKS FAILED - ISO may be stale or corrupt")
