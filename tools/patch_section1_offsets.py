#!/usr/bin/env python3
"""
patch_section1_offsets.py -- Patch Section 1 glyph offsets after variable-size Section 2 injection
==================================================================================================

When English translations are injected into Section 2 of type-02 resources, messages
can grow or shrink. Section 1 contains event script opcodes that reference Section 2
by word offset (glyph index). After injection, these offsets become stale and must be
updated to match the new Section 2 layout.

Opcodes that reference Section 2:
  0x0004  DISPLAY_TEXT:    0004 0000 GLYPH_OFF 0000 GLYPH_COUNT  (5 words)
  0x000C  SET_NAME_REF:    000C PARAM GLYPH_IDX                  (3 words)
  0x000D  CLEAR_NAME_REF:  000D PARAM GLYPH_IDX                  (3 words)

Strategy:
  1. Parse ORIGINAL Section 2 into FFFF-delimited groups, recording each group's
     word-start offset.
  2. Parse NEW (injected) Section 2 the same way.
  3. Build a word-level remapping: for each word position in the old Section 2,
     find which group it belongs to and its offset within that group, then compute
     the corresponding position in the new Section 2.
  4. Scan Section 1 for the three opcodes above and remap their glyph offsets/counts.
  5. Rewrite the patched file with updated Section 1 + new Section 2.

Usage:
    python tools/patch_section1_offsets.py <original.raw> <patched.raw> [output.raw]

    If output.raw is omitted, the patched file is overwritten in-place.

    Can also be called as a library:
        from patch_section1_offsets import patch_section1
        result = patch_section1(original_bytes, patched_bytes)
"""

import sys
import os
import struct
import math

SECTOR = 2048


def parse_sec2_group_offsets(sec2_data):
    """
    Parse Section 2 into FFFF-delimited groups and return their word-start offsets.

    Returns list of (group_start_word, group_end_word) tuples.
    group_end_word is the index of the FFFF terminator itself.
    The actual group content is words[group_start_word:group_end_word].
    """
    n_words = len(sec2_data) // 2
    groups = []
    start = 0
    for i in range(n_words):
        w = struct.unpack_from(">H", sec2_data, i * 2)[0]
        if w == 0xFFFF:
            groups.append((start, i))
            start = i + 1
    # Trailing data after last FFFF (shouldn't happen in well-formed data, but handle it)
    if start < n_words:
        groups.append((start, n_words))
    return groups


def build_word_remap(old_groups, new_groups):
    """
    Build a mapping from old word offset -> new word offset.

    For each word position in the old Section 2, we find:
      - Which group it belongs to (by index)
      - Its offset within that group
    Then map to the corresponding position in the new Section 2's same group.

    For FFFF terminators: the old FFFF at old_groups[i][1] maps to new_groups[i][1].

    Returns a dict {old_word_offset: new_word_offset}.
    Also returns a function for count remapping within a group span.
    """
    remap = {}
    n_groups = min(len(old_groups), len(new_groups))

    for gi in range(n_groups):
        old_start, old_end = old_groups[gi]
        new_start, new_end = new_groups[gi]
        old_len = old_end - old_start
        new_len = new_end - new_start

        # Map each word within the group
        for offset_in_group in range(old_len):
            old_pos = old_start + offset_in_group
            if offset_in_group < new_len:
                # Direct mapping: same offset within group
                remap[old_pos] = new_start + offset_in_group
            else:
                # Old group was longer; map to end of new group
                remap[old_pos] = new_end

        # Map the FFFF terminator
        remap[old_end] = new_end

    return remap


def find_group_for_offset(groups, word_offset):
    """Find which group index a word offset falls in (or at its FFFF terminator)."""
    for gi, (gs, ge) in enumerate(groups):
        if gs <= word_offset <= ge:  # <= ge to include the FFFF position
            return gi, word_offset - gs
    return None, None


