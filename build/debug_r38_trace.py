#!/usr/bin/env python3
"""
Debug script: trace EXACTLY what happens to R38 at each build pipeline step.
Does NOT modify build_v9.py -- runs each step independently.
"""
import sys, os, struct, json, hashlib, shutil, math

os.chdir('C:/Programmieren/wizardrytranslation')

SECTOR = 2048
R38_ORIG = 'extracted/packdata_raw/0038_type01.raw'
R38_PATCHED = 'build/packdata_resources/0038_type01.raw'
PACKDATA_OUT = 'build/PACKDATA_v3.DIG'

def md5(path):
    if not os.path.exists(path):
        return "FILE_NOT_FOUND"
    return hashlib.md5(open(path, 'rb').read()).hexdigest()

def file_size(path):
    if not os.path.exists(path):
        return -1
    return os.path.getsize(path)

def read_first_glyphs_after_first_ffff(data, label, count=6):
    """Find first FFFF in glyph stream, then print next `count` glyph values."""
    # Skip 16-byte sub-header
    for off in range(16, len(data) - 1, 2):
        val = struct.unpack_from('>H', data, off)[0]
        if val == 0xFFFF:
            # Found first FFFF - read next glyphs
            glyphs = []
            pos = off + 2
            for _ in range(count):
                if pos + 2 <= len(data):
                    g = struct.unpack_from('>H', data, pos)[0]
                    glyphs.append(g)
                    pos += 2
            glyph_strs = [f"0x{g:04X}" for g in glyphs]
            print(f"  [{label}] First {count} glyphs after first FFFF (offset 0x{off:04X}): {', '.join(glyph_strs)}")
            return glyphs
    print(f"  [{label}] No FFFF found in data!")
    return []

def is_english_glyphs(glyphs):
    """Check if glyph values look like English (low values 0-127) vs Japanese (high values)."""
    text_glyphs = [g for g in glyphs if g < 0xFB00]  # exclude control codes
    if not text_glyphs:
        return "NO_TEXT_GLYPHS"
    avg = sum(text_glyphs) / len(text_glyphs)
    max_g = max(text_glyphs)
    if max_g < 200:
        return f"ENGLISH (avg={avg:.0f}, max={max_g})"
    else:
        return f"JAPANESE (avg={avg:.0f}, max={max_g})"

def count_ffff(data, start=16):
    """Count FFFF markers in data."""
    count = 0
    for off in range(start, len(data) - 1, 2):
        val = struct.unpack_from('>H', data, off)[0]
        if val == 0xFFFF:
            count += 1
    return count

def sample_multiple_messages(data, msg_indices=[1, 5, 10], label=""):
    """Sample specific FFFF groups to check content."""
    groups = []
    prev = 16  # after sub-header
    for off in range(16, len(data) - 1, 2):
        val = struct.unpack_from('>H', data, off)[0]
        if val == 0xFFFF:
            groups.append((prev, off))
            prev = off + 2

    for mi in msg_indices:
        if mi < len(groups):
            gs, ge = groups[mi]
            # Read first few glyphs of this group
            glyphs = []
            for p in range(gs, min(ge, gs + 12), 2):
                glyphs.append(struct.unpack_from('>H', data, p)[0])
            glyph_strs = [f"0x{g:04X}" for g in glyphs]
            lang = is_english_glyphs(glyphs)
            print(f"  [{label}] Group {mi}: {', '.join(glyph_strs[:6])} => {lang}")

# ============================================================================
print("=" * 70)
print("  R38 STEP-BY-STEP PIPELINE DEBUG TRACE")
print("=" * 70)

# ------ CHECKPOINT 0: Original file ------
print("\n--- CHECKPOINT 0: Original extracted file ---")
orig_data = open(R38_ORIG, 'rb').read()
print(f"  File: {R38_ORIG}")
print(f"  Size: {len(orig_data)} bytes, MD5: {md5(R38_ORIG)}")
print(f"  FFFF count: {count_ffff(orig_data)}")
read_first_glyphs_after_first_ffff(orig_data, "ORIGINAL")
sample_multiple_messages(orig_data, [1, 5, 10, 20], "ORIGINAL")

# ------ CHECKPOINT 0.5: Current state of patched file (before running anything) ------
print("\n--- CHECKPOINT 0.5: Current state of build/packdata_resources/0038_type01.raw ---")
if os.path.exists(R38_PATCHED):
    cur_data = open(R38_PATCHED, 'rb').read()
    print(f"  Size: {len(cur_data)} bytes, MD5: {md5(R38_PATCHED)}")
    print(f"  FFFF count: {count_ffff(cur_data)}")
    read_first_glyphs_after_first_ffff(cur_data, "CURRENT-PATCHED")
    sample_multiple_messages(cur_data, [1, 5, 10, 20], "CURRENT-PATCHED")
    same = md5(R38_ORIG) == md5(R38_PATCHED)
    print(f"  Same as original? {same}")
else:
    print("  File does not exist yet")

