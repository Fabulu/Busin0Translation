#!/usr/bin/env python3
"""Diagnose R37 instruction text truncation."""
import struct, json, sys, os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(BASE)

sys.path.insert(0, 'tools')
from encode_english_text import encode_text, table

SECTOR = 2048

# --- Step 1: Read original R37 from PACKDATA.DIG ---
with open('extracted/PACKDATA.DIG', 'rb') as f:
    toc = f.read(2883 * 12)
    r37_so, r37_sc, _ = struct.unpack_from('<III', toc, 37 * 12)
    f.seek(r37_so * SECTOR)
    orig = f.read(r37_sc * SECTOR)

msg_count = struct.unpack_from('>H', orig, 16)[0]
print(f"R37: {len(orig)} bytes, {msg_count} messages")
print(f"  TOC: sector_offset={r37_so}, sector_count={r37_sc}")
print()

# Parse offset table
ot_start = 20
groups = []
for gi in range(msg_count):
    off = struct.unpack_from('>H', orig, ot_start + gi * 4)[0]
    flags = struct.unpack_from('>H', orig, ot_start + gi * 4 + 2)[0]
    start = 16 + off
    # Find FFFF terminator
    pos = start
    while pos < len(orig) - 1:
        if struct.unpack_from('>H', orig, pos)[0] == 0xFFFF:
            break
        pos += 2
    groups.append((start, pos))

# --- Step 2: Load translations ---
trans = {}
for fn in ['chunk_r37_r48_r49_translated.json', 'chunk_r37_extra.json']:
    fp = f'data/translate_chunks/{fn}'
    if os.path.exists(fp):
        for e in json.load(open(fp, encoding='utf-8')):
            if e.get('resource') == 37:
                trans[e['message']] = e['english']

# Also check main chunks
for i in range(10):
    fp = f'data/translate_chunks/chunk_{i:02d}_translated.json'
    if os.path.exists(fp):
        for e in json.load(open(fp, encoding='utf-8')):
            if e.get('resource') == 37:
                # Don't override fix files
                if e['message'] not in trans:
                    trans[e['message']] = e['english']

# Fix files override main chunks, so reload fix files last
for fn in ['chunk_r37_r48_r49_translated.json', 'chunk_r37_extra.json']:
    fp = f'data/translate_chunks/{fn}'
    if os.path.exists(fp):
        for e in json.load(open(fp, encoding='utf-8')):
            if e.get('resource') == 37:
                trans[e['message']] = e['english']


def clean_and_encode(english_text):
    """Same as build_full_english_v2.py"""
    text = english_text.rstrip()
    if not text:
        return []
    if text.endswith(' /'):
        text = text + ' '
    parts = text.split(' / ')
    while parts and not parts[-1].strip():
        parts.pop()
    glyphs = []
    for pi, part in enumerate(parts):
        part = part.strip()
        if pi > 0:
            glyphs.append(0xFFFE)
        if not part:
            continue
        line_glyphs = encode_text(part, max_chars_per_line=20, max_lines_per_page=3)
        glyphs.extend(line_glyphs)
    return glyphs


# --- Step 3: Analyze groups 0-16 ---
print("=" * 90)
print(f"{'Grp':>3} {'OrigBytes':>9} {'EngBytes':>8} {'+FFFE':>5} {'OrigEndsFFFE':>12} {'Fits?':>5} {'FitNoFF':>7} Translation")
print("=" * 90)

