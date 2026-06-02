#!/usr/bin/env python3
"""
Verify R38 and R39 build outputs for structural integrity.

R38 checks (type-01, Format A):
  - Offset table count matches FFFF group count
  - Each offset table entry points to a valid group start
  - All FFFF groups are properly delimited

R39 checks (type-15):
  - Stat label offsets (0x56D6-0x57BC) contain ASCII glyph IDs, not kanji
  - FFFF delimiter counts are preserved vs original
"""

import struct
import sys
import os

BASE = 'C:/Programmieren/wizardrytranslation'
os.chdir(BASE)

errors = []
warnings = []


def check(condition, msg):
    if not condition:
        errors.append(msg)
        print(f"  FAIL: {msg}")
        return False
    else:
        print(f"  OK: {msg}")
        return True


# ============================================================================
# R38 verification
# ============================================================================
print("=" * 60)
print("R38 (build/packdata_resources/0038_type01.raw)")
print("=" * 60)

r38_path = 'build/packdata_resources/0038_type01.raw'
if not os.path.exists(r38_path):
    errors.append("R38 file not found")
    print("  FAIL: R38 file not found")
else:
    data = open(r38_path, 'rb').read()
    print(f"  File size: {len(data)} bytes")

    # Parse sub-header (LE32 x4)
    h_zero1, h_payload_size, h_stride, h_zero2 = struct.unpack_from('<IIII', data, 0)
    payload_end = 16 + h_payload_size
    print(f"  Payload size: {h_payload_size} (0x{h_payload_size:X}), ends at {payload_end}")

    # Detect sequential table (entries of 16 bytes with sequential LE32 IDs: 1, 2, 3, ...)
    seq_count = 0
    if len(data) >= 32:
        first_id = struct.unpack_from('<I', data, 16)[0]
        if first_id == 1:
            for e in range(min(256, (len(data) - 16) // 16)):
                eid = struct.unpack_from('<I', data, 16 + e * 16)[0]
                if eid == e + 1:
                    seq_count = e + 1
                else:
                    break
    seq_size = seq_count * 16
    after_seq = 16 + seq_size
    print(f"  Sequential table: {seq_count} entries ({seq_size} bytes)")

    # Parse offset table at after_seq (Format A: BE16 pairs)
    ot_start = after_seq
    msg_count = struct.unpack_from('>H', data, ot_start)[0]
    first_flags = struct.unpack_from('>H', data, ot_start + 2)[0]
    check(first_flags == 0x0000, f"Offset table header flags = 0x{first_flags:04X} (expected 0x0000)")
    check(1 <= msg_count <= 500, f"Message count = {msg_count} (in valid range 1-500)")

    # Read offset entries
    offsets = []
    pos = ot_start + 4
    last_entry_flags = None
    for i in range(msg_count):
        val = struct.unpack_from('>H', data, pos)[0]
        flags = struct.unpack_from('>H', data, pos + 2)[0]
        offsets.append(val)
        last_entry_flags = flags
        pos += 4
        if flags == 0xFFFF:
            break

    ot_size = pos - ot_start
    stream_start = ot_start + ot_size
    print(f"  Offset table: {len(offsets)} entries, {ot_size} bytes, stream starts at {stream_start}")

    check(last_entry_flags == 0xFFFF,
          f"Last OT entry has trailing 0xFFFF flag (got 0x{last_entry_flags:04X})")

    # Parse FFFF-delimited groups in payload
    ffff_groups = []
    grp_start = stream_start
    off = stream_start
    while off < payload_end - 1:
        val = struct.unpack_from('>H', data, off)[0]
        if val == 0xFFFF:
            ffff_groups.append((grp_start, off))
            grp_start = off + 2
        off += 2

    print(f"  FFFF groups in payload: {len(ffff_groups)}")

    check(len(offsets) == len(ffff_groups),
          f"OT entry count ({len(offsets)}) matches FFFF group count ({len(ffff_groups)})")

    # Verify each OT entry points to a valid group start
    # OT offsets are payload-relative (relative to byte 16), so they include
    # seq_data size + OT size as a prefix before the glyph stream.
    ot_valid = 0
    for i, (ot_off, (grp_start_abs, grp_end_abs)) in enumerate(zip(offsets, ffff_groups)):
        # payload-relative offset: subtract the 16-byte header from absolute position
        expected_payload_rel = grp_start_abs - 16
        if ot_off == expected_payload_rel:
            ot_valid += 1
        else:
            if len(errors) < 20:  # cap error spam
                errors.append(
                    f"OT[{i}] offset 0x{ot_off:04X} != expected 0x{expected_payload_rel:04X}")

    check(ot_valid == len(offsets),
          f"All {ot_valid}/{len(offsets)} OT entries point to correct group starts")

    # Verify no empty groups (each group should have at least 1 glyph word)
    empty_groups = [i for i, (s, e) in enumerate(ffff_groups) if e <= s]
    if empty_groups:
        warnings.append(f"R38 has {len(empty_groups)} empty FFFF groups: {empty_groups[:10]}")
        print(f"  WARN: {len(empty_groups)} empty FFFF groups")


# ============================================================================
# R39 verification
# ============================================================================
print()
print("=" * 60)
print("R39 (build/packdata_resources/0039_type15.raw)")
print("=" * 60)

r39_path = 'build/packdata_resources/0039_type15.raw'
if not os.path.exists(r39_path):
    errors.append("R39 file not found")
    print("  FAIL: R39 file not found")
else:
    data = open(r39_path, 'rb').read()
    print(f"  File size: {len(data)} bytes")

    # Stat label glyph patches: these offsets should contain ASCII-range glyph IDs
    # ASCII glyphs: 0 (space/null) through ~94 (tilde). Kanji IDs are typically > 200.
    STAT_LABEL_PATCHES = {
        "ST (STR)": [
            (0x56D6, 51),  # S
            (0x56D8, 52),  # T
        ],
        "INT": [
            (0x5700, 41),  # I
            (0x5702, 46),  # N
            (0x5704, 52),  # T
        ],
        "PIE": [
            (0x572C, 48),  # P
            (0x572E, 41),  # I
            (0x5730, 37),  # E
            (0x5732, 0),   # null padding
        ],
        "VIT": [
            (0x575A, 54),  # V
            (0x575C, 41),  # I
            (0x575E, 52),  # T
            (0x5760, 0),   # null padding
        ],
        "AGI": [
            (0x5788, 33),  # A
            (0x578A, 39),  # G
            (0x578C, 41),  # I
            (0x578E, 0),   # null padding
        ],
        "LCK": [
            (0x57B6, 44),  # L
            (0x57B8, 35),  # C
            (0x57BA, 43),  # K
            (0x57BC, 0),   # null padding
        ],
    }

    MAX_ASCII_GLYPH = 94  # printable ASCII range in glyph table

    all_stat_ok = True
    for label, patches in STAT_LABEL_PATCHES.items():
        for byte_offset, expected_glyph in patches:
            if byte_offset + 1 >= len(data):
                errors.append(f"R39 stat patch offset 0x{byte_offset:04X} out of range")
                all_stat_ok = False
                continue
            actual = struct.unpack_from('>H', data, byte_offset)[0]
            if actual != expected_glyph:
                errors.append(
                    f"R39 {label} @ 0x{byte_offset:04X}: expected glyph {expected_glyph}, got {actual}")
                all_stat_ok = False
            elif actual > MAX_ASCII_GLYPH and actual != 0:
                errors.append(
                    f"R39 {label} @ 0x{byte_offset:04X}: glyph {actual} is kanji-range (>94)")
                all_stat_ok = False

    check(all_stat_ok, "All stat label glyphs are correct ASCII-range values")

    # Count FFFF delimiters in the file
    ffff_count = 0
    for i in range(0, len(data) - 1, 2):
        val = struct.unpack_from('>H', data, i)[0]
        if val == 0xFFFF:
            ffff_count += 1

    check(ffff_count > 0, f"R39 contains {ffff_count} FFFF delimiters")

    # Compare against original if available
    orig_path = 'extracted/packdata_raw/0039_type15.raw'
    if os.path.exists(orig_path):
        orig = open(orig_path, 'rb').read()
        orig_ffff = 0
        for i in range(0, len(orig) - 1, 2):
            val = struct.unpack_from('>H', orig, i)[0]
            if val == 0xFFFF:
                orig_ffff += 1
        check(ffff_count == orig_ffff,
              f"FFFF count preserved: build={ffff_count} vs original={orig_ffff}")
    else:
        print(f"  SKIP: Original R39 not found at {orig_path}, cannot compare FFFF counts")


# ============================================================================
# Summary
# ============================================================================
print()
print("=" * 60)
if errors:
    print(f"FAILED: {len(errors)} error(s)")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)
else:
    print("ALL CHECKS PASSED")
    if warnings:
        for w in warnings:
            print(f"  WARN: {w}")
    sys.exit(0)
