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
for fix in ['chunk_r38_fix.json', 'chunk_r43_fix.json', 'chunk_r37_extra.json', 'chunk_r40_r42_translated.json', 'chunk_r36_translated.json', 'chunk_r37_r48_r49_translated.json', 'chunk_r43_r45_translated.json', 'chunk_r35_menus_fix.json']:
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

for r_id in [34, 35, 2654]:  # In-place translation (NONE are truly flat: each needs its own data_start)
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
    elif r_id == 35:
        # R35 is NOT flat: it has a 0x20-byte type-02-style header (sec2_off
        # LE u32 = 0x230 at +0x18) followed at 0x20 by a 25-entry offset table
        # (BE u16 count 0x0019 + ascending BE u32s 0x68, 0x6E, ...) ending at
        # 0x86, where the first FFFF sits. Scanning from byte 0 made "group 0"
        # = header + offset table, and message 1 ('Save') was written over it
        # (the v85 QA bug: header destroyed, table zeroed). Text starts right
        # after the table. Layout + mapping verified empirically:
        # build/recon_v85/qa/r35_alignment_check.py
        data_start = 0x22 + 4 * struct.unpack_from('>H', orig, 0x20)[0]  # 0x86
    fp = [i for i in range(data_start, len(orig) - 1, 2) if struct.unpack_from('>H', orig, i)[0] == 0xFFFF]
    groups = []
    prev = data_start
    for f in fp:
        groups.append((prev, f + 2))
        prev = f + 2
    out = bytearray(orig)
    rep = 0
    for gi, (g_s, g_e) in enumerate(groups):
        if r_id == 34:
            # R34: group 0 is a STRUCTURAL TABLE (word[0]=49 count followed by
            # 49 ascending u16 values, zero-interleaved), NOT text — never write it.
            # Group 1 is empty; item-name text starts at group 2 = message 1.
            # Alignment verified empirically (build/recon_v85/font-artifacts/
            # r34_alignment_check.py): decoded Japanese of group gi matches the
            # chunk 'japanese' of message gi-1 for 24/25 entries exactly
            # (the 25th differs by one ambiguous glyph-map entry only).
            if gi == 0:
                continue
            mi = gi - 1
        elif r_id == 35:
            # R35: group 0 (scanned from data_start=0x86) is an EMPTY pre-text
            # group (lone FFFF at 0x86) — never write it. Text group gi maps
            # to message gi - 1. Alignment verified empirically
            # (build/recon_v85/qa/r35_alignment_check.py): decoded Japanese of
            # group gi matches the chunk 'japanese' of message gi-1 for 16/19
            # entries exactly (the other 3 differ only by '■' placeholder
            # glyphs in the chunk Japanese, not by alignment).
            if gi == 0:
                continue
            mi = gi - 1
        else:
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
    if r_id == 34:
        # Guard: the structural table group (group 0) must be byte-identical
        # to the original — a corrupted table breaks R34 item lookups.
        t_s, t_e = groups[0]
        assert bytes(out[t_s:t_e]) == bytes(orig[t_s:t_e]), \
            "R34 structural table (group 0) was modified — aborting build"
    if r_id == 35:
        # Guard: header + offset table + empty group 0 (bytes 0 .. first text
        # group start, 0x88) must be byte-identical to the original — writing
        # there is exactly the v85 'Save'-over-header corruption.
        first_text = groups[1][0] if len(groups) > 1 else data_start
        assert bytes(out[:first_text]) == bytes(orig[:first_text]), \
            "R35 header/offset table (bytes 0..first text group) was modified — aborting build"
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

# ===== STEP 3.2: R39 quest UI labels and quest titles =====
print("\n=== Step 3.2: R39 quest labels and titles ===")
os.system('python build/inject_r39_quest.py')
print("  R39 quest labels injected")