for gi in range(min(17, len(groups))):
    data_start, ffff_pos = groups[gi]
    orig_size = ffff_pos - data_start

    # Check if original ends with FFFE before FFFF
    orig_ends_fffe = False
    if orig_size >= 2:
        last_glyph = struct.unpack_from('>H', orig, ffff_pos - 2)[0]
        orig_ends_fffe = (last_glyph == 0xFFFE)

    # Dump original glyphs for this group
    orig_glyphs = []
    for p in range(data_start, ffff_pos, 2):
        orig_glyphs.append(struct.unpack_from('>H', orig, p)[0])

    eng_text = trans.get(gi, None)
    if eng_text is None:
        print(f"{gi:3d} {orig_size:9d}      --    --  ends_fffe={orig_ends_fffe}  (no translation)")
        continue

    glyphs = clean_and_encode(eng_text)
    eng_bytes = len(glyphs) * 2

    # With trailing FFFE (as current code does for gi <= 16)
    has_trailing_fffe = glyphs and glyphs[-1] == 0xFFFE
    eng_bytes_with_fffe = eng_bytes if has_trailing_fffe else eng_bytes + 2

    fits_with = "YES" if eng_bytes_with_fffe <= orig_size else "NO"
    fits_without = "YES" if eng_bytes <= orig_size else "NO"

    # Show what gets truncated
    trunc_info = ""
    if eng_bytes_with_fffe > orig_size:
        # How many glyphs fit?
        max_glyphs = orig_size // 2
        # The code adds FFFE, so effective content glyphs = max_glyphs - 1 (if FFFE added)
        trunc_info = f" TRUNCATED: need {eng_bytes_with_fffe}b, have {orig_size}b (overflow={eng_bytes_with_fffe - orig_size}b)"

    print(f"{gi:3d} {orig_size:9d} {eng_bytes:8d} {eng_bytes_with_fffe:5d}  ends_fffe={str(orig_ends_fffe):5s} {fits_with:>5s} {fits_without:>7s}  \"{eng_text.strip()}\"{trunc_info}")

print()
print("--- Detailed glyph breakdown for truncated messages ---")
for gi in range(min(17, len(groups))):
    data_start, ffff_pos = groups[gi]
    orig_size = ffff_pos - data_start
    eng_text = trans.get(gi, None)
    if eng_text is None:
        continue
    glyphs = clean_and_encode(eng_text)
    eng_bytes = len(glyphs) * 2
    has_trailing_fffe = glyphs and glyphs[-1] == 0xFFFE
    eng_bytes_with_fffe = eng_bytes if has_trailing_fffe else eng_bytes + 2

    if eng_bytes_with_fffe > orig_size:
        print(f"\n  Group {gi}: \"{eng_text.strip()}\"")
        print(f"    Original data size: {orig_size} bytes ({orig_size // 2} glyphs)")
        print(f"    Encoded glyphs ({len(glyphs)}): {[hex(g) for g in glyphs]}")
        print(f"    Encoded bytes: {eng_bytes}")
        print(f"    + trailing FFFE: {eng_bytes_with_fffe}")
        print(f"    Overflow: {eng_bytes_with_fffe - orig_size} bytes")
        print(f"    Without FFFE: {eng_bytes} bytes -> {'FITS' if eng_bytes <= orig_size else 'STILL TRUNCATED'}")

        # Show what the truncated result looks like
        max_bytes = orig_size
        max_glyphs_total = max_bytes // 2
        # Current code: adds FFFE then truncates to orig_size
        with_fffe = glyphs[:]
        if not has_trailing_fffe:
            with_fffe.append(0xFFFE)
        truncated = with_fffe[:max_glyphs_total]

        # Decode truncated glyphs back to text
        rev_table = {v: k for k, v in table.items()}
        decoded = ""
        for g in truncated:
            if g == 0xFFFE:
                decoded += "[FFFE]"
            elif g in rev_table:
                decoded += rev_table[g]
            else:
                decoded += f"[{g:04X}]"
        print(f"    Truncated renders as: \"{decoded}\"")

# --- Also show original R37 groups 0-16 trailing bytes ---
print()
print("--- Original R37 group endings (last 4 glyphs before FFFF) ---")
for gi in range(min(17, len(groups))):
    data_start, ffff_pos = groups[gi]
    orig_size = ffff_pos - data_start
    tail_start = max(data_start, ffff_pos - 8)
    tail = []
    for p in range(tail_start, ffff_pos, 2):
        tail.append(hex(struct.unpack_from('>H', orig, p)[0]))
    # Also show the FFFF
    ffff_val = hex(struct.unpack_from('>H', orig, ffff_pos)[0])
    print(f"  Group {gi:2d}: size={orig_size:4d}b  ...{' '.join(tail)} | {ffff_val}")