def remap_glyph_offset(old_offset, old_groups, new_groups, is_display_text=False):
    """
    Remap a single glyph offset from old Section 2 to new Section 2.

    Handles offsets that fall at group starts, mid-group, or at FFFF terminators.

    For DISPLAY_TEXT mid-group starts (is_display_text=True):
      The skipped prefix was original-language text that no longer exists after
      injection. We remap to the new group's start so the full translated text
      is shown.

    For SET_NAME_REF / CLEAR_NAME_REF (is_display_text=False):
      We preserve the word-level offset within the group, since name references
      point to specific glyph positions that are preserved by the injector's
      control-code splitting.
    """
    gi, offset_in_group = find_group_for_offset(old_groups, old_offset)
    if gi is None:
        # Offset is outside all groups (sentinel value like 11264) -- leave unchanged
        return old_offset

    if gi >= len(new_groups):
        return old_offset

    old_start, old_end = old_groups[gi]
    new_start, new_end = new_groups[gi]
    old_len = old_end - old_start
    new_len = new_end - new_start

    if offset_in_group == old_len:
        # This is the FFFF terminator position
        return new_end

    if is_display_text and offset_in_group > 0:
        # Mid-group DISPLAY_TEXT start: the skipped prefix was original text
        # that has been replaced by injection. Remap to show the full new group.
        return new_start

    if offset_in_group < new_len:
        return new_start + offset_in_group
    else:
        # Offset was deep in old group, but new group is shorter
        return new_start + new_len - 1 if new_len > 0 else new_start


def remap_glyph_count(old_offset, old_count, old_groups, new_groups):
    """
    Remap a DISPLAY_TEXT glyph count.

    DISPLAY_TEXT references words[offset .. offset+count-1].  The exclusive end
    (offset + count) always lands on the word immediately AFTER a FFFF terminator
    (i.e., the start of the next group, or the end of Section 2).

    To remap: find the structural end-point in the old layout, locate the same
    structural point in the new layout, then new_count = new_end - new_start.

    Multi-group spans are supported: off=23 cnt=118 covers groups 1-3 inclusive
    (including the FFFF terminators between them).
    """
    if old_count == 0:
        return 0

    old_end = old_offset + old_count  # exclusive end in old section

    # Find which group the start offset falls in
    gi_start, _ = find_group_for_offset(old_groups, old_offset)
    if gi_start is None:
        return old_count  # sentinel, leave unchanged

    # The exclusive end (old_end) should be:
    #   - The start of the next group after the last spanned group, OR
    #   - Beyond the last group (end of Section 2)
    # Find the last group whose FFFF terminator is covered by the span:
    # old_end - 1 is the last word in the span. If it's a FFFF, it's a group terminator.
    gi_last, off_in_last = find_group_for_offset(old_groups, old_end - 1)
    if gi_last is None:
        return old_count

    # The exclusive end in the new layout is right after the FFFF of gi_last
    # which is new_groups[gi_last][1] + 1 (the FFFF is at new_groups[gi_last][1],
    # so the word after it is at position new_groups[gi_last][1] + 1)
    if gi_last >= len(new_groups):
        return old_count

    new_start = remap_glyph_offset(old_offset, old_groups, new_groups, is_display_text=True)

    # new_end = position after the FFFF terminator of the last group
    new_end = new_groups[gi_last][1] + 1

    new_count = new_end - new_start
    return max(new_count, 0)


# -- Opcode length table (words including the opcode itself) --
OPCODE_LENGTHS = {
    0x0003: 3,
    0x0004: 5,
    0x0006: 7,
    0x0007: 7,
    0x0008: 3,
    0x000B: 3,
    0x000C: 3,
    0x000D: 3,
    0x0010: 2,
    0x0012: 3,
    0x0016: 6,
    0x0017: 5,
    0x001A: 3,
    0x002B: 2,
}


