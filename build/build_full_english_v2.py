#!/usr/bin/env python3
"""
build_full_english_v2.py  --  Fixed injection pipeline
======================================================

Fixes ALL five known bugs from the v1 pipeline:

  1. Font atlas assembly (palette position) -- ALREADY FIXED in generate_font_atlas.py
  2. Message counting mismatch -- v1 splits on FFFF only; translations index by
     FFFF-group numbering from full_decoded_text.txt.  Internal " / " in
     translations is converted to FFFE line-break tokens.
  3. Offset table not rebuilt -- Format A resources need recalculated offset tables
     after the glyph stream changes size.  FIXED: offset table is rebuilt.
  4. Stream start off by 2 -- the offset table's trailing 0xFFFF flag was mistaken
     for the glyph stream start.  FIXED: we properly parse the offset table to
     find the real stream start.
  5. Trailing " / " -- Translation chunks have literal " / " that the v1 pipeline
     encoded as visible slash glyphs.  FIXED: " / " is now correctly converted
     to 0xFFFE line-break tokens (matching the original binary structure).

Additional fixes:
  - Preserves data beyond payload_size (critical for type20/type03/type06 resources
    that have multi-section data beyond the declared payload).
  - Skips untranslated entries (Japanese == English, like resources 1053/1908/2124).
  - Fix chunks (r38_fix, r43_fix) override earlier chunk entries.

Usage:
    cd C:/Programmieren/wizardrytranslation
    python build/build_full_english_v2.py
"""

import sys, io, struct, json, glob, os, shutil, math

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(BASE)

sys.path.insert(0, 'tools')
from encode_english_text import encode_text, table

SECTOR = 2048

print('=' * 60)
print('  BUILD FULL ENGLISH PATCH  v2  (fixed pipeline)')
print('=' * 60)
print()

# ---------------------------------------------------------------------------
# STEP 1 -- Load and merge ALL translation chunks
# ---------------------------------------------------------------------------
print('STEP 1: Loading translation chunks ...')

# Load main chunks (chunk_00 .. chunk_09)
all_trans = []
for i in range(10):
    fp = f'data/translate_chunks/chunk_{i:02d}_translated.json'
    if os.path.exists(fp):
        chunk = json.load(open(fp, encoding='utf-8'))
        all_trans.extend(chunk)
        print(f'  {fp}: {len(chunk)} entries')

# Load fix chunks -- these OVERRIDE earlier entries for the same (resource, message)
fix_files = ['chunk_r38_fix.json', 'chunk_r43_fix.json', 'chunk_r37_extra.json',
             'chunk_r36_translated.json', 'chunk_r37_r48_r49_translated.json',
             'chunk_r40_r42_translated.json', 'chunk_r43_r45_translated.json',
             'chunk_r34_fix.json']
for fix_name in fix_files:
    fp = f'data/translate_chunks/{fix_name}'
    if os.path.exists(fp):
        chunk = json.load(open(fp, encoding='utf-8'))
        all_trans.extend(chunk)
        print(f'  {fp}: {len(chunk)} entries (OVERRIDE)')

print(f'  Total raw entries: {len(all_trans)}')

# De-duplicate: later entries win (so fix chunks override originals)
trans_map = {}  # (resource, message) -> entry
for entry in all_trans:
    r = entry.get('resource')
    m = entry.get('message')
    eng = entry.get('english', '')
    if r is None or m is None or not eng:
        continue
    trans_map[(int(r), int(m))] = entry

print(f'  Unique (resource, message) pairs: {len(trans_map)}')

# ---------------------------------------------------------------------------
# STEP 2 -- Clean translations and encode to glyph streams
# ---------------------------------------------------------------------------
print()
print('STEP 2: Cleaning and encoding translations ...')


