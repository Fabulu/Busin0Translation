"""
Binary comparison of working vs broken PACKDATA.
Step 1: Build working PACKDATA (only R1272 changed, all others original)
Step 2: Build broken PACKDATA (full build with all translations)
Step 3: Compare TOC, header, resource data
"""
import struct, json, os, math, shutil, sys

os.chdir('C:/Programmieren/wizardrytranslation')

SECTOR = 2048

manifest = json.load(open('extracted/packdata_resources/manifest.json', encoding='utf-8'))
n_entries = len(manifest)

built_dir = 'build/packdata_resources'
orig_dir = 'extracted/packdata_raw'

# ---- STEP 1: Identify which files in build/packdata_resources differ from originals ----
print("=" * 80)
print("STEP 1: Identifying modified resources in build/packdata_resources/")
print("=" * 80)

modified_files = []
built_files = sorted(os.listdir(built_dir))
for f in built_files:
    if not f.endswith('.raw'):
        continue
    built_path = os.path.join(built_dir, f)
    orig_path = os.path.join(orig_dir, f)
    if os.path.exists(orig_path):
        b = open(built_path, 'rb').read()
        o = open(orig_path, 'rb').read()
        if b != o:
            modified_files.append(f)
            print(f"  MODIFIED: {f}  built={len(b)} orig={len(o)} delta={len(b)-len(o):+d}")
        else:
            print(f"  same:     {f}")
    else:
        modified_files.append(f)
        print(f"  NEW (no original): {f}")

print(f"\n{len(modified_files)} modified resources out of {len(built_files)} built files")

# ---- STEP 2: Build WORKING PACKDATA (only R1272 changed) ----
print("\n" + "=" * 80)
print("STEP 2: Building WORKING PACKDATA (only R1272)")
print("=" * 80)

# Save current built files that differ from originals
saved = {}
for f in modified_files:
    if '1272' in f:
        continue
    bp = os.path.join(built_dir, f)
    op = os.path.join(orig_dir, f)
    if os.path.exists(op):
        saved[f] = open(bp, 'rb').read()
        shutil.copy2(op, bp)
        print(f"  Restored original: {f}")

# Now rebuild
exec(open('build/rebuild_packdata.py').read())
shutil.copy2('build/PACKDATA_v3.DIG', 'build/PACKDATA_working.DIG')
working_size = os.path.getsize('build/PACKDATA_working.DIG')
print(f"Working PACKDATA saved: {working_size:,} bytes")

# ---- STEP 3: Restore modified files and build BROKEN PACKDATA ----
print("\n" + "=" * 80)
print("STEP 3: Building BROKEN PACKDATA (full build)")
print("=" * 80)

for f, data in saved.items():
    bp = os.path.join(built_dir, f)
    open(bp, 'wb').write(data)
    print(f"  Restored modified: {f}")

exec(open('build/rebuild_packdata.py').read())
shutil.copy2('build/PACKDATA_v3.DIG', 'build/PACKDATA_broken.DIG')
broken_size = os.path.getsize('build/PACKDATA_broken.DIG')
print(f"Broken PACKDATA saved: {broken_size:,} bytes")

# ---- STEP 4: Compare TOC ----
print("\n" + "=" * 80)
print("STEP 4: Comparing TOC entries")
print("=" * 80)

wf = open('build/PACKDATA_working.DIG', 'rb')
bf = open('build/PACKDATA_broken.DIG', 'rb')

wtoc = [struct.unpack('<III', wf.read(12)) for _ in range(n_entries)]
wf.seek(0)
btoc = [struct.unpack('<III', bf.read(12)) for _ in range(n_entries)]
bf.seek(0)

toc_diffs = []
for i in range(n_entries):
    ws, wc, wt = wtoc[i]
    bs, bc, bt = btoc[i]
    if (ws, wc, wt) != (bs, bc, bt):
        toc_diffs.append(i)
        print(f"  R{i:04d}: working=({ws},{wc},type{wt:02d}) broken=({bs},{bc},type{bt:02d})"
              f"  sector_delta={bs-ws:+d} size_delta={bc-wc:+d}")

print(f"\n{len(toc_diffs)} TOC entries differ")