# ===== STEP 3.5: R46/R47 type-03 injection =====
print("\n=== Step 3.5: R46/R47 type-03 injection ===")
os.system('python build/inject_r46_r47.py')
print("  R46/R47 injected")

# ===== STEP 3.6/3.7: R1188 patches DISABLED (BUG-3) =====
# R1188 is the LIVE dialogue/narration font: a 1024x1024 PSMT4 atlas of 24x24
# serif glyph cells DMA'd verbatim from disc to VRAM 0x3000 (proven via GS dump
# 20260612061701). The patchers below wrote 'name entry labels'/kana cells with
# layout assumptions off by 1008 bytes, scattering writes into ~150 live glyph
# cells (ASCII U,V,Z,[,r,x,y,z,~ and most kana) — the cause of the r/y/V glyph
# artifacts (BUG-3). The labels they wrote were never consumed: the companion
# EXE patch was never implemented, and tab labels already render English via
# R2138 sub7 (tools/patch_r2138.py, Step 3.9). R1188 must ship pristine.
print("\n=== Step 3.6/3.7: R1188 patches DISABLED (BUG-3: live dialogue font) ===")
# os.system('python tools/patch_r1188_comprehensive.py')
# os.system('python tools/patch_r1188_bw256.py')
# Delete any stale patched override so rebuild_packdata.py falls back to the
# pristine extracted/packdata_raw/1188_type01.raw.
_r1188_override = 'build/packdata_resources/1188_type01.raw'
if os.path.exists(_r1188_override):
    os.remove(_r1188_override)
    print("  Removed stale R1188 override — pristine 1188_type01.raw will be used")
else:
    print("  No R1188 override present — pristine 1188_type01.raw will be used")

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

# Purge stale artifacts from previous builds: the Section-1 patcher SKIPS
# resources whose Section 1 fails to walk, so a leftover *.raw from an older
# (corrupted) run would otherwise survive and be merged in Step 6.
_stale = glob.glob('build/patched_type2/*.raw')
for _f in _stale:
    os.remove(_f)
print(f"  Purged {len(_stale)} stale files from build/patched_type2")

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

    # R1203: Section 2 overflow guard.
    # The English translation grows Section 2 from 50,231 to ~76,054 words, exceeding
    # the u16 limit of 65,535.  The total must account for ALL groups (translated +
    # original), because every group still occupies space even if untranslated.
    # Binary search shows cap=1069 is the highest group index where the full Section 2
    # stays within 65,535 words (cumulative: 65,527).  Groups 1070-1632 (555 translated
    # messages) are left in their original Japanese to avoid the overflow.
    R1203_MAX_GROUP = 1069  # last group index that keeps total Section 2 <= 65535 words
    if r_id == 1203:
        before = len(encoded_trans)
        encoded_trans = {mi: g for mi, g in encoded_trans.items() if mi <= R1203_MAX_GROUP}
        dropped = before - len(encoded_trans)
        if dropped:
            print(
                "  R1203: capped at group %d — dropped %d overflow translations (groups %d-%d)"
                % (R1203_MAX_GROUP, dropped, R1203_MAX_GROUP + 1, max(msg_trans))
            )

    result = inject_and_patch(
        r_id, encoded_trans,
        'extracted/packdata_raw',
        'build/patched_type2'
    )

    if result[0]:
        total_patched += 1
        total_encoded += len(encoded_trans)
        print(f"  R{r_id}: {result[1]}")
    else:
        print(f"  R{r_id}: SKIPPED -- {result[1]}")

print(f"  Patched {total_patched} resources, {total_encoded} messages")