def clean_and_encode(english_text):
    """
    Clean a translation string and encode it to a glyph stream.

    The translation chunks use " / " as a line-break delimiter.  Translations
    often end with a trailing " / " which would produce an extra trailing FFFE.
    That extra FFFE acts as a phantom blank line and can overflow fixed-size
    textboxes (e.g. R38 chargen descriptions are limited to 3 lines).  We strip
    trailing empty segments after splitting so the FFFE count matches the actual
    number of content lines.

    Algorithm:
    1. Split on " / " to get line segments.
    2. Strip trailing empty segments (prevents phantom blank lines).
    3. For each segment, encode via encode_text() (which handles word-wrapping).
    4. Insert FFFE tokens between segments.

    Returns a list of uint16 glyph values (including 0xFFFE line breaks).
    """
    text = english_text.rstrip()  # strip trailing whitespace only

    if not text:
        return []

    # Split on " / " to find FFFE boundaries
    # A trailing " /" (without final space) also indicates a line break
    # Normalize: if text ends with " /" add the trailing space for clean split
    if text.endswith(' /'):
        text = text + ' '

    parts = text.split(' / ')

    # Strip trailing empty segments to avoid phantom blank lines / FFFE overflow
    while parts and not parts[-1].strip():
        parts.pop()

    glyphs = []
    for pi, part in enumerate(parts):
        part = part.strip()
        if pi > 0:
            glyphs.append(0xFFFE)  # line break between parts
        if not part:
            # Empty part -- just the FFFE is enough (blank line / page cue)
            continue
        # Encode this line segment; encode_text handles word-wrapping within
        # the segment, adding its own FFFE + FFD2 for page breaks if needed.
        line_glyphs = encode_text(part, max_chars_per_line=20, max_lines_per_page=3)
        glyphs.extend(line_glyphs)

    return glyphs


# Group encoded translations by resource
encoded_by_res = {}   # resource_idx -> { message_idx: [glyphs] }
errors = 0
skipped_identity = 0

for (res, msg), entry in trans_map.items():
    english = entry.get('english', '')
    japanese = entry.get('japanese', '')

    # Skip identity translations (Japanese == English means untranslated)
    if english.strip() == japanese.strip():
        skipped_identity += 1
        continue

    try:
        glyphs = clean_and_encode(english)
        if glyphs:
            encoded_by_res.setdefault(res, {})[msg] = glyphs
    except Exception as e:
        errors += 1
        if errors <= 5:
            print(f'  ERROR encoding r{res}/m{msg}: {e}')

total_encoded = sum(len(v) for v in encoded_by_res.values())
print(f'  Encoded {total_encoded} messages for {len(encoded_by_res)} resources')
print(f'  Skipped {skipped_identity} identity translations, {errors} errors')

# ---------------------------------------------------------------------------
# STEP 3 -- Inject font atlas into resource 1272
# ---------------------------------------------------------------------------
print()
print('STEP 3: Injecting font atlas ...')
os.makedirs('build/packdata_resources', exist_ok=True)

font_data = open('build/english_font_atlas.bin', 'rb').read()
raw_1272 = glob.glob('extracted/packdata_raw/1272_type*.raw')[0]
orig_1272 = open(raw_1272, 'rb').read()

# Preserve original sub-header fields except payload_size
h0 = struct.unpack_from('<I', orig_1272, 0)[0]
h2 = struct.unpack_from('<I', orig_1272, 8)[0]
h3 = struct.unpack_from('<I', orig_1272, 12)[0]
new_sub = struct.pack('<IIII', h0, len(font_data), h2, h3)
new_1272 = new_sub + font_data
sc = math.ceil(len(new_1272) / SECTOR)
new_1272 += b'\x00' * (sc * SECTOR - len(new_1272))
out_name = os.path.basename(raw_1272)
open(f'build/packdata_resources/{out_name}', 'wb').write(new_1272)
print(f'  Font atlas -> {out_name} ({len(new_1272)} bytes, {sc} sectors)')

# ---------------------------------------------------------------------------
# STEP 3b -- Patch R1188 kanji atlas (name-entry labels + stat labels)
# ---------------------------------------------------------------------------
print()
print('STEP 3b: Patching R1188 kanji atlas ...')
# First: name-entry tab labels (Kana/Hira/ABC/Sym/OK etc.)
os.system('python tools/patch_r1188_direct.py')
# Second: stat labels (STR/INT/PIE/VIT/AGI/LCK) -- stacks on top of direct patch
os.system('python tools/patch_r1188_stats.py')
print('  R1188 patched (tab labels + stat labels)')


# ---------------------------------------------------------------------------
# STEP 4 -- Inject translations into MSG resources
# ---------------------------------------------------------------------------
print()
print('STEP 4: Injecting translations into MSG resources ...')