# ---- STEP 5: Compare header region (sectors 0-124) ----
print("\n" + "=" * 80)
print("STEP 5: Comparing header region (sectors 0-124)")
print("=" * 80)

wf.seek(0)
bf.seek(0)
whdr = wf.read(125 * SECTOR)
bhdr = bf.read(125 * SECTOR)

if whdr == bhdr:
    print("  Header regions are IDENTICAL")
else:
    # Find first difference
    for i in range(len(whdr)):
        if whdr[i] != bhdr[i]:
            print(f"  First difference at offset 0x{i:X} (sector {i//SECTOR}, offset in sector {i%SECTOR})")
            break

    # Check by sector
    for s in range(125):
        ws = whdr[s*SECTOR:(s+1)*SECTOR]
        bs = bhdr[s*SECTOR:(s+1)*SECTOR]
        if ws != bs:
            diff_bytes = sum(1 for a, b in zip(ws, bs) if a != b)
            print(f"  Sector {s}: {diff_bytes} bytes differ")

# ---- STEP 6: Compare actual resource data ----
print("\n" + "=" * 80)
print("STEP 6: Comparing resource data for differing TOC entries")
print("=" * 80)

for i in toc_diffs[:50]:  # Limit output
    ws, wc, wt = wtoc[i]
    bs, bc, bt = btoc[i]

    wf.seek(ws * SECTOR)
    wdata = wf.read(wc * SECTOR)
    bf.seek(bs * SECTOR)
    bdata = bf.read(bc * SECTOR)

    if wdata == bdata:
        status = "DATA IDENTICAL (only offset changed)"
    else:
        diff_count = sum(1 for a, b in zip(wdata[:min(len(wdata), len(bdata))], bdata[:min(len(wdata), len(bdata))]) if a != b)
        status = f"DATA DIFFERS ({diff_count} bytes differ in first {min(len(wdata), len(bdata))} bytes)"

    print(f"\n  R{i:04d} (type{wt:02d}): {status}")
    print(f"    Working: sector {ws}, {wc} sectors = {wc*SECTOR} bytes")
    print(f"    Broken:  sector {bs}, {bc} sectors = {bc*SECTOR} bytes")
    print(f"    Working first 64: {wdata[:64].hex()}")
    print(f"    Broken  first 64: {bdata[:64].hex()}")

# ---- STEP 7: Verify broken PACKDATA matches build/packdata_resources ----
print("\n" + "=" * 80)
print("STEP 7: Verifying broken PACKDATA resource data matches source files")
print("=" * 80)

mismatch_count = 0
for entry in manifest:
    idx = entry['index']
    if entry.get('skipped'):
        continue
    tc = entry['type_code']
    fn = f'{idx:04d}_type{tc:02d}.raw'

    # Find source file
    mp = f'build/packdata_resources/{fn}'
    rp = f'extracted/packdata_raw/{fn}'
    if os.path.exists(mp):
        src_data = open(mp, 'rb').read()
        src = 'build'
    elif os.path.exists(rp):
        src_data = open(rp, 'rb').read()
        src = 'orig'
    else:
        continue

    # Read from broken PACKDATA
    bs, bc, bt = btoc[idx]
    bf.seek(bs * SECTOR)
    pack_data = bf.read(bc * SECTOR)

    # Compare (pack_data is sector-padded, src_data may not be)
    src_padded_len = math.ceil(len(src_data) / SECTOR) * SECTOR
    src_padded = src_data + b'\x00' * (src_padded_len - len(src_data))

    if pack_data[:len(src_data)] != src_data:
        mismatch_count += 1
        # Find first difference
        for j in range(min(len(src_data), len(pack_data))):
            if src_data[j] != pack_data[j]:
                print(f"  MISMATCH R{idx:04d} (src={src}): first diff at offset 0x{j:X}")
                print(f"    Source: {src_data[j:j+32].hex()}")
                print(f"    Pack:   {pack_data[j:j+32].hex()}")
                break
        if mismatch_count > 20:
            print("  ... (truncated)")
            break

if mismatch_count == 0:
    print("  ALL resources match their source files perfectly!")

