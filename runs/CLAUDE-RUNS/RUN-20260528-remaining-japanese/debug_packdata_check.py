#!/usr/bin/env python3
"""Check PACKDATA_v3.DIG directly: are type-2 resources patched there?"""
import struct, os

SECTOR = 2048
V3 = 'C:/Programmieren/wizardrytranslation/build/PACKDATA_v3.DIG'
ORIG = 'C:/Programmieren/wizardrytranslation/extracted/PACKDATA.DIG'

# Read TOCs
with open(V3, 'rb') as f:
    v3_toc = f.read(12 * 2700)

with open(ORIG, 'rb') as f:
    orig_toc = f.read(12 * 2700)

# Count patched resources in build dir
patched_files = os.listdir('C:/Programmieren/wizardrytranslation/build/packdata_resources')
patched_type2 = [f for f in patched_files if '_type02.raw' in f]
patched_type2_dir = os.listdir('C:/Programmieren/wizardrytranslation/build/patched_type2')
print(f"Files in build/packdata_resources: {len(patched_files)}")
print(f"Type-02 files in build/packdata_resources: {len(patched_type2)}")
print(f"Files in build/patched_type2: {len(patched_type2_dir)}")

# Check a few specific type-2 resources in PACKDATA_v3 vs original
type2_patched_in_packdata = 0
type2_same_in_packdata = 0

for r_id in range(2700):
    v3_off, v3_cnt, v3_tc = struct.unpack_from('<III', v3_toc, r_id * 12)
    o_off, o_cnt, o_tc = struct.unpack_from('<III', orig_toc, r_id * 12)

    if v3_tc != 2 or v3_cnt == 0:
        continue

    # Compare data
    with open(V3, 'rb') as v3f, open(ORIG, 'rb') as of:
        v3f.seek(v3_off * SECTOR)
        v3_data = v3f.read(v3_cnt * SECTOR)
        of.seek(o_off * SECTOR)
        o_data = of.read(o_cnt * SECTOR)

    if v3_data == o_data[:len(v3_data)] and len(v3_data) == len(o_data):
        type2_same_in_packdata += 1
    else:
        type2_patched_in_packdata += 1

print(f"\nIn PACKDATA_v3.DIG directly:")
print(f"  Type-2 patched (differ from orig): {type2_patched_in_packdata}")
print(f"  Type-2 identical to original:      {type2_same_in_packdata}")

# The PACKDATA_v3 already matches the ISO (we confirmed MD5 match)
# So the question is: why are only 30 out of 617 type-2 resources patched?

# Check: how many type-02 .raw files exist in build/packdata_resources?
print(f"\n--- Type-02 raw files in build/packdata_resources ---")
type02_raws = sorted([f for f in patched_files if '_type02.raw' in f])
print(f"  Count: {len(type02_raws)}")
print(f"  First 10: {type02_raws[:10]}")
print(f"  Last 10: {type02_raws[-10:]}")

# Check build/patched_type2 directory
print(f"\n--- Type-02 raw files in build/patched_type2 ---")
pt2 = sorted(os.listdir('C:/Programmieren/wizardrytranslation/build/patched_type2'))
print(f"  Count: {len(pt2)}")
if pt2:
    print(f"  First 10: {pt2[:10]}")
    print(f"  Last 10: {pt2[-10:]}")

# Check: does rebuild_packdata.py filename format match what build_v9 produces?
# build_v9 produces: f'{idx:04d}_type{tc:02d}.raw' -> '0051_type02.raw'
# Check if any type-02 file in build/packdata_resources differs from extracted
print(f"\n--- Spot-check: R51 type-02 ---")
v3_51 = None
for r_id in [51]:
    v3_off, v3_cnt, v3_tc = struct.unpack_from('<III', v3_toc, r_id * 12)
    o_off, o_cnt, o_tc = struct.unpack_from('<III', orig_toc, r_id * 12)
    print(f"  R{r_id}: v3 off={v3_off} cnt={v3_cnt} tc={v3_tc}, orig off={o_off} cnt={o_cnt} tc={o_tc}")

    with open(V3, 'rb') as v3f, open(ORIG, 'rb') as of:
        v3f.seek(v3_off * SECTOR)
        v3_data = v3f.read(v3_cnt * SECTOR)
        of.seek(o_off * SECTOR)
        o_data = of.read(o_cnt * SECTOR)

    print(f"  Data match: {v3_data == o_data}")

    # Check if patched file exists
    raw_path = f'C:/Programmieren/wizardrytranslation/build/packdata_resources/0051_type02.raw'
    if os.path.exists(raw_path):
        pdata = open(raw_path, 'rb').read()
        print(f"  Patched file exists: {len(pdata):,} bytes")
        print(f"  Patched == v3 region: {pdata == v3_data[:len(pdata)]}")
        print(f"  Patched == orig region: {pdata == o_data[:len(pdata)]}")
    else:
        print(f"  No patched file at {raw_path}")

    raw_path2 = f'C:/Programmieren/wizardrytranslation/build/patched_type2/0051_type02.raw'
    if os.path.exists(raw_path2):
        pdata2 = open(raw_path2, 'rb').read()
        print(f"  patched_type2 file exists: {len(pdata2):,} bytes")
    else:
        print(f"  No file in patched_type2 for R51")

# Check manifest to understand naming
import json
manifest = json.load(open('C:/Programmieren/wizardrytranslation/extracted/packdata_resources/manifest.json', encoding='utf-8'))
# Check R51
if len(manifest) > 51:
    print(f"\n  Manifest R51: {manifest[51]}")

# Check naming pattern
# rebuild_packdata.py uses: f'{idx:04d}_type{tc:02d}.raw'
# build_v9.py for type-2 also uses: f'{r_id:04d}_type02.raw' (via inject_and_patch)
# But what does inject_and_patch actually write?
print(f"\n--- inject_and_patch output filenames ---")
pt2_files = sorted(os.listdir('C:/Programmieren/wizardrytranslation/build/patched_type2'))
for f in pt2_files[:5]:
    full = f'C:/Programmieren/wizardrytranslation/build/patched_type2/{f}'
    print(f"  {f}: {os.path.getsize(full):,} bytes")

# Now the key question: rebuild_packdata.py looks for files as:
# f'{idx:04d}_type{tc:02d}.raw'
# But the manifest type_code could differ from what build_v9 writes
# Let's check a few manifest entries for type-2 resources
print(f"\n--- Manifest type codes for some type-2 resources ---")
type2_manifest = [(i, e) for i, e in enumerate(manifest) if e.get('type_code') == 2 and not e.get('skipped')]
print(f"  Total type-2 in manifest: {len(type2_manifest)}")
# Check if the filename format matches
for idx, entry in type2_manifest[:5]:
    fn = f'{idx:04d}_type{entry["type_code"]:02d}.raw'
    exists_pr = os.path.exists(f'C:/Programmieren/wizardrytranslation/build/packdata_resources/{fn}')
    exists_pt2 = os.path.exists(f'C:/Programmieren/wizardrytranslation/build/patched_type2/{fn}')
    print(f"  R{idx}: fn={fn}, in packdata_resources={exists_pr}, in patched_type2={exists_pt2}")
