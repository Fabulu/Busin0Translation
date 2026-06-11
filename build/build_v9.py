#!/usr/bin/env python3
"""Build v9 ISO: variable-size type-2 injection + Section 1 opcode patching"""
import sys, os, struct, json, glob, shutil, math

os.chdir('C:/Programmieren/wizardrytranslation')
sys.path.insert(0, 'tools')

SECTOR = 2048

print("=" * 60)
print("  BUILD v9 - Full variable-size + Section 1 patching")
print("=" * 60)

# ===== STEP 1: Run v2 pipeline for type-1 resources =====
print("\n=== Step 1: Type-1 injection (v2 pipeline) ===")
os.system('python build/build_full_english_v2.py')
print("  v2 pipeline complete")

# Remove unsafe type-03/06 resources that v2 pipeline incorrectly patches
for unsafe_r, tc in [(1053, '03'), (1908, '06')]:
    f = f'build/packdata_resources/{unsafe_r:04d}_type{tc}.raw'
    if os.path.exists(f):
        os.remove(f)
        print(f"  Removed unsafe R{unsafe_r} (type-{tc})")

# ===== STEP 2: Fix problem type-1 resources (R34, R35, R2124, R2654) =====
print("\n=== Step 2: Fix type-1 FFFF mismatches ===")
table = json.load(open('data/english_glyph_table.json', encoding='utf-8'))

translations = {}
for i in range(10):
    try:
        d = json.load(open(f'data/translate_chunks/chunk_{i:02d}_translated.json', encoding='utf-8'))
        for e in d:
            k = (e.get('resource', -1), e.get('message', -1))
            en = e.get('english', '').strip()
            if en and en != e.get('japanese', ''):
                translations[k] = en
    except:
        pass
for fix in ['chunk_r38_fix.json', 'chunk_r43_fix.json', 'chunk_r37_extra.json', 'chunk_r40_r42_translated.json', 'chunk_r36_translated.json', 'chunk_r37_r48_r49_translated.json', 'chunk_r43_r45_translated.json']:
    try:
        d = json.load(open(f'data/translate_chunks/{fix}', encoding='utf-8'))
        for e in d:
            k = (e.get('resource', -1), e.get('message', -1))
            en = e.get('english', '').strip()
            if en:
                translations[k] = en
    except:
        pass

def enc(ch):
    if ch in table:
        return table[ch]
    if ch.lower() in table:
        return table[ch.lower()]
    return 31

def word_wrap(text, max_chars=18):
    """Wrap text to fit within max_chars per line.

    Preserves existing ' / ' line breaks.  For segments that exceed
    max_chars, inserts ' / ' at the last space before the limit.
    """
    segments = text.split(' / ')
    wrapped = []
    for seg in segments:
        while len(seg) > max_chars:
            # find last space at or before max_chars
            brk = seg.rfind(' ', 0, max_chars + 1)
            if brk <= 0:
                # no space found — force break at max_chars
                brk = max_chars
            wrapped.append(seg[:brk])
            seg = seg[brk:].lstrip(' ')
        wrapped.append(seg)
    return ' / '.join(wrapped)

for r_id in [34, 35, 2654]:  # Flat-format resources with in-place translation
    tc_map = {34: '20', 35: '02', 2654: '44'}
    tc = tc_map.get(r_id, '01')
    orig = bytearray(open(f'extracted/packdata_raw/{r_id:04d}_type{tc}.raw', 'rb').read())
    rt = {m: e for (r, m), e in translations.items() if r == r_id}
    # R2654 (type-44) and R34 (type-20) have multi-section headers before
    # the glyph data. The glyph data offset is stored at header byte 8 (LE u32).
    # Scanning for FFFF from byte 0 would treat the header as group 0,
    # and writing translations there corrupts the header -> VIF FIFO crash.
    data_start = 0
    if r_id in (34, 2654):
        data_start = struct.unpack_from('<I', orig, 8)[0]
    fp = [i for i in range(data_start, len(orig) - 1, 2) if struct.unpack_from('>H', orig, i)[0] == 0xFFFF]
    groups = []
    prev = data_start
    for f in fp:
        groups.append((prev, f + 2))
        prev = f + 2
    out = bytearray(orig)
    rep = 0
    for gi, (g_s, g_e) in enumerate(groups):
        mi = gi + 1
        if mi not in rt:
            continue
        en = rt[mi]
        if any(ord(c) > 127 for c in en):
            continue
        ocs = g_e - g_s - 2
        ctrls = bytearray()
        p = g_s
        while p < g_e - 1:
            v = struct.unpack_from('>H', orig, p)[0]
            if v >= 0xFB00 and v not in (0xFFFF, 0xFFFE):
                ctrls += struct.pack('>H', v)
                p += 2
            else:
                break
        en = word_wrap(en)
        gls = []
        for pi, pt in enumerate(en.split(' / ')):
            if pi > 0:
                gls.append(0xFFFE)
            for c in pt:
                gls.append(enc(c))
        nc = ctrls
        for g in gls:
            nc += struct.pack('>H', g)
        while len(nc) < ocs:
            nc += struct.pack('>H', 0)
        if len(nc) > ocs:
            nc = nc[:ocs]
        out[g_s:g_e - 2] = nc
        rep += 1
    pd = (SECTOR - len(out) % SECTOR) % SECTOR
    out += b'\x00' * pd
    open(f'build/packdata_resources/{r_id:04d}_type{tc}.raw', 'wb').write(out)
    nf = sum(1 for i in range(0, len(out) - 1, 2) if struct.unpack_from('>H', out, i)[0] == 0xFFFF)
    status = 'OK' if len(fp) == nf else 'MISMATCH!'
    print(f"  R{r_id}: {rep} replaced, FFFF {len(fp)}=={nf} {status}")

