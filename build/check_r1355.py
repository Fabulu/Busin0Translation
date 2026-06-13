"""
Deep investigation of R1355 - group count changed from 56 to 55.
This is a critical bug that could cause the VIF crash.
"""
import struct, os, sys

os.chdir('C:/Programmieren/wizardrytranslation')
sys.path.insert(0, 'tools')

orig_dir = 'extracted/packdata_raw'
built_dir = 'build/packdata_resources'

op = os.path.join(orig_dir, '1355_type02.raw')
bp = os.path.join(built_dir, '1355_type02.raw')

o = open(op, 'rb').read()
b = open(bp, 'rb').read()

# Parse Section 0
o_sec0_size = struct.unpack_from('<I', o, 0x14)[0]
o_sec0_off = struct.unpack_from('<I', o, 0x18)[0]
b_sec0_size = struct.unpack_from('<I', b, 0x14)[0]
b_sec0_off = struct.unpack_from('<I', b, 0x18)[0]

o_sec0 = o[o_sec0_off:o_sec0_off + o_sec0_size]
b_sec0 = b[b_sec0_off:b_sec0_off + b_sec0_size]

# Parse groups
def parse_groups(data):
    n = len(data) // 2
    words = [struct.unpack_from('>H', data, i*2)[0] for i in range(n)]
    groups = []
    start = 0
    for i in range(n):
        if words[i] == 0xFFFF:
            groups.append(words[start:i])
            start = i + 1
    trailing = words[start:] if start < n else []
    return groups, trailing

o_groups, o_trail = parse_groups(o_sec0)
b_groups, b_trail = parse_groups(b_sec0)

print(f"R1355 Analysis:")
print(f"  Original: {len(o_groups)} groups, {len(o_trail)} trailing words")
print(f"  Built:    {len(b_groups)} groups, {len(b_trail)} trailing words")
print(f"  sec0 size: orig={o_sec0_size} built={b_sec0_size}")

# Find which group was lost
print(f"\n  Group comparison (orig vs built):")
max_groups = max(len(o_groups), len(b_groups))
for i in range(max_groups):
    og = o_groups[i] if i < len(o_groups) else None
    bg = b_groups[i] if i < len(b_groups) else None

    if og is not None and bg is not None:
        if og == bg:
            status = "SAME"
        else:
            # Check if bg matches a different orig group
            o_text = ' '.join(f'{g:04X}' for g in og[:5])
            b_text = ' '.join(f'{g:04X}' for g in bg[:5])
            status = f"DIFF: orig=[{o_text}...] built=[{b_text}...]"
    elif og is None:
        b_text = ' '.join(f'{g:04X}' for g in bg[:5])
        status = f"NEW in built: [{b_text}...]"
    else:
        o_text = ' '.join(f'{g:04X}' for g in og[:5])
        status = f"MISSING in built: [{o_text}...]"

    print(f"  Group {i}: len={len(og) if og else 0}/{len(bg) if bg else 0} {status}")

# Check if any translation batch has R1355 messages
import json, glob
print(f"\n  Translation sources for R1355:")
for fn in sorted(glob.glob('data/type2_translated/batch_*.json')):
    try:
        d = json.load(open(fn, encoding='utf-8'))
        r1355_entries = [e for e in d if e.get('resource') == 1355]
        if r1355_entries:
            print(f"    {os.path.basename(fn)}: {len(r1355_entries)} entries")
            for e in r1355_entries[:5]:
                mi = e.get('msg_index', '?')
                en = e.get('english', '')[:60]
                print(f"      msg {mi}: {en!r}")
    except:
        pass