# ===== STEP 5: R1193 intro narration injection =====
# R1193's boot prologue (BUG-10) lives in a TRAILING block after the last FFFF
# group terminator, drawn line-by-line by 23 Section-1 0x14 records.
# tools/patch_r1193_narration.py injects the FFFF-group translations via
# inject_and_patch (group-0 narration islands preserved, patch_section1 runs
# inside), rebuilds the trailing block as 23 English lines (pages 4/3/2/4/1/
# 3/2/3/1, <= 23 glyphs each) and rewrites each 0x14 record's WORD_OFF/
# GLYPH_CNT exactly. Writes build/patched_type2/1193_type02.raw.
print("\n=== Step 5: R1193 intro narration ===")
if 1193 in all_trans and os.path.exists('extracted/packdata_raw/1193_type02.raw'):
    from patch_r1193_narration import build_r1193
    build_r1193('extracted/packdata_raw/1193_type02.raw', all_trans[1193],
                'build/patched_type2')
else:
    # Fallback: copy existing file
    if os.path.exists('build/packdata_resources/1193_type02.raw'):
        shutil.copy('build/packdata_resources/1193_type02.raw', 'build/patched_type2/1193_type02.raw')
        print("  R1193 preserved (no translation found)")

# ===== STEP 6: Merge and clean =====
print("\n=== Step 6: Merge resources ===")
for f in os.listdir('build/patched_type2'):
    shutil.copy(f'build/patched_type2/{f}', f'build/packdata_resources/{f}')

# Skip-fallback: any type-02 resource the Section-1 patcher SKIPPED this run
# has no file in build/patched_type2 — remove any stale override in
# build/packdata_resources so rebuild_packdata falls back to the pristine raw.
# (Only ids from type02_resources + 1193. R35 is EXCLUDED: although it has
# type_code 2 and appears in type02_resources, build/packdata_resources/
# 0035_type02.raw is written by Step 2 each run and must never be deleted here.)
for _rid in sorted((type02_resources | {1193}) - {35}):
    _name = f'{_rid:04d}_type02.raw'
    if not os.path.exists(f'build/patched_type2/{_name}'):
        _stale_out = f'build/packdata_resources/{_name}'
        if os.path.exists(_stale_out):
            os.remove(_stale_out)
            print(f"  R{_rid} skipped this run — removed stale override {_name} (ships pristine)")

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

# ===== Step 6.5: v86 pre-rendered UI strips + item DB =====
# Runs AFTER Step 6's stale-override purge and binary_resources deletion loop,
# and BEFORE Step 7's PACKDATA rebuild. This placement is CRITICAL and safe:
#   - The Step 6 binary_resources loop deletes 2141/2144 (and other *_type02.raw
#     names) BEFORE this block, so facility/strip outputs written here survive to
#     Step 7. If this block ran before that loop, 2141_type02/2144_type02 would be
#     deleted out from under us.
#   - Several outputs here use *_type02.raw names (1359/1360/1361/1362/1363/1365/
#     1367/1910/1054). Even though some of those ids may appear in type02_resources
#     or binary_resources, BOTH the Step 6 stale-override purge and the
#     binary_resources deletion loop have already run by this point — nothing
#     between here and Step 7 deletes any *.raw — so these outputs ship intact.
#   - inject_r34_db.py reads build/packdata_resources/2654_type44.raw (Step 2's
#     output, carrying co-op sub0 translations) as its R2654 base and overwrites
#     0034_type20.raw + 2654_type44.raw. Neither the stale-override purge nor the
#     binary_resources loop touch those names (both operate on *_type02.raw only;
#     R2654 is type44, R0034 is type20), so the Step 2 base survives to here.
print("\n=== Step 6.5: v86 pre-rendered UI strips + item DB ===")
for script in [
    'tools/patch_r2124.py',
    'tools/patch_r1365.py',
    'tools/patch_battle_strips.py',
    'tools/patch_camp_strips.py',
    'tools/patch_facility_strips.py',
    'tools/patch_r2147.py',
    'tools/patch_r1370.py',
    'tools/patch_r2880.py',
    'tools/patch_r2881_ending.py',
    'build/inject_r34_db.py',
]:
    rc = os.system(f'python {script}')
    if rc != 0:
        print(f'FATAL: v86 patcher failed: {script}')
        sys.exit(1)

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