# ===== STEP 3: R39 custom type-15 injection =====
print("\n=== Step 3: R39 type-15 injection ===")
if os.path.exists('build/packdata_resources/0039_type15.raw'):
    os.remove('build/packdata_resources/0039_type15.raw')
os.system('python build/inject_r39_v2.py')
print("  R39 injected")

# ===== STEP 3.1: R39 inline Japanese glyph patching =====
print("\n=== Step 3.1: R39 inline Japanese patch ===")
os.system('python tools/patch_r39_inline.py')
print("  R39 inline labels patched")

# ===== STEP 3.5: R46/R47 type-03 injection =====
print("\n=== Step 3.5: R46/R47 type-03 injection ===")
os.system('python build/inject_r46_r47.py')
print("  R46/R47 injected")

# ===== STEP 3.6: R1188 comprehensive name-entry screen patch =====
print("\n=== Step 3.6: R1188 comprehensive patch ===")
os.system('python tools/patch_r1188_comprehensive.py')
print("  R1188 patched (kana, stat/sidebar/tab labels, banner, PCSX2 replacements)")

# ===== STEP 3.7: R1188 stat label bw=256 patch =====
print("\n=== Step 3.7: R1188 stat labels (bw=256) ===")
os.system('python tools/patch_r1188_bw256.py')
print("  R1188 stat labels patched (bw=256)")

# ===== STEP 3.8: R2100 chargen font atlas patch =====
print("\n=== Step 3.8: R2100 chargen font atlas ===")
os.system('python tools/patch_r2100.py')

# ===== STEP 3.9: R2138 unified patcher (all sub-resources) =====
print("\n=== Step 3.9: R2138 unified patcher (sub0/4/6/7/25/26/27) ===")
os.system('python tools/patch_r2138.py')

# ===== STEP 4: Variable-size type-2 injection + Section 1 patching =====
print("\n=== Step 4: Variable-size type-2 + Section 1 patching ===")

from patch_section1_offsets import inject_and_patch

# Load ALL type-2 translations
all_trans = {}
for fn in sorted(glob.glob('data/type2_translated/batch_*.json')):
    try:
        d = json.load(open(fn, encoding='utf-8'))
        for e in d:
            r = e['resource']
            mi = e['msg_index']
            en = e.get('english', '')
            if not en:
                continue
            if en.startswith('[DATA]') or en.startswith('[LAYOUT]') or en.startswith('[BINARY]'):
                continue
            if en.startswith('[MAP]') or en.startswith('[SYSTEM]') or en.startswith('[GLYPH'):
                continue
            if en.startswith('[DEBUG]'):
                continue
            if any(ord(c) > 127 for c in en):
                continue
            if r not in all_trans:
                all_trans[r] = {}
            all_trans[r][mi] = en
    except Exception as ex:
        print(f"  Warning: {fn}: {ex}")

print(f"  Loaded translations for {len(all_trans)} resources")

manifest = json.load(open('extracted/packdata_resources/manifest.json', encoding='utf-8'))
type02_resources = set()
for r in all_trans:
    if r < len(manifest) and not manifest[r].get('skipped') and manifest[r].get('type_code') == 2:
        type02_resources.add(r)

# Exclude R1193 -- handled manually in Step 5 (has trailing data without FFFF terminator)
type02_resources.discard(1193)

print(f"  Type-02 dialogue resources: {len(type02_resources)}")