def patch_section1(orig_data, patched_data):
    """
    Patch Section 1 glyph offsets in patched_data to match its (potentially resized)
    Section 2, using orig_data as the reference for old offsets.

    Returns the fully patched file as bytes.
    """
    if len(orig_data) < 0x1C or len(patched_data) < 0x1C:
        raise ValueError("Files too small to be type-02 resources")

    # Parse headers
    orig_sec2_size = struct.unpack_from("<I", orig_data, 0x14)[0]
    orig_sec2_off = struct.unpack_from("<I", orig_data, 0x18)[0]
    pat_sec2_size = struct.unpack_from("<I", patched_data, 0x14)[0]
    pat_sec2_off = struct.unpack_from("<I", patched_data, 0x18)[0]

    if orig_sec2_off != pat_sec2_off:
        raise ValueError(
            "Section 2 offset mismatch (orig=0x%x, patched=0x%x) -- "
            "Section 1 must be preserved byte-for-byte before this step"
            % (orig_sec2_off, pat_sec2_off)
        )

    sec2_off = orig_sec2_off
    header_size = 28  # 0x1C

    # Extract sections
    orig_sec2 = orig_data[sec2_off : sec2_off + orig_sec2_size]
    new_sec2 = patched_data[sec2_off : sec2_off + pat_sec2_size]

    # Parse groups
    old_groups = parse_sec2_group_offsets(orig_sec2)
    new_groups = parse_sec2_group_offsets(new_sec2)

    if len(old_groups) != len(new_groups):
        print(
            "  WARNING: Group count changed (%d -> %d). "
            "Offset patching may be unreliable."
            % (len(old_groups), len(new_groups))
        )

    # Check if anything actually changed
    if orig_sec2_size == pat_sec2_size and orig_sec2 == new_sec2:
        print("  Section 2 unchanged, no patching needed.")
        return patched_data

    print(
        "  Section 2: %d -> %d bytes (%+d), %d -> %d groups"
        % (
            orig_sec2_size,
            pat_sec2_size,
            pat_sec2_size - orig_sec2_size,
            len(old_groups),
            len(new_groups),
        )
    )

    # Parse Section 1 as big-endian uint16 words
    sec1_bytes = bytearray(patched_data[header_size:sec2_off])
    n_words = len(sec1_bytes) // 2
    words = [struct.unpack_from(">H", sec1_bytes, i * 2)[0] for i in range(n_words)]

    old_sec2_words = orig_sec2_size // 2

    # Scan for opcodes using PATTERN MATCHING rather than sequential walking.
    # Sequential walking fails because Section 1 contains data regions (zero padding,
    # 0xFFFF values, etc.) that aren't valid opcodes. Walking by unknown-opcode=1
    # causes desynchronization, making the walker miss real opcodes.
    #
    # Pattern matching is safe here because:
    #   - DISPLAY_TEXT has a distinctive 5-word pattern: 0004 0000 xxxx 0000 xxxx
    #   - SET_NAME_REF/CLEAR_NAME_REF: 000C/000D followed by param and glyph_idx
    #   - False positives are filtered by checking if the glyph offset/index
    #     falls within the old Section 2 bounds.

    patched_count = 0

    # Pass 1: DISPLAY_TEXT (0x0004) -- pattern: 0004 0000 GOFF 0000 GCNT
    for i in range(n_words - 4):
        if (
            words[i] == 0x0004
            and words[i + 1] == 0x0000
            and words[i + 3] == 0x0000
        ):
            old_off = words[i + 2]
            old_count = words[i + 4]

            new_off = remap_glyph_offset(old_off, old_groups, new_groups, is_display_text=True)
            new_count = remap_glyph_count(old_off, old_count, old_groups, new_groups)

            if new_off != old_off or new_count != old_count:
                if new_off > 0xFFFF:
                    print(
                        "  WARNING: DISPLAY_TEXT at S1+0x%04x: remapped offset %d overflows u16 "
                        "(old=%d). Opcode left unchanged to avoid corruption."
                        % (i * 2, new_off, old_off)
                    )
                    continue
                if new_count > 0xFFFF:
                    print(
                        "  WARNING: DISPLAY_TEXT at S1+0x%04x: remapped count %d overflows u16 "
                        "(old=%d). Opcode left unchanged to avoid corruption."
                        % (i * 2, new_count, old_count)
                    )
                    continue
                words[i + 2] = new_off & 0xFFFF
                words[i + 4] = new_count & 0xFFFF
                patched_count += 1

    # Pass 2: SET_NAME_REF (0x000C) and CLEAR_NAME_REF (0x000D)
    for i in range(n_words - 2):
        if words[i] in (0x000C, 0x000D):
            param = words[i + 1]
            old_idx = words[i + 2]

            # Only remap if the glyph_idx is a valid Section 2 reference.
            # Known param types that reference Section 2: 0, 2, 6
            # param=121 with small values is NOT a Section 2 reference.
            if old_idx < old_sec2_words and param != 121:
                new_idx = remap_glyph_offset(old_idx, old_groups, new_groups)
                if new_idx != old_idx:
                    if new_idx > 0xFFFF:
                        print(
                            "  WARNING: %s at S1+0x%04x: remapped glyph_idx %d overflows u16 "
                            "(old=%d). Opcode left unchanged to avoid corruption."
                            % (
                                "SET_NAME_REF" if words[i] == 0x000C else "CLEAR_NAME_REF",
                                i * 2,
                                new_idx,
                                old_idx,
                            )
                        )
                        continue
                    words[i + 2] = new_idx & 0xFFFF
                    patched_count += 1

    print("  Patched %d opcode references in Section 1" % patched_count)

    # Write patched words back to section 1 bytes
    for wi in range(n_words):
        struct.pack_into(">H", sec1_bytes, wi * 2, words[wi])

    # Reassemble: header (with updated sec2_size) + patched Section 1 + new Section 2
    header = bytearray(patched_data[:header_size])
    # sec2_size should already be correct in patched_data, but ensure it
    struct.pack_into("<I", header, 0x14, pat_sec2_size)

    # Everything after sec2 in the patched file (padding, etc.)
    after_sec2 = patched_data[sec2_off + pat_sec2_size :]

    block = bytes(header) + bytes(sec1_bytes) + bytes(new_sec2) + after_sec2

    return block