def count_sequential_table(data, start=16):
    """Count sequential-ID table entries (LE u32 ids: 1, 2, 3, ...) at start."""
    if len(data) < start + 16:
        return 0
    first = struct.unpack_from('<I', data, start)[0]
    if first != 1:
        return 0
    count = 0
    for e in range(min(256, (len(data) - start) // 16)):
        eid = struct.unpack_from('<I', data, start + e * 16)[0]
        if eid == e + 1:
            count = e + 1
        else:
            break
    return count


def parse_offset_table(data, table_start):
    """
    Parse a Format-A offset table starting at table_start.

    Format:
        entry[0]:  (BE u16 message_count, BE u16 0x0000)
        entry[1]:  (BE u16 offset_to_msg0,  BE u16 0x0000)
        ...
        entry[N]:  (BE u16 offset_to_msgN-1, BE u16 0xFFFF)   <-- last entry

    Returns (msg_count, list_of_offsets, table_byte_size) or None if not valid.
    """
    if table_start + 4 > len(data):
        return None

    first_val = struct.unpack_from('>H', data, table_start)[0]
    first_flags = struct.unpack_from('>H', data, table_start + 2)[0]

    # Heuristic: first entry should be (count, 0x0000) with count in [1..500]
    if first_flags != 0x0000 or first_val < 1 or first_val > 500:
        return None

    msg_count = first_val
    offsets = []
    i = table_start + 4   # skip count entry
    for e in range(msg_count):
        if i + 4 > len(data):
            return None
        val = struct.unpack_from('>H', data, i)[0]
        flags = struct.unpack_from('>H', data, i + 2)[0]
        offsets.append(val)
        i += 4
        if flags == 0xFFFF:
            # This was the last entry
            break

    table_size = i - table_start
    return (msg_count, offsets, table_size)


def parse_ffff_groups(data, stream_start, stream_end):
    """
    Parse the glyph stream into FFFF-delimited groups.
    Each group can contain internal FFFE line breaks.

    Returns list of (start_offset, end_offset) for each FFFF-terminated group.
    """
    groups = []
    grp_start = stream_start
    off = stream_start
    while off < stream_end - 1:
        val = struct.unpack_from('>H', data, off)[0]
        if val == 0xFFFF:
            groups.append((grp_start, off))
            grp_start = off + 2
        off += 2
    # Catch trailing data after last FFFF
    if grp_start < stream_end:
        groups.append((grp_start, stream_end))
    return groups


def rebuild_offset_table(msg_count, ffff_group_byte_offsets, has_trailing_ffff_flag=True):
    """
    Rebuild a Format-A offset table.

    msg_count:   number declared in entry[0]
    ffff_group_byte_offsets:  list of byte offsets (relative to payload start)
                              for each FFFF-delimited message group.
    has_trailing_ffff_flag:   if True, the last offset entry gets flags=0xFFFF.

    Returns bytes for the complete offset table.
    """
    buf = bytearray()
    # Entry 0: (count, 0x0000)
    buf += struct.pack('>HH', msg_count, 0x0000)
    # Entries 1..N: (offset, flags)
    for i, off in enumerate(ffff_group_byte_offsets):
        is_last = (i == len(ffff_group_byte_offsets) - 1)
        flags = 0xFFFF if (is_last and has_trailing_ffff_flag) else 0x0000
        buf += struct.pack('>HH', off, flags)
    return bytes(buf)


def inject_resource(res_idx, msg_trans):
    """
    Inject translated messages into a single resource file.

    msg_trans: dict { message_index: [glyph_list] }
    Message indices match the FFFF-group numbering from full_decoded_text.txt.
    These are typically 1-indexed (group 0 is often a control/empty group).
    The internal " / " separators in translations have already been converted
    to 0xFFFE tokens by clean_and_encode().

    Returns (output_filename, status_string) or (None, error_string).
    """
    raws = glob.glob(f'extracted/packdata_raw/{res_idx:04d}_type*.raw')
    if not raws:
        return (None, f'raw file not found')

    raw_path = raws[0]
    rfn = os.path.basename(raw_path)
    raw = bytearray(open(raw_path, 'rb').read())

    if len(raw) < 32:
        return (None, f'file too small ({len(raw)} bytes)')

    # Parse sub-header
    h_zero1, h_payload_size, h_stride, h_zero2 = struct.unpack_from('<IIII', raw, 0)
    payload_end = 16 + h_payload_size
    extra_data = bytes(raw[payload_end:])   # data beyond payload -- MUST preserve!

    # Detect sequential table
    seq_count = count_sequential_table(raw, 16)
    seq_data = bytes(raw[16: 16 + seq_count * 16])
    after_seq = 16 + seq_count * 16

    # Try to parse offset table (Format A)
    ot_result = parse_offset_table(raw, after_seq)
    has_offset_table = ot_result is not None

    if has_offset_table:
        ot_msg_count, ot_offsets, ot_table_size = ot_result
        stream_start = after_seq + ot_table_size
    else:
        # No offset table -- find stream start by scanning for first FFFF
        stream_start = None
        for off in range(after_seq, min(len(raw) - 1, payload_end), 2):
            val = struct.unpack_from('>H', raw, off)[0]
            if val == 0xFFFF:
                stream_start = off
                break
        if stream_start is None:
            return (None, f'no glyph stream found')

    # Parse FFFF-delimited groups (this is the message numbering the translations use)
    stream_end = payload_end
    ffff_groups = parse_ffff_groups(raw, stream_start, stream_end)

    # Also parse FFFF groups in extra data (beyond payload) for resources like R34
    # that store most of their messages in the extra region.
    extra_ffff_groups = []
    if extra_data and len(extra_data) > 2:
        extra_ffff_groups = parse_ffff_groups(bytearray(extra_data), 0, len(extra_data))

    # Check if any translations target the extra data region
    payload_group_count = len(ffff_groups)
    extra_replaced = 0
    has_extra_trans = any(gi >= payload_group_count for gi in msg_trans)

    # Rebuild the glyph stream, replacing translated FFFF groups
    replaced = 0
    new_stream = bytearray()
    for gi, (gs, ge) in enumerate(ffff_groups):
        if gi in msg_trans:
            # Replace entire FFFF group with English translation
            # (which already contains FFFE line breaks from clean_and_encode)
            for g in msg_trans[gi]:
                new_stream += struct.pack('>H', g)
            # Ensure trailing FFFE before FFFF -- the original format requires
            # every group to end with FFFE FFFF. clean_and_encode() strips
            # trailing FFFE, so we must restore it here.
            if not msg_trans[gi] or msg_trans[gi][-1] != 0xFFFE:
                new_stream += struct.pack('>H', 0xFFFE)
            replaced += 1
        else:
            # Keep original group content (including internal FFFE markers)
            new_stream += raw[gs:ge]
        # Always terminate group with FFFF
        new_stream += struct.pack('>H', 0xFFFF)

    # If there are translations for the extra data region, rebuild it too
    if has_extra_trans and extra_ffff_groups:
        extra_data_buf = bytearray(extra_data)
        new_extra = bytearray()
        for egi, (egs, ege) in enumerate(extra_ffff_groups):
            global_idx = payload_group_count + egi
            if global_idx in msg_trans:
                for g in msg_trans[global_idx]:
                    new_extra += struct.pack('>H', g)
                # Ensure trailing FFFE before FFFF (same invariant as payload groups)
                if not msg_trans[global_idx] or msg_trans[global_idx][-1] != 0xFFFE:
                    new_extra += struct.pack('>H', 0xFFFE)
                extra_replaced += 1
            else:
                new_extra += extra_data_buf[egs:ege]
            new_extra += struct.pack('>H', 0xFFFF)
        extra_data = bytes(new_extra)
        replaced += extra_replaced

    # Rebuild offset table if present
    if has_offset_table:
        # Find byte positions of each FFFF group start in the new stream
        new_ffff_positions = []
        pos = 0
        grp_start_pos = 0
        in_first = True
        while pos < len(new_stream) - 1:
            if in_first:
                new_ffff_positions.append(grp_start_pos)
                in_first = False
            val = struct.unpack_from('>H', new_stream, pos)[0]
            if val == 0xFFFF:
                grp_start_pos = pos + 2
                in_first = True
            pos += 2

        # Compute new offset table size
        new_msg_count = len(new_ffff_positions)
        new_ot_size = (new_msg_count + 1) * 4

        seq_size = len(seq_data)
        glyph_stream_base = seq_size + new_ot_size

        # Convert group-local byte offsets to payload-relative offsets
        payload_rel_offsets = [glyph_stream_base + goff for goff in new_ffff_positions]

        new_ot_bytes = rebuild_offset_table(new_msg_count, payload_rel_offsets, True)

        # Assemble new payload
        new_payload = seq_data + new_ot_bytes + bytes(new_stream)
    else:
        # No offset table: payload = seq_data + pre-stream data + new_stream
        pre_stream_data = bytes(raw[after_seq:stream_start])
        new_payload = seq_data + pre_stream_data + bytes(new_stream)

    # Build new sub-header
    new_payload_size = len(new_payload)
    new_sub_header = struct.pack('<IIII', h_zero1, new_payload_size, h_stride, h_zero2)

    # Assemble full block: sub-header + payload + extra data (beyond payload)
    block = new_sub_header + new_payload + extra_data
    sc = math.ceil(len(block) / SECTOR)
    block += b'\x00' * (sc * SECTOR - len(block))

    # Write
    out_path = f'build/packdata_resources/{rfn}'
    open(out_path, 'wb').write(block)

    old_sc = len(raw) // SECTOR
    total_groups = len(ffff_groups) + len(extra_ffff_groups)
    extra_info = f', extra_replaced={extra_replaced}' if extra_replaced else ''
    ot_info = 'none'
    if has_offset_table:
        ot_info = f'rebuilt (orig={ot_msg_count}, new={new_msg_count})'
        if ot_msg_count != new_msg_count:
            ot_info += ' *** COUNT CHANGED ***'
    return (rfn, f'replaced {replaced}/{total_groups} groups, '
                 f'{old_sc}->{sc} sectors, '
                 f'payload {h_payload_size}->{new_payload_size}, '
                 f'offset_table={ot_info}, '
                 f'extra_data={len(extra_data)}{extra_info}')


def fixup_r37_inplace(raw_path, translations):
    """Build R37 by patching the ORIGINAL binary in-place.

    The game reads keyboard data from FIXED byte offsets in R37, NOT the offset
    table. The v2 pipeline's rebuild changes message sizes, shifting keyboard
    groups to wrong positions. Fix: start from original R37, replace each
    message's content in-place (truncate/pad to fit original size).

    CRITICAL: Keyboard groups 17-20 contain special marker glyphs at the END of
    each group: 0x0206 (male name button) and 0x015D (female name button). These
    markers occupy rows 7-9 of the 10-row keyboard grid. When the English
    replacement is shorter than the Japanese original, we must PRESERVE the
    original trailing bytes (which contain these markers) rather than zero-pad.
    Zero-padding destroys the markers, breaking random name generation buttons.
    """
    # Read ORIGINAL R37 from PACKDATA.DIG
    with open('extracted/PACKDATA.DIG', 'rb') as f:
        toc = f.read(2883 * 12)
        r37_so, r37_sc, _ = struct.unpack_from('<III', toc, 37 * 12)
        f.seek(r37_so * SECTOR)
        orig = bytearray(f.read(r37_sc * SECTOR))

    # Parse structure: 16-byte sub-header + offset table + glyph stream
    msg_count = struct.unpack_from('>H', orig, 16)[0]
    ot_start = 20  # first offset entry

    # Find each FFFF group's byte range
    groups = []
    for gi in range(msg_count):
        off = struct.unpack_from('>H', orig, ot_start + gi * 4)[0]
        start = 16 + off
        # Find the FFFF terminator
        pos = start
        while pos < len(orig) - 1:
            if struct.unpack_from('>H', orig, pos)[0] == 0xFFFF:
                break
            pos += 2
        groups.append((start, pos))  # (data_start, ffff_pos)

    # Keyboard groups (17-20): replace 0x0206/0x015D markers with 0x01FF
    # (page 1, index 255 — out of bounds = invisible). The original markers
    # render as visible 男/女 kanji (cell data sprites). Zero (0x0000) breaks
    # name buttons because page-0 glyphs fail the grid validity check.
    # Page-1 glyphs pass validity, and an out-of-bounds index renders nothing.
    # The ♂/♀ symbols come from the Layer 1 background sprite.
    #
    # Also record FFFE row-separator positions. The English content only fills
    # rows 0-5 (6 FFFEs). Rows 6-9 are in the zero-padded gap and need their
    # FFFE separators restored so the 10×10 grid structure is intact. Without
    # these FFFEs the cursor can't navigate from the male marker row to the
    # female marker row.
    KEYBOARD_GROUPS = {17, 18, 19, 20}
    # Markers are zero-padded (0x0000 = space = invisible). EXE Patch 10
    # changes the page validity table so page-0 glyphs pass the cursor
    # check, allowing the cursor to reach zero-padded button positions.
    # The name generation function is triggered by grid position (function
    # pointer table), not by glyph value.
    fffe_positions = {}  # gi -> [byte positions of FFFE separators]
    for gi in KEYBOARD_GROUPS:
        if gi >= len(groups):
            continue
        data_start, ffff_pos = groups[gi]
        f_positions = []
        for pos in range(data_start, ffff_pos, 2):
            if struct.unpack_from('>H', orig, pos)[0] == 0xFFFE:
                f_positions.append(pos)
        if f_positions:
            fffe_positions[gi] = f_positions

    replaced = 0
    remapped_names = 0
    for gi, glyphs in translations.items():
        # Remap uppercase glyph IDs in name groups (21+) to avoid keyboard
        # font metrics pollution. Uppercase A-Z (33-58) → 95-120. The chargen
        # atlas (R2100) and font metrics (R1369) are patched to support 95-120
        # with duplicate A-Z bitmaps and metrics.
        if gi >= 21 and gi != 123:
            remapped = []
            did_remap = False
            for g in glyphs:
                if 33 <= g <= 58:  # uppercase A-Z
                    remapped.append(g - 33 + 95)  # remap to 95-120
                    did_remap = True
                else:
                    remapped.append(g)
            glyphs = remapped
            if did_remap:
                remapped_names += 1
        if gi >= len(groups):
            continue
        data_start, ffff_pos = groups[gi]
        orig_data_size = ffff_pos - data_start  # bytes of glyph data (before FFFF)

        # Encode new glyphs as BE u16
        new_data = bytearray()
        for g in glyphs:
            new_data += struct.pack('>H', g)
        # Ensure trailing FFFE for instruction text groups (0-16) only.
        # Keyboard groups (17-20): original FFFEs in the gap provide row structure.
        # Name groups (21+): FFFE wastes 2 bytes, causing truncation of ~30 names
        # ("Eddie"→"Eddi") and a trailing 0x0000 glyph that renders as Japanese.
        if gi <= 16:
            if not glyphs or glyphs[-1] != 0xFFFE:
                new_data += struct.pack('>H', 0xFFFE)

        if len(new_data) <= orig_data_size:
            # Fits: write new data at the start of the group
            orig[data_start:data_start + len(new_data)] = new_data

            # Zero-pad the remainder, then restore FFFE row separators
            for i in range(data_start + len(new_data), ffff_pos):
                orig[i] = 0
            # Restore FFFE row separators that fell in the zero-padded gap.
            # Without these, the keyboard grid loses row boundaries and the
            # cursor can't navigate between marker rows (male/female).
            if gi in fffe_positions:
                for pos in fffe_positions[gi]:
                    if pos >= data_start + len(new_data):
                        struct.pack_into('>H', orig, pos, 0xFFFE)

            replaced += 1
        else:
            # Truncate to fit (lose trailing content)
            orig[data_start:ffff_pos] = new_data[:orig_data_size]
            replaced += 1

    # --- Second pass: relocate truncated instruction groups 0-16 to free space ---
    # Find the last non-zero byte to determine where free space starts
    resource_size = 4096  # 2 sectors
    free_ptr = resource_size
    while free_ptr > 0 and orig[free_ptr - 1] == 0:
        free_ptr -= 1
    # Align free_ptr to next 2-byte boundary
    if free_ptr % 2 != 0:
        free_ptr += 1

    relocated = 0
    for gi in range(min(17, len(groups))):
        if gi not in translations:
            continue
        glyphs = translations[gi]
        data_start, ffff_pos = groups[gi]
        orig_data_size = ffff_pos - data_start

        # Encode new glyphs as BE u16
        new_data = bytearray()
        for g in glyphs:
            new_data += struct.pack('>H', g)
        # Ensure trailing FFFE
        if not glyphs or glyphs[-1] != 0xFFFE:
            new_data += struct.pack('>H', 0xFFFE)

        if len(new_data) <= orig_data_size:
            continue  # Already fits in-place, no relocation needed

        # Need relocation: new_data + FFFF terminator
        needed = len(new_data) + 2  # +2 for FFFF terminator
        if free_ptr + needed > resource_size:
            print(f'  WARNING: R37 group {gi} relocation failed — no space '
                  f'(need {needed} bytes, have {resource_size - free_ptr})')
            continue

        # Write full content at free_ptr
        orig[free_ptr:free_ptr + len(new_data)] = new_data
        struct.pack_into('>H', orig, free_ptr + len(new_data), 0xFFFF)

        # Update offset table: payload-relative offset (relative to byte 16)
        new_offset = free_ptr - 16
        struct.pack_into('>H', orig, ot_start + gi * 4, new_offset)

        print(f'  R37 group {gi}: relocated to 0x{free_ptr:04X} '
              f'(offset 0x{new_offset:04X}, {len(new_data)} bytes data)')

        free_ptr += needed
        relocated += 1

    # Write
    out_sc = math.ceil(len(orig) / SECTOR)
    orig += b'\x00' * (out_sc * SECTOR - len(orig))
    open(raw_path, 'wb').write(orig)
    print(f'  R37 in-place patch: {replaced}/{len(translations)} messages, {len(orig)} bytes')
    if relocated:
        print(f'  R37 relocated {relocated} overflowing instruction groups to free space')
    print(f'  Keyboard groups preserved at original byte offsets')
    if remapped_names:
        print(f'  Remapped uppercase A-Z (33-58 -> 95-120) in {remapped_names} name groups')


modified = 0
# R34 (type-20) has a multi-sub header (20 entries x 16 bytes = 320 bytes).
# inject_resource() misinterprets this as a standard sub-header, causing
# sub 0's expanded payload to overflow into sub 1 -> data corruption.
# R34 is handled in Step 2 of build_v9.py instead.
# Resources with non-text binary data that happens to contain 0xFFFF patterns.
# The v2 pipeline would misinterpret these as text group terminators and inject
# translations over VIF/DMA commands, causing VIF FIFO crashes.
SKIP_V2_PIPELINE = {34, 2124}

for res_idx in sorted(encoded_by_res.keys()):
    if res_idx in SKIP_V2_PIPELINE:
        print(f'  R{res_idx:04d}: SKIPPED -- multi-sub header, handled in Step 2')
        continue
    msg_trans = encoded_by_res[res_idx]
    rfn, status = inject_resource(res_idx, msg_trans)
    if rfn:
        print(f'  R{res_idx:04d} ({rfn}): {status}')
        modified += 1
    else:
        print(f'  R{res_idx:04d}: SKIPPED -- {status}')

print(f'  Modified {modified} resources')

# R37 special handling: patch original binary in-place instead of rebuilding.
# The game reads keyboard data from FIXED byte offsets in R37, NOT the offset
# table. The v2 pipeline's rebuild shifts message positions, breaking keyboard
# rendering. Fix: start from original R37, patch in-place.
#
# Font metrics pollution (F/M invisible) is fixed by EXE Patch 9 which forces
# non-zero metrics for glyphs F(38) and M(45) in the keyboard atlas builder.
# All groups can now be safely translated with original glyph IDs.
r37_path = 'build/packdata_resources/0037_type01.raw'
if 37 in encoded_by_res:
    r37_all = encoded_by_res[37]
    print(f'\n  R37: In-place patching ALL {len(r37_all)} groups (EXE Patch 9 prevents F/M pollution)...')
    fixup_r37_inplace(r37_path, r37_all)

# ---------------------------------------------------------------------------
# STEP 5 -- Rebuild PACKDATA.DIG
# ---------------------------------------------------------------------------
print()
print('STEP 5: Rebuilding PACKDATA.DIG ...')

manifest = json.load(open('extracted/packdata_resources/manifest.json', encoding='utf-8'))
orig_packdata = 'extracted/PACKDATA.DIG'

# Read original TOC (2883 entries * 12 bytes = first 125 sectors)
with open(orig_packdata, 'rb') as f:
    otoc = [struct.unpack('<III', f.read(12)) for _ in range(2883)]
    f.seek(0)
    hdr = f.read(125 * SECTOR)

orig_size = os.path.getsize(orig_packdata)

with open('build/PACKDATA.DIG', 'wb') as out:
    out.write(hdr)
    cs = 125  # current sector (data starts after TOC)
    ntoc = []

    for entry in manifest:
        idx = entry['index']

        if entry.get('skipped'):
            ntoc.append(otoc[idx])
            continue

        tc = entry['type_code']
        fn = f'{idx:04d}_type{tc:02d}.raw'
        mp = f'build/packdata_resources/{fn}'
        rp = f'extracted/packdata_raw/{fn}'

        if os.path.exists(mp):
            d = open(mp, 'rb').read()
        elif os.path.exists(rp):
            d = open(rp, 'rb').read()
        else:
            cc = glob.glob(f'extracted/packdata_raw/{idx:04d}_type*.raw')
            d = open(cc[0], 'rb').read() if cc else b'\x00' * SECTOR

        sc = math.ceil(len(d) / SECTOR)
        if len(d) < sc * SECTOR:
            d += b'\x00' * (sc * SECTOR - len(d))

        out.seek(cs * SECTOR)
        out.write(d)
        ntoc.append((cs, sc, tc))
        cs += sc

    # Write new TOC
    out.seek(0)
    for so, sc, tc in ntoc:
        out.write(struct.pack('<III', so, sc, tc))

    out.seek(0, 2)
    fs = out.tell()

print(f'  Size: {fs:,} bytes  (orig: {orig_size:,}, diff: {fs - orig_size:+,})')

# Pad to original size for ISO replacement
if fs < orig_size:
    with open('build/PACKDATA.DIG', 'ab') as f:
        f.write(b'\x00' * (orig_size - fs))
    fs = orig_size
    print(f'  Padded to {fs:,} bytes')
elif fs > orig_size:
    print(f'  WARNING: new PACKDATA.DIG is {fs - orig_size:,} bytes LARGER than original!')
    print(f'  This will NOT fit in the original ISO extent. Truncating is NOT safe.')
    print(f'  The ISO build step will proceed but the result may be corrupt.')

# ---------------------------------------------------------------------------
# STEP 6 -- Build ISO via direct binary replacement
# ---------------------------------------------------------------------------
print()
print('STEP 6: Building ISO ...')

ISO_PATH = 'Busin 0 - Wizardry Alternative Neo (Japan) (v2.01).iso'
OUTPUT_ISO = 'build/BUSIN0_EN.iso'

if not os.path.exists(ISO_PATH):
    print(f'  ERROR: Source ISO not found: {ISO_PATH}')
    print(f'  Skipping ISO build.  PACKDATA.DIG is ready at build/PACKDATA.DIG')
else:
    # Find PACKDATA.DIG extent in ISO by parsing primary volume descriptor
    with open(ISO_PATH, 'rb') as f:
        f.seek(16 * 2048)
        pvd = f.read(2048)
        root_rec = pvd[156:156 + 34]
        root_extent = struct.unpack_from('<I', root_rec, 2)[0]
        root_size = struct.unpack_from('<I', root_rec, 10)[0]
        f.seek(root_extent * 2048)
        root_data = f.read(root_size)

    packdata_extent = None
    pos = 0
    while pos < len(root_data):
        rec_len = root_data[pos]
        if rec_len == 0:
            break
        name_len = root_data[pos + 32]
        name = root_data[pos + 33: pos + 33 + name_len]
        if b'PACKDATA' in name:
            packdata_extent = struct.unpack_from('<I', root_data, pos + 2)[0]
            break
        pos += rec_len

    if packdata_extent is None:
        print(f'  ERROR: Could not find PACKDATA.DIG in ISO directory')
    else:
        print(f'  PACKDATA.DIG at ISO sector {packdata_extent} (byte offset {packdata_extent * 2048:,})')

        shutil.copy2(ISO_PATH, OUTPUT_ISO)

        with open(OUTPUT_ISO, 'r+b') as iso_f:
            iso_f.seek(packdata_extent * 2048)
            with open('build/PACKDATA.DIG', 'rb') as pd:
                while True:
                    chunk = pd.read(4 * 1024 * 1024)
                    if not chunk:
                        break
                    iso_f.write(chunk)

        print(f'  ISO written: {OUTPUT_ISO}')
        print(f'  Size: {os.path.getsize(OUTPUT_ISO):,} bytes')

        # --- Patch EXE into ISO ---
        print()
        print('STEP 6b: Patching EXE ...')
        os.system('python build/patch_exe.py')
        exe_path = 'build/SLPM_653.78_patched'
        if os.path.exists(exe_path):
            exe_data = open(exe_path, 'rb').read()
            # Find SLPM EXE extent in root directory
            exe_extent = None
            pos2 = 0
            while pos2 < len(root_data):
                rec_len2 = root_data[pos2]
                if rec_len2 == 0:
                    break
                name_len2 = root_data[pos2 + 32]
                name2 = root_data[pos2 + 33: pos2 + 33 + name_len2]
                if b'SLPM' in name2:
                    exe_extent = struct.unpack_from('<I', root_data, pos2 + 2)[0]
                    # Update file size in directory record (both LE and BE)
                    with open(OUTPUT_ISO, 'r+b') as iso_f:
                        iso_f.seek(root_extent * SECTOR + pos2 + 10)
                        iso_f.write(struct.pack('<I', len(exe_data)))
                        iso_f.write(struct.pack('>I', len(exe_data)))
                        # Write patched EXE data
                        iso_f.seek(exe_extent * SECTOR)
                        iso_f.write(exe_data)
                    print(f'  EXE patched: {len(exe_data):,} bytes at LBA {exe_extent}')
                    break
                pos2 += rec_len2
            if exe_extent is None:
                print(f'  WARNING: Could not find SLPM EXE in ISO directory')
        else:
            print(f'  No patched EXE found, skipping')

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
print()
print('=' * 60)
print(f'  BUILD COMPLETE')
print(f'  {total_encoded} messages encoded across {len(encoded_by_res)} resources')
print(f'  {modified} resource files modified')
print(f'  PACKDATA.DIG: build/PACKDATA.DIG')
if os.path.exists(OUTPUT_ISO):
    print(f'  ISO: {OUTPUT_ISO}')
print('=' * 60)