# ---- STEP 8: Check sector alignment in broken PACKDATA ----
print("\n" + "=" * 80)
print("STEP 8: Checking sector alignment in broken PACKDATA")
print("=" * 80)

broken_file_size = os.path.getsize('build/PACKDATA_broken.DIG')
alignment_issues = 0
for i in range(n_entries):
    bs, bc, bt = btoc[i]
    byte_offset = bs * SECTOR
    if byte_offset > broken_file_size:
        print(f"  R{i:04d}: sector {bs} BEYOND EOF (offset {byte_offset} > size {broken_file_size})")
        alignment_issues += 1
        continue

    if byte_offset % SECTOR != 0:
        print(f"  R{i:04d}: NOT sector-aligned! offset={byte_offset}")
        alignment_issues += 1

if alignment_issues == 0:
    print("  All resources are sector-aligned and within file bounds")

# ---- STEP 9: Check for resources that GREW vs original ----
print("\n" + "=" * 80)
print("STEP 9: Resources that changed size vs original")
print("=" * 80)

orig_f = open('extracted/PACKDATA.DIG', 'rb')
orig_toc = [struct.unpack('<III', orig_f.read(12)) for _ in range(n_entries)]

grew = []
shrank = []
same_size_diff_data = []

for i in range(n_entries):
    os_sec, oc, ot = orig_toc[i]
    bs, bc, bt = btoc[i]

    if bc != oc:
        delta = bc - oc
        if delta > 0:
            grew.append((i, oc, bc, delta, bt))
        else:
            shrank.append((i, oc, bc, delta, bt))
    else:
        # Same size - check if data differs
        orig_f.seek(os_sec * SECTOR)
        odata = orig_f.read(oc * SECTOR)
        bf.seek(bs * SECTOR)
        bdata = bf.read(bc * SECTOR)
        if odata != bdata:
            same_size_diff_data.append(i)

print(f"\nResources that GREW ({len(grew)}):")
for idx, oc, bc, delta, t in grew:
    print(f"  R{idx:04d} (type{t:02d}): {oc} -> {bc} sectors (+{delta} = +{delta*SECTOR} bytes)")

print(f"\nResources that SHRANK ({len(shrank)}):")
for idx, oc, bc, delta, t in shrank:
    print(f"  R{idx:04d} (type{t:02d}): {oc} -> {bc} sectors ({delta} = {delta*SECTOR} bytes)")

print(f"\nResources SAME SIZE but DIFFERENT DATA ({len(same_size_diff_data)}):")
for idx in same_size_diff_data:
    print(f"  R{idx:04d} (type{orig_toc[idx][2]:02d})")

total_growth = sum(d for _,_,_,d,_ in grew) + sum(d for _,_,_,d,_ in shrank)
print(f"\nNet sector growth: {total_growth:+d} sectors ({total_growth*SECTOR:+d} bytes)")

# ---- STEP 10: Focus on town-relevant resources ----
print("\n" + "=" * 80)
print("STEP 10: Town-relevant resources analysis")
print("=" * 80)

# Key resources for town: R34 items, R35 ?, R36-R49 text/menus, R989 ?, R1193, R1272 font
# Also type-2 resources used in town scenes
town_resources = list(range(34, 50)) + [989, 1188, 1193, 1213, 1272, 2100, 1370, 2124, 2138, 2654]
for idx in town_resources:
    if idx >= n_entries:
        continue
    os_sec, oc, ot = orig_toc[idx]
    bs, bc, bt = btoc[idx]
    ws, wc, wt = wtoc[idx]

    changed_from_orig = (bc != oc) or (bt != ot)
    changed_from_working = (bc != wc) or (bs != ws)

    # Read first 64 bytes from broken
    bf.seek(bs * SECTOR)
    bfirst = bf.read(64)

    marker = ""
    if changed_from_working:
        marker = " ** DIFFERS FROM WORKING **"

    print(f"  R{idx:04d} type{bt:02d}: orig={oc}sec broken={bc}sec delta={bc-oc:+d}{marker}")
    print(f"    First 16 bytes: {bfirst[:16].hex()}")

orig_f.close()
wf.close()
bf.close()

print("\n" + "=" * 80)
print("COMPARISON COMPLETE")
print("=" * 80)