def patch_file(orig_path, patched_path, output_path=None):
    """
    Patch a single type-02 resource file.

    orig_path:    path to the ORIGINAL (unmodified) resource
    patched_path: path to the PATCHED resource (with injected Section 2)
    output_path:  where to write the result (defaults to overwriting patched_path)
    """
    if output_path is None:
        output_path = patched_path

    orig_data = open(orig_path, "rb").read()
    patched_data = open(patched_path, "rb").read()

    result = patch_section1(orig_data, patched_data)

    # Pad to sector boundary
    sc = math.ceil(len(result) / SECTOR)
    if len(result) < sc * SECTOR:
        result = result + b"\x00" * (sc * SECTOR - len(result))

    open(output_path, "wb").write(result)
    return output_path


def inject_and_patch(res_idx, msg_translations, raw_dir, out_dir):
    """
    Full pipeline: inject translations with variable-size, then patch Section 1 offsets.

    This is the proper replacement for fixed-size injection.

    res_idx:          resource number (e.g., 1198)
    msg_translations: dict {msg_index: [glyph_list]}
    raw_dir:          directory with original *_type02.raw files
    out_dir:          output directory for patched files

    Returns (output_filename, status_string) or (None, error_string).
    """
    # We import inject_resource logic inline to avoid circular dependencies
    raw_path = os.path.join(raw_dir, "{:04d}_type02.raw".format(res_idx))
    if not os.path.isfile(raw_path):
        return (None, "no _type02.raw found")

    raw = bytearray(open(raw_path, "rb").read())
    orig_bytes = bytes(raw)  # save original for offset patching

    if len(raw) < 0x1C:
        return (None, "file too small")

    sec2_size = struct.unpack_from("<I", raw, 0x14)[0]
    sec2_offset = struct.unpack_from("<I", raw, 0x18)[0]

    if sec2_offset == 0 or sec2_offset >= len(raw):
        return (None, "invalid sec2_offset=0x{:x}".format(sec2_offset))
    if sec2_size < 4:
        return (None, "sec2_size too small")

    sec2_end = sec2_offset + sec2_size

    # Parse Section 2 groups
    sec2_data = raw[sec2_offset:sec2_end]
    n_words = len(sec2_data) // 2
    words = [struct.unpack_from(">H", sec2_data, i * 2)[0] for i in range(n_words)]

    groups = []
    start = 0
    for i in range(n_words):
        if words[i] == 0xFFFF:
            groups.append(words[start:i])
            start = i + 1

    # Preserve trailing data after last FFFF terminator.
    # Resources like R989, R1034 have massive scene/dungeon script data
    # (60-77KB) after their last FFFF. Dropping this causes crashes.
    trailing_words = words[start:] if start < n_words else []

    if not groups:
        return (None, "no FFFF groups in Section 2")

    # Replace translated messages (variable-size -- no padding!)
    replaced = 0
    for msg_idx, eng_glyphs in msg_translations.items():
        if msg_idx < 0 or msg_idx >= len(groups):
            print(
                "    WARNING: R%d msg_index %d out of range (0..%d)"
                % (res_idx, msg_idx, len(groups) - 1)
            )
            continue

        original_group = groups[msg_idx]

        # Split into leading controls, text, trailing controls
        leading, _old_text, trailing = _split_control_and_text(original_group)
        groups[msg_idx] = leading + eng_glyphs + trailing
        replaced += 1

    # Rebuild Section 2
    new_sec2 = bytearray()
    for group in groups:
        for g in group:
            new_sec2 += struct.pack(">H", g)
        new_sec2 += struct.pack(">H", 0xFFFF)
    # Append trailing data preserved from after the last FFFF
    for t in trailing_words:
        new_sec2 += struct.pack(">H", t)

    new_sec2_size = len(new_sec2)

    # Build injected file (Section 1 unchanged, new Section 2)
    section1 = bytearray(raw[:sec2_offset])
    struct.pack_into("<I", section1, 0x14, new_sec2_size)

    after_sec2 = raw[sec2_end:]
    injected = bytes(section1) + bytes(new_sec2) + bytes(after_sec2)

    # Now patch Section 1 offsets
    result = patch_section1(orig_bytes, injected)

    # Pad to sector boundary
    sc = math.ceil(len(result) / SECTOR)
    if len(result) < sc * SECTOR:
        result = result + b"\x00" * (sc * SECTOR - len(result))

    out_name = os.path.basename(raw_path)
    out_path = os.path.join(out_dir, out_name)
    os.makedirs(out_dir, exist_ok=True)
    open(out_path, "wb").write(result)

    size_delta = new_sec2_size - sec2_size
    old_sc = len(raw) // SECTOR if len(raw) >= SECTOR else 1
    status = "replaced %d/%d, sec2 %d->%d (%+d bytes), %d->%d sectors, OFFSETS PATCHED" % (
        replaced,
        len(groups),
        sec2_size,
        new_sec2_size,
        size_delta,
        old_sc,
        sc,
    )
    return (out_name, status)