# ------ STEP 1: Run build_full_english_v2.py ------
print("\n--- STEP 1: Running build_full_english_v2.py ---")
# Back up current patched file
if os.path.exists(R38_PATCHED):
    shutil.copy2(R38_PATCHED, R38_PATCHED + '.bak_pre_step1')

ret = os.system('PYTHONIOENCODING=utf-8 python build/build_full_english_v2.py > build/debug_step1_output.txt 2>&1')
print(f"  Exit code: {ret}")

# Check what v2 pipeline said about R38
with open('build/debug_step1_output.txt', 'r', encoding='utf-8', errors='replace') as f:
    for line in f:
        if 'R0038' in line or 'r38' in line.lower() or 'R38' in line:
            print(f"  v2 output: {line.rstrip()}")

print("\n--- CHECKPOINT 1: After build_full_english_v2.py ---")
if os.path.exists(R38_PATCHED):
    step1_data = open(R38_PATCHED, 'rb').read()
    print(f"  Size: {len(step1_data)} bytes, MD5: {md5(R38_PATCHED)}")
    print(f"  FFFF count: {count_ffff(step1_data)}")
    read_first_glyphs_after_first_ffff(step1_data, "AFTER-STEP1")
    sample_multiple_messages(step1_data, [1, 5, 10, 20], "AFTER-STEP1")
    same_as_orig = md5(R38_ORIG) == md5(R38_PATCHED)
    print(f"  Same as original? {same_as_orig}")
    lang_glyphs = read_first_glyphs_after_first_ffff(step1_data, "STEP1-LANG-CHECK", 20)
    print(f"  Language: {is_english_glyphs(lang_glyphs)}")
else:
    print("  R38 NOT FOUND after Step 1!")

# ------ STEP 2: Run the build_v9.py Step 2 logic for R38 ONLY ------
print("\n--- STEP 2: Running build_v9 fixed-size injection for R38 ---")

# Save step1 version
if os.path.exists(R38_PATCHED):
    shutil.copy2(R38_PATCHED, R38_PATCHED + '.bak_post_step1')

# Re-implement build_v9 Step 2 logic for R38 only
sys.path.insert(0, 'tools')
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
for fix in ['chunk_r38_fix.json', 'chunk_r43_fix.json', 'chunk_r37_extra.json',
            'chunk_r40_r42_translated.json', 'chunk_r36_translated.json',
            'chunk_r37_r48_r49_translated.json', 'chunk_r43_r45_translated.json']:
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
    segments = text.split(' / ')
    wrapped = []
    for seg in segments:
        while len(seg) > max_chars:
            brk = seg.rfind(' ', 0, max_chars + 1)
            if brk <= 0:
                brk = max_chars
            wrapped.append(seg[:brk])
            seg = seg[brk:].lstrip(' ')
        wrapped.append(seg)
    return ' / '.join(wrapped)

r_id = 38
tc = '01'
# KEY: build_v9 reads from ORIGINAL, not from the step1 output!
orig = bytearray(open(f'extracted/packdata_raw/{r_id:04d}_type{tc}.raw', 'rb').read())
print(f"  build_v9 Step 2 reads FROM: extracted/packdata_raw/0038_type01.raw (ORIGINAL)")
print(f"  NOT from build/packdata_resources/0038_type01.raw (Step 1 output)")

rt = {m: e for (r, m), e in translations.items() if r == r_id}
print(f"  Translations available for R38: {len(rt)} messages")
print(f"  Message indices: {sorted(rt.keys())[:20]}...")

fp = [i for i in range(0, len(orig) - 1, 2) if struct.unpack_from('>H', orig, i)[0] == 0xFFFF]
groups = []
prev = 0
for f in fp:
    groups.append((prev, f + 2))
    prev = f + 2

out = bytearray(orig)  # NOTE: starts from ORIGINAL
rep = 0
truncated = 0
for gi, (g_s, g_e) in enumerate(groups):
    mi = gi + 1
    if mi not in rt:
        continue
    en = rt[mi]
    if any(ord(c) > 127 for c in en):
        continue
    ocs = g_e - g_s - 2  # original content size (excluding FFFF terminator)
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

    # Fixed-size: pad or truncate
    while len(nc) < ocs:
        nc += struct.pack('>H', 0)
    if len(nc) > ocs:
        nc = nc[:ocs]
        truncated += 1
    out[g_s:g_e - 2] = nc
    rep += 1

pd_val = (SECTOR - len(out) % SECTOR) % SECTOR
out += b'\x00' * pd_val
open(R38_PATCHED, 'wb').write(out)

nf = sum(1 for i in range(0, len(out) - 1, 2) if struct.unpack_from('>H', out, i)[0] == 0xFFFF)
print(f"  Replaced: {rep} messages, Truncated: {truncated}")
print(f"  FFFF count: orig={len(fp)}, new={nf}, match={'YES' if len(fp)==nf else 'MISMATCH!'}")