os.makedirs('build/patched_type2', exist_ok=True)
total_patched = 0
total_encoded = 0

for r_id in sorted(type02_resources):
    msg_trans = all_trans[r_id]

    # Encode English text to glyph lists
    encoded_trans = {}
    for mi, en_text in msg_trans.items():
        # word_wrap removed — translations already have proper " / " breaks
        glyphs = []
        parts = en_text.split(' / ')
        line_count = 0
        for pi, part in enumerate(parts):
            if pi > 0:
                line_count += 1
                if line_count >= 3:
                    # Insert page break every 3 lines (wait for input, clear, continue)
                    glyphs.append(0xFFD2)
                    line_count = 0
                else:
                    glyphs.append(0xFFFE)
            for ch in part:
                glyphs.append(enc(ch))
        encoded_trans[mi] = glyphs

    result = inject_and_patch(
        r_id, encoded_trans,
        'extracted/packdata_raw',
        'build/patched_type2'
    )

    if result[0]:
        total_patched += 1
        total_encoded += len(encoded_trans)

print(f"  Patched {total_patched} resources, {total_encoded} messages")

# ===== STEP 5: R1193 intro narration injection =====
# R1193 has trailing data after its last FFFF terminator that inject_and_patch would drop.
# We handle it here: inject English into FFFF groups, preserve trailing data intact.
print("\n=== Step 5: R1193 intro narration ===")
if 1193 in all_trans and os.path.exists('extracted/packdata_raw/1193_type02.raw'):
    raw = bytearray(open('extracted/packdata_raw/1193_type02.raw', 'rb').read())
    orig_bytes = bytes(raw)

    sec2_size = struct.unpack_from('<I', raw, 0x14)[0]
    sec2_offset = struct.unpack_from('<I', raw, 0x18)[0]
    sec2_end = sec2_offset + sec2_size
    sec2_data = raw[sec2_offset:sec2_end]
    n_words = len(sec2_data) // 2
    words_s2 = [struct.unpack_from('>H', sec2_data, i * 2)[0] for i in range(n_words)]

    # Parse FFFF-delimited groups AND capture trailing data
    groups_1193 = []
    start_1193 = 0
    last_ffff_pos = -1
    for i_w, w in enumerate(words_s2):
        if w == 0xFFFF:
            groups_1193.append(words_s2[start_1193:i_w])
            start_1193 = i_w + 1
            last_ffff_pos = i_w
    trailing_data = words_s2[start_1193:] if start_1193 < n_words else []

    # Encode and inject English translations into groups
    msg_trans_1193 = all_trans[1193]
    replaced_1193 = 0
    for mi, en_text in msg_trans_1193.items():
        glyphs = []
        parts = en_text.split(' / ')
        line_count = 0
        for pi, part in enumerate(parts):
            if pi > 0:
                line_count += 1
                if line_count >= 3:
                    glyphs.append(0xFFD2)
                    line_count = 0
                else:
                    glyphs.append(0xFFFE)
            for ch in part:
                glyphs.append(enc(ch))
        if mi < len(groups_1193):
            groups_1193[mi] = glyphs
            replaced_1193 += 1

    # NOTE: Trailing data translation DISABLED. Growing section 1 from 702->1716
    # bytes may be causing VIF FIFO crashes. The intro text system is not yet
    # understood well enough to safely patch. Keep trailing data as original Japanese.
    # TODO: Investigate intro text rendering before re-enabling.

    # Rebuild Section 2: groups + FFFF terminators + trailing data
    new_sec2 = bytearray()
    for group in groups_1193:
        for g in group:
            new_sec2 += struct.pack('>H', g)
        new_sec2 += struct.pack('>H', 0xFFFF)
    for t in trailing_data:
        new_sec2 += struct.pack('>H', t)

    new_sec2_size = len(new_sec2)

    # Build injected file
    section1 = bytearray(raw[:sec2_offset])
    struct.pack_into('<I', section1, 0x14, new_sec2_size)
    after_sec2 = raw[sec2_end:]
    injected = bytes(section1) + bytes(new_sec2) + bytes(after_sec2)

    # Patch Section 1 offsets
    from patch_section1_offsets import patch_section1
    result_1193 = patch_section1(orig_bytes, injected)

    # Pad to sector boundary
    sc = math.ceil(len(result_1193) / SECTOR)
    if len(result_1193) < sc * SECTOR:
        result_1193 = result_1193 + b'\x00' * (sc * SECTOR - len(result_1193))

    open('build/patched_type2/1193_type02.raw', 'wb').write(result_1193)
    print(f"  R1193 injected: {replaced_1193} messages, sec2 {sec2_size}->{new_sec2_size} bytes")