def _split_control_and_text(group):
    """Split a group into leading controls, text, trailing controls."""
    if not group:
        return ([], [], [])

    lead_end = 0
    for i, g in enumerate(group):
        if g < 0xFB00:
            lead_end = i
            break
    else:
        return (list(group), [], [])

    trail_start = len(group)
    for i in range(len(group) - 1, lead_end - 1, -1):
        if group[i] < 0xFB00:
            trail_start = i + 1
            break

    return (list(group[:lead_end]), list(group[lead_end:trail_start]), list(group[trail_start:]))


# ---------------------------------------------------------------------------
# Verification / diagnostics
# ---------------------------------------------------------------------------
def verify_patched(orig_path, patched_path):
    """
    Verify that a patched file's Section 1 references are consistent with its Section 2.
    Returns list of issues found.
    """
    orig = open(orig_path, "rb").read()
    patched = open(patched_path, "rb").read()

    sec2_size = struct.unpack_from("<I", patched, 0x14)[0]
    sec2_off = struct.unpack_from("<I", patched, 0x18)[0]
    sec2 = patched[sec2_off : sec2_off + sec2_size]
    sec2_words = sec2_size // 2

    # Parse groups in patched section 2
    groups = parse_sec2_group_offsets(sec2)

    # Parse Section 1
    s1 = patched[28:sec2_off]
    n = len(s1) // 2
    words = [struct.unpack_from(">H", s1, i * 2)[0] for i in range(n)]

    issues = []
    text_ops = 0
    name_ops = 0

    # Pattern-based scanning (same approach as the patcher)
    for i in range(n - 4):
        if words[i] == 0x0004 and words[i + 1] == 0 and words[i + 3] == 0:
            goff = words[i + 2]
            glen = words[i + 4]
            text_ops += 1

            if glen == 0:
                continue

            if goff >= sec2_words:
                if goff < 0x4000:
                    issues.append(
                        "DISPLAY_TEXT at S1+0x%04x: offset %d beyond Section 2 (%d words)"
                        % (i * 2, goff, sec2_words)
                    )
            else:
                end = goff + glen
                if end > sec2_words:
                    issues.append(
                        "DISPLAY_TEXT at S1+0x%04x: range %d..%d exceeds Section 2 (%d words)"
                        % (i * 2, goff, end, sec2_words)
                    )
                else:
                    last_word = struct.unpack_from(">H", sec2, (end - 1) * 2)[0]
                    if last_word != 0xFFFF:
                        issues.append(
                            "DISPLAY_TEXT at S1+0x%04x: off=%d cnt=%d does not end at FFFF "
                            "(word[end-1]=0x%04x)"
                            % (i * 2, goff, glen, last_word)
                        )

    for i in range(n - 2):
        if words[i] in (0x000C, 0x000D):
            param = words[i + 1]
            gidx = words[i + 2]
            name_ops += 1

            if param != 121 and gidx >= sec2_words and gidx < 0x4000:
                issues.append(
                    "%s at S1+0x%04x: glyph_idx %d beyond Section 2 (%d words)"
                    % ("SET_NAME" if words[i] == 0x000C else "CLR_NAME", i * 2, gidx, sec2_words)
                )

    return issues, text_ops, name_ops


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    if len(sys.argv) < 2:
        # Default: test on R1198
        print("=" * 60)
        print("  SECTION 1 OFFSET PATCHER -- Test Mode (R1198)")
        print("=" * 60)

        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        os.chdir(base)

        # We need to do a variable-size injection first, then patch offsets
        sys.path.insert(0, "tools")
        from encode_english_text import encode_text

        import json

        raw_dir = "extracted/packdata_raw"
        out_dir = "build/patched_type2"
        trans_file = "data/type2_translated/batch_r1198.json"

        if not os.path.isfile(trans_file):
            print("ERROR: Translation file not found:", trans_file)
            sys.exit(1)

        entries = json.load(open(trans_file, encoding="utf-8"))
        print("Loaded %d translation entries for R1198" % len(entries))

        # Encode translations
        def clean_and_encode(text):
            text = text.strip()
            if not text:
                return []
            if text.endswith(" /"):
                text = text + " "
            if " / " in text:
                parts = text.split(" / ")
                glyphs = []
                for pi, part in enumerate(parts):
                    part = part.strip()
                    if pi > 0:
                        glyphs.append(0xFFFE)
                    if part:
                        glyphs.extend(encode_text(part, max_chars_per_line=18, max_lines_per_page=3))
                return glyphs
            else:
                return encode_text(text, max_chars_per_line=18, max_lines_per_page=3)

        msg_trans = {}
        for entry in entries:
            eng = entry.get("english", "").strip()
            jpn = entry.get("japanese", "").strip()
            if not eng or eng == jpn:
                continue
            msg_idx = int(entry["msg_index"])
            try:
                glyphs = clean_and_encode(eng)
                if glyphs:
                    msg_trans[msg_idx] = glyphs
            except Exception as e:
                print("  ERROR encoding msg %d: %s" % (msg_idx, e))

        print("Encoded %d messages" % len(msg_trans))
        print()

        # Inject and patch
        print("Injecting with VARIABLE-SIZE and patching offsets...")
        out_name, status = inject_and_patch(1198, msg_trans, raw_dir, out_dir)
        if out_name:
            print("  SUCCESS: %s -> %s" % (out_name, status))
        else:
            print("  FAILED:", status)
            sys.exit(1)

        # Verify
        print()
        print("Verifying patched file...")
        orig_path = os.path.join(raw_dir, "1198_type02.raw")
        patched_path = os.path.join(out_dir, "1198_type02.raw")
        issues, text_ops, name_ops = verify_patched(orig_path, patched_path)

        print("  DISPLAY_TEXT opcodes: %d" % text_ops)
        print("  Name ref opcodes: %d" % name_ops)
        if issues:
            print("  ISSUES FOUND:")
            for issue in issues:
                print("    - %s" % issue)
        else:
            print("  ALL REFERENCES VALID")

        # Show detailed diff
        print()
        print("Offset mapping details:")
        orig = open(orig_path, "rb").read()
        patched = open(patched_path, "rb").read()
        o_s2size = struct.unpack_from("<I", orig, 0x14)[0]
        p_s2size = struct.unpack_from("<I", patched, 0x14)[0]
        sec2_off = struct.unpack_from("<I", orig, 0x18)[0]

        o_s1 = orig[28:sec2_off]
        p_s1 = patched[28:sec2_off]
        o_words = [struct.unpack_from(">H", o_s1, j * 2)[0] for j in range(len(o_s1) // 2)]
        p_words = [struct.unpack_from(">H", p_s1, j * 2)[0] for j in range(len(p_s1) // 2)]

        print("  %-8s %-20s %-20s" % ("S1 off", "Original", "Patched"))
        print("  " + "-" * 50)
        # Pattern-based diff display
        for j in range(len(o_words) - 4):
            if o_words[j] == 0x0004 and o_words[j + 1] == 0 and o_words[j + 3] == 0:
                o_off, o_cnt = o_words[j + 2], o_words[j + 4]
                p_off, p_cnt = p_words[j + 2], p_words[j + 4]
                if o_off != p_off or o_cnt != p_cnt:
                    print(
                        "  0x%04x   DISP off=%d cnt=%d    -> off=%d cnt=%d"
                        % (j * 2, o_off, o_cnt, p_off, p_cnt)
                    )
        for j in range(len(o_words) - 2):
            if o_words[j] in (0x000C, 0x000D):
                o_idx = o_words[j + 2]
                p_idx = p_words[j + 2]
                if o_idx != p_idx:
                    name = "SET_NAME" if o_words[j] == 0x000C else "CLR_NAME"
                    print(
                        "  0x%04x   %s idx=%d       -> idx=%d"
                        % (j * 2, name, o_idx, p_idx)
                    )

        print()
        print("Original sec2: %d bytes, Patched sec2: %d bytes" % (o_s2size, p_s2size))
        print("Section 1 changed: %s" % (o_s1 != p_s1))

    elif len(sys.argv) >= 3:
        orig_path = sys.argv[1]
        patched_path = sys.argv[2]
        output_path = sys.argv[3] if len(sys.argv) > 3 else patched_path

        print("Patching Section 1 offsets:")
        print("  Original: %s" % orig_path)
        print("  Patched:  %s" % patched_path)
        print("  Output:   %s" % output_path)

        patch_file(orig_path, patched_path, output_path)

        print()
        print("Verifying...")
        issues, text_ops, name_ops = verify_patched(orig_path, output_path)
        print("  DISPLAY_TEXT: %d, Name refs: %d" % (text_ops, name_ops))
        if issues:
            for issue in issues:
                print("  ISSUE: %s" % issue)
        else:
            print("  ALL REFERENCES VALID")
    else:
        print("Usage: python patch_section1_offsets.py <original.raw> <patched.raw> [output.raw]")
        print("       python patch_section1_offsets.py   (test mode with R1198)")
        sys.exit(1)


if __name__ == "__main__":
    main()