print("\n--- CHECKPOINT 2: After build_v9 Step 2 injection ---")
step2_data = open(R38_PATCHED, 'rb').read()
print(f"  Size: {len(step2_data)} bytes, MD5: {md5(R38_PATCHED)}")
print(f"  FFFF count: {count_ffff(step2_data)}")
read_first_glyphs_after_first_ffff(step2_data, "AFTER-STEP2")
sample_multiple_messages(step2_data, [1, 5, 10, 20], "AFTER-STEP2")
lang_glyphs2 = read_first_glyphs_after_first_ffff(step2_data, "STEP2-LANG-CHECK", 20)
print(f"  Language: {is_english_glyphs(lang_glyphs2)}")

# Compare Step 1 vs Step 2
step1_path = R38_PATCHED + '.bak_post_step1'
if os.path.exists(step1_path):
    s1md5 = md5(step1_path)
    s2md5 = md5(R38_PATCHED)
    print(f"\n  Step1 MD5: {s1md5}")
    print(f"  Step2 MD5: {s2md5}")
    print(f"  Step 2 OVERWROTE Step 1? {'YES - files differ!' if s1md5 != s2md5 else 'NO - same file'}")

    # Compare FFFF counts
    s1data = open(step1_path, 'rb').read()
    s1_ffff = count_ffff(s1data)
    s2_ffff = count_ffff(step2_data)
    print(f"  Step1 FFFF count: {s1_ffff}, Step2 FFFF count: {s2_ffff}")
    print(f"  Step1 size: {len(s1data)}, Step2 size: {len(step2_data)}")

# ------ STEP 3: Run rebuild_packdata.py ------
print("\n--- STEP 3: Running rebuild_packdata.py ---")
ret = os.system('PYTHONIOENCODING=utf-8 python build/rebuild_packdata.py > build/debug_step3_output.txt 2>&1')
print(f"  Exit code: {ret}")

with open('build/debug_step3_output.txt', 'r', encoding='utf-8', errors='replace') as f:
    for line in f:
        print(f"  rebuild: {line.rstrip()}")

# ------ CHECKPOINT 3: Check R38 in rebuilt PACKDATA_v3.DIG ------
print("\n--- CHECKPOINT 3: R38 in rebuilt PACKDATA_v3.DIG ---")
if os.path.exists(PACKDATA_OUT):
    manifest = json.load(open('extracted/packdata_resources/manifest.json', encoding='utf-8'))

    # Read TOC to find R38's location
    with open(PACKDATA_OUT, 'rb') as f:
        toc = []
        for _ in range(2883):
            so, sc, tc_val = struct.unpack('<III', f.read(12))
            toc.append((so, sc, tc_val))

        r38_so, r38_sc, r38_tc = toc[38]
        print(f"  TOC entry 38: sector_offset={r38_so}, sector_count={r38_sc}, type={r38_tc}")

        f.seek(r38_so * SECTOR)
        r38_in_pack = f.read(r38_sc * SECTOR)

    print(f"  R38 in PACKDATA: {len(r38_in_pack)} bytes")
    print(f"  FFFF count: {count_ffff(r38_in_pack)}")
    read_first_glyphs_after_first_ffff(r38_in_pack, "IN-PACKDATA")
    sample_multiple_messages(r38_in_pack, [1, 5, 10, 20], "IN-PACKDATA")
    lang_glyphs3 = read_first_glyphs_after_first_ffff(r38_in_pack, "PACKDATA-LANG", 20)
    print(f"  Language: {is_english_glyphs(lang_glyphs3)}")

    # Compare: is R38 in PACKDATA the same as the patched file?
    pack_md5 = hashlib.md5(r38_in_pack).hexdigest()
    step2_md5_trimmed = hashlib.md5(step2_data[:len(r38_in_pack)]).hexdigest()
    print(f"  PACKDATA R38 MD5: {pack_md5}")
    print(f"  Patched file MD5 (trimmed): {step2_md5_trimmed}")
    print(f"  Match? {'YES' if pack_md5 == step2_md5_trimmed else 'NO - MISMATCH!'}")
else:
    print(f"  {PACKDATA_OUT} not found!")

# ------ SUMMARY ------
print("\n" + "=" * 70)
print("  SUMMARY")
print("=" * 70)
print(f"  Step 1 (v2 pipeline): Injects R38 with variable-size offset-table rebuild")
print(f"  Step 2 (v9 fix):      OVERWRITES R38 with fixed-size in-place injection")
print(f"                        Source: ORIGINAL file (not Step 1 output)")
print(f"  Step 3 (rebuild):     Packs whatever is in build/packdata_resources/")
print()
print("  KEY FINDING: build_v9.py Step 2 reads from extracted/packdata_raw/ (ORIGINAL)")
print("  and overwrites the Step 1 output. This is BY DESIGN for fixed-size safety.")
print("  The question is whether the Step 2 output is actually English.")
print()

# Cleanup backup files
for ext in ['.bak_pre_step1', '.bak_post_step1']:
    p = R38_PATCHED + ext
    if os.path.exists(p):
        os.remove(p)

print("Done. See debug_r38_stepwise.md for full analysis.")