else:
    # Fallback: copy existing file
    if os.path.exists('build/packdata_resources/1193_type02.raw'):
        shutil.copy('build/packdata_resources/1193_type02.raw', 'build/patched_type2/1193_type02.raw')
        print("  R1193 preserved (no translation found)")

# ===== STEP 6: Merge and clean =====
print("\n=== Step 6: Merge resources ===")
for f in os.listdir('build/patched_type2'):
    shutil.copy(f'build/patched_type2/{f}', f'build/packdata_resources/{f}')

binary_resources = [677,690,712,715,726,741,750,757,769,780,785,787,793,795,797,799,
    801,803,816,837,839,852,860,862,864,866,868,870,871,873,875,877,879,881,883,885,
    889,917,920,1057,1061,1072,1073,1077,1084,1091,1093,1099,1105,1109,1110,1112,
    1123,1133,1141,1145,1146,1147,1174,1192,1912,1930,1931,1933,1934,1935,1936,
    1939,1940,1941,1948,1952,1953,1959,1972,2141,2144,2161,2162,2163,2166,2174,
    2176,2200,2201,2204,2206,2207,2208,2588,2589,2651,2652,2653]
for r in binary_resources:
    f = f'build/packdata_resources/{r:04d}_type02.raw'
    if os.path.exists(f):
        os.remove(f)

file_count = len(os.listdir('build/packdata_resources'))
print(f"  {file_count} files in build/packdata_resources")

# ===== STEP 7: Rebuild PACKDATA =====
print("\n=== Step 7: Rebuild PACKDATA.DIG ===")
os.system('python build/rebuild_packdata.py')

# ===== STEP 8: Build ISO =====
print("\n=== Step 8: Build ISO ===")
d = open('build/PACKDATA_v3.DIG', 'rb').read()
shutil.copy2('Busin 0 - Wizardry Alternative Neo (Japan) (v2.01).iso', 'build/BUSIN0_EN_v9.iso')
with open('build/BUSIN0_EN_v9.iso', 'r+b') as iso:
    iso.seek(16 * SECTOR)
    pvd = iso.read(SECTOR)
    root_lba = struct.unpack_from('<I', pvd, 158)[0]
    root_size = struct.unpack_from('<I', pvd, 166)[0]
    iso.seek(root_lba * SECTOR)
    root_dir = iso.read(root_size)
    pos = 0
    while pos < len(root_dir):
        rec_len = root_dir[pos]
        if rec_len == 0:
            break
        name_len = root_dir[pos + 32]
        name = root_dir[pos + 33:pos + 33 + name_len].decode('ascii', errors='replace')
        if 'PACKDATA' in name:
            pack_lba = struct.unpack_from('<I', root_dir, pos + 2)[0]
            iso.seek(root_lba * SECTOR + pos + 10)
            iso.write(struct.pack('<I', len(d)))
            iso.write(struct.pack('>I', len(d)))
            iso.seek(pack_lba * SECTOR)
            iso.write(d)
            break
        pos += rec_len

