"""
Check which modified resources are loaded when entering town.
The town scene likely uses resources in the R1196-R1213 range (scene scripts).
Also check R35 (type-02 with VIF commands in first KB).

For each, verify that Section 1 opcodes that reference Section 0 text data
use valid word offsets given the NEW Section 0 size.
"""
import struct, os, sys

os.chdir('C:/Programmieren/wizardrytranslation')
sys.path.insert(0, 'tools')

from patch_section1_offsets import parse_sec2_group_offsets

orig_dir = 'extracted/packdata_raw'
built_dir = 'build/packdata_resources'

# Check DISPLAY_TEXT opcodes in detail for town resources
town_candidates = [35, 1193, 1194, 1196, 1197, 1198, 1199, 1200, 1201,
                   1202, 1203, 1204, 1205, 1206, 1207, 1208, 1209, 1210,
                   1211, 1212, 1213, 1347, 1348, 1349, 1351, 1353, 1354, 1355]

for idx in town_candidates:
    bp = os.path.join(built_dir, f'{idx:04d}_type02.raw')
    op = os.path.join(orig_dir, f'{idx:04d}_type02.raw')
    if not os.path.exists(bp) or not os.path.exists(op):
        continue

    b = open(bp, 'rb').read()
    o = open(op, 'rb').read()
    if b == o:
        continue

    # Parse sec0 (text data)
    b_sec0_size = struct.unpack_from('<I', b, 0x14)[0]
    b_sec0_off = struct.unpack_from('<I', b, 0x18)[0]
    o_sec0_size = struct.unpack_from('<I', o, 0x14)[0]
    o_sec0_off = struct.unpack_from('<I', o, 0x18)[0]

    b_sec0 = b[b_sec0_off:b_sec0_off + b_sec0_size]
    o_sec0 = o[o_sec0_off:o_sec0_off + o_sec0_size]

    b_groups = parse_sec2_group_offsets(b_sec0)
    o_groups = parse_sec2_group_offsets(o_sec0)

    if len(b_groups) != len(o_groups):
        print(f"R{idx:04d}: *** GROUP COUNT CHANGED! orig={len(o_groups)} built={len(b_groups)} ***")
        continue

    # Check Section 1 opcodes
    sec1 = b[0x1C:b_sec0_off]
    n_words = len(sec1) // 2
    words = [struct.unpack_from('>H', sec1, i*2)[0] for i in range(n_words)]

    sec0_words = b_sec0_size // 2

    issues = []

    # Check DISPLAY_TEXT: 0004 0000 GOFF 0000 GCNT
    for i in range(n_words - 4):
        if words[i] == 0x0004 and words[i+1] == 0x0000 and words[i+3] == 0x0000:
            goff = words[i+2]
            gcnt = words[i+4]
            if gcnt == 0:
                continue
            end = goff + gcnt
            if end > sec0_words and goff < 0x4000:
                issues.append(f"DISPLAY_TEXT off={goff} cnt={gcnt} end={end} > sec0_words={sec0_words}")

    # Check SET_NAME_REF / CLEAR_NAME_REF
    for i in range(n_words - 2):
        if words[i] in (0x000C, 0x000D):
            param = words[i+1]
            gidx = words[i+2]
            if param != 121 and gidx >= sec0_words and gidx < 0x4000:
                issues.append(f"NAME_REF param={param} gidx={gidx} >= sec0_words={sec0_words}")

    delta = b_sec0_size - o_sec0_size
    if issues:
        print(f"R{idx:04d}: sec0 {o_sec0_size}->{b_sec0_size} ({delta:+d}), {len(b_groups)} groups, {len(issues)} ISSUES:")
        for iss in issues[:5]:
            print(f"  {iss}")
    else:
        print(f"R{idx:04d}: sec0 {o_sec0_size}->{b_sec0_size} ({delta:+d}), {len(b_groups)} groups, ALL REFS OK")