# ===== STEP 8.2: Fix PACKDATA overflow into BSN2_0.DSI =====
# If our PACKDATA grew past the original end, shift all subsequent files
# forward to prevent overwriting BSN2_0.DSI (audio) and other files.
print("\n=== Step 8.2: Check PACKDATA overflow ===")
with open('build/BUSIN0_EN_v9.iso', 'r+b') as iso:
    iso.seek(16 * SECTOR)
    pvd = iso.read(SECTOR)
    root_lba = struct.unpack_from('<I', pvd, 158)[0]
    root_size = struct.unpack_from('<I', pvd, 166)[0]
    iso.seek(root_lba * SECTOR)
    root_dir = bytearray(iso.read(root_size))

    # Parse all directory entries
    dir_entries = []
    pos = 0
    while pos < len(root_dir):
        rec_len = root_dir[pos]
        if rec_len == 0:
            break
        name_len = root_dir[pos + 32]
        name = root_dir[pos + 33:pos + 33 + name_len].decode('ascii', errors='replace')
        lba = struct.unpack_from('<I', root_dir, pos + 2)[0]
        size = struct.unpack_from('<I', root_dir, pos + 10)[0]
        dir_entries.append((pos, name, lba, size))
        pos += rec_len

    # Find PACKDATA end and first file after it
    pack_entry = [e for e in dir_entries if 'PACKDATA' in e[1]]
    if pack_entry:
        _, _, pack_lba, pack_size = pack_entry[0]
        pack_end_lba = pack_lba + math.ceil(pack_size / SECTOR)

        # Find all files after PACKDATA's START (they could be within the
        # overflow zone). Use pack_lba, not pack_end_lba, to catch files
        # that started right after the ORIGINAL (smaller) PACKDATA.
        after_pack = sorted(
            [e for e in dir_entries if e[2] > pack_lba and 'PACKDATA' not in e[1]],
            key=lambda e: e[2]
        )

        if after_pack:
            first_after_lba = after_pack[0][2]
            if pack_end_lba > first_after_lba:
                shift = pack_end_lba - first_after_lba
                print(f"  PACKDATA overflow: {shift} sectors into subsequent files")
                print(f"  Shifting {len(after_pack)} files forward by {shift} sectors...")

                # Read relocated files from the ORIGINAL ISO, not the working copy.
                # PACKDATA was written into the working ISO in Step 8, overwriting
                # the first N sectors of BSN2_0.DSI. Reading from the working ISO
                # would copy PACKDATA garbage into the relocated BSN2_0.DSI.
                orig_iso = open('Busin 0 - Wizardry Alternative Neo (Japan) (v2.01).iso', 'rb')

                # Shift files in REVERSE order (last first) to avoid overwriting
                for dir_off, name, old_lba, fsize in reversed(after_pack):
                    new_lba = old_lba + shift
                    sec_count = math.ceil(fsize / SECTOR)
                    # Read file data from ORIGINAL ISO (not working copy)
                    orig_iso.seek(old_lba * SECTOR)
                    fdata = orig_iso.read(sec_count * SECTOR)
                    # Write to new position
                    iso.seek(new_lba * SECTOR)
                    iso.write(fdata)
                    # Update directory entry LBA (both LE and BE)
                    struct.pack_into('<I', root_dir, dir_off + 2, new_lba)
                    struct.pack_into('>I', root_dir, dir_off + 6, new_lba)

                orig_iso.close()

                # Write updated directory
                iso.seek(root_lba * SECTOR)
                iso.write(root_dir)

                # Extend ISO to accommodate shifted content
                iso.seek(0, 2)
                current_size = iso.tell()
                needed = (after_pack[-1][2] + shift + math.ceil(after_pack[-1][3] / SECTOR)) * SECTOR
                if needed > current_size:
                    iso.seek(needed - 1)
                    iso.write(b'\x00')

                # Also update PVD volume space size if needed
                new_vol_sectors = math.ceil(needed / SECTOR)
                iso.seek(16 * SECTOR + 80)
                iso.write(struct.pack('<I', new_vol_sectors))
                iso.write(struct.pack('>I', new_vol_sectors))

                print(f"  Done. ISO extended by {shift * SECTOR:,} bytes")
            else:
                print(f"  No overflow (PACKDATA ends at {pack_end_lba}, next file at {first_after_lba})")

# ===== STEP 8.4: Patch EXE =====
print("\n=== Step 8.4: Patch EXE ===")
os.system('python build/patch_exe.py')

# ===== STEP 8.5: Patch EXE into ISO =====
print("\n=== Step 8.5: Patch EXE ===")
exe_path = 'build/SLPM_653.78_patched'
if os.path.exists(exe_path):
    exe_data = open(exe_path, 'rb').read()
    with open('build/BUSIN0_EN_v9.iso', 'r+b') as iso:
        iso.seek(16 * SECTOR)
        pvd = iso.read(SECTOR)
        root_lba = struct.unpack_from('<I', pvd, 158)[0]
        root_size = struct.unpack_from('<I', pvd, 166)[0]
        iso.seek(root_lba * SECTOR)
        root_dir = iso.read(root_size)
        pos = 0
        while pos < len(root_dir):
            rec_len = root_dir[pos]
            if rec_len == 0:
                break
            name_len = root_dir[pos + 32]
            name = root_dir[pos + 33:pos + 33 + name_len].decode('ascii', errors='replace')
            if 'SLPM' in name:
                exe_lba = struct.unpack_from('<I', root_dir, pos + 2)[0]
                iso.seek(root_lba * SECTOR + pos + 10)
                iso.write(struct.pack('<I', len(exe_data)))
                iso.write(struct.pack('>I', len(exe_data)))
                iso.seek(exe_lba * SECTOR)
                iso.write(exe_data)
                print(f"  EXE patched: {len(exe_data):,} bytes at LBA {exe_lba}")
                break
            pos += rec_len
else:
    print("  No patched EXE found, skipping")

print(f"\n{'=' * 60}")
print(f"  BUSIN0_EN_v9.iso built ({len(d):,} bytes)")
print(f"  Variable-size + Section 1 opcode patching + EXE")
print(f"{'=' * 60}")
