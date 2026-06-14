#!/usr/bin/env python3
"""
inject_type2_dialogue.py -- Inject translated English dialogue into type-2 resources
=====================================================================================

Reads translated dialogue from data/type2_translated/*.json and injects it into
the corresponding type-2 resources from extracted/packdata_raw/, writing patched
copies to build/patched_type2/.

Type-2 resource binary layout:
  - Header (variable size), with:
      +0x14  LE u32  sec2_size   (byte size of Section 2)
      +0x18  LE u32  sec2_offset (byte offset to Section 2 start)
  - Section 1: non-text data (models, scripts, etc.) -- preserved byte-for-byte
  - Section 2: dialogue as BE uint16 glyph stream
      Messages delimited by 0xFFFF
      Line breaks within a message: 0xFFFE
      Control codes: >= 0xFB00

Translation JSON format (each file in data/type2_translated/):
  [
    {
      "resource": 1203,
      "msg_index": 4,
      "japanese": "original text...",
      "english": "translated text..."
    },
    ...
  ]

Usage:
    cd C:/Programmieren/wizardrytranslation
    python tools/inject_type2_dialogue.py
"""

import sys, io, os, struct, json, glob, math

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(BASE)

sys.path.insert(0, "tools")
from encode_english_text import encode_text

# Force UTF-8 output (reconfigure rather than re-wrap, since
# encode_english_text already wrapped sys.stdout)
sys.stdout.reconfigure(encoding="utf-8")

SECTOR = 2048
RAW_DIR = "extracted/packdata_raw"
TRANS_DIR = "data/type2_translated"
OUT_DIR = "build/patched_type2"

print("=" * 60)
print("  TYPE-2 DIALOGUE INJECTOR")
print("=" * 60)
print()

# ---------------------------------------------------------------------------
# STEP 1 -- Load all translation files
# ---------------------------------------------------------------------------
print("STEP 1: Loading translations ...")

if not os.path.isdir(TRANS_DIR):
    print("  ERROR: Translation directory not found: " + TRANS_DIR)
    print("  Create it and add JSON translation files.")
    sys.exit(1)

trans_files = sorted(glob.glob(os.path.join(TRANS_DIR, "*.json")))
if not trans_files:
    print("  ERROR: No JSON files found in " + TRANS_DIR)
    sys.exit(1)

# Load and merge all translation entries, later files override earlier
all_entries = []
for fp in trans_files:
    try:
        chunk = json.load(open(fp, encoding="utf-8"))
        all_entries.extend(chunk)
        print("  " + os.path.basename(fp) + ": " + str(len(chunk)) + " entries")
    except Exception as e:
        print("  WARNING: Failed to load " + fp + ": " + str(e))

print("  Total raw entries: " + str(len(all_entries)))

# De-duplicate: (resource, msg_index) -> entry, later wins
trans_map = {}
for entry in all_entries:
    res = entry.get("resource")
    msg = entry.get("msg_index")
    eng = (entry.get("english") or "").strip()
    if res is None or msg is None or not eng:
        continue
    trans_map[(int(res), int(msg))] = entry

print("  Unique (resource, msg_index) pairs: " + str(len(trans_map)))

# Group by resource
by_resource = {}
for (res, msg), entry in trans_map.items():
    by_resource.setdefault(res, {})[msg] = entry

print("  Resources with translations: " + str(len(by_resource)))

# ---------------------------------------------------------------------------
# STEP 2 -- Encode English text to glyph streams
# ---------------------------------------------------------------------------
print()
print("STEP 2: Encoding English text ...")


# Control words used in the glyph stream
LINE_BREAK = 0xFFFE   # ' / '  -> line break within a page
PAGE_BREAK = 0xFFD2   # ' // ' -> page break (advance to next text page)

# Safety hard-wrap fallback. The authored ' / ' breaks carry the real wrapping;
# this only kicks in if an individual segment is wider than the narrowest frame
# (centered narration ~16 glyphs). Segments already <= this are NOT re-wrapped.
WRAP_FALLBACK = 16


def _encode_segment(segment):
    """Encode a single (already line-broken) text segment, hard-wrapping only
    if it exceeds WRAP_FALLBACK glyphs."""
    segment = segment.strip()
    if not segment:
        return []
    return encode_text(segment, max_chars_per_line=WRAP_FALLBACK, max_lines_per_page=3)


def clean_and_encode(english_text):
    """Encode an English translation to a glyph stream.

    Delimiter convention (applied in order):
      ' // ' -> page break (0xFFD2)
      ' / '  -> line break (0xFFFE)

    Each resulting segment is hard-wrapped only if it exceeds WRAP_FALLBACK.
    """
    text = english_text.strip()
    if not text:
        return []

    # Normalize a trailing " /" (no final space) to " / " for a clean split.
    # (Do not disturb a trailing " //".)
    if text.endswith(" /") and not text.endswith(" //"):
        text = text + " "

    glyphs = []
    # Split on PAGE breaks first, then LINE breaks within each page.
    pages = text.split(" // ")
    for page_i, page in enumerate(pages):
        page = page.strip()
        if page_i > 0:
            glyphs.append(PAGE_BREAK)  # page break between pages
        if not page:
            continue

        # Normalize trailing " /" within this page too.
        if page.endswith(" /"):
            page = page + " "

        parts = page.split(" / ")
        for pi, part in enumerate(parts):
            part = part.strip()
            if pi > 0:
                glyphs.append(LINE_BREAK)  # line break between parts
            if not part:
                continue
            glyphs.extend(_encode_segment(part))

    return glyphs


# ---------------------------------------------------------------------------
# Choice-group (FFC0/FFC1/FFC2...) support
# ---------------------------------------------------------------------------
CHOICE_MIN = 0xFFC0
CHOICE_MAX = 0xFFCF  # FFC0..FFCF reserved for option markers


def _is_choice_marker(w):
    return CHOICE_MIN <= w <= CHOICE_MAX


def group_choice_markers(group):
    """Return the ordered list of choice-marker words (FFC0, FFC1, ...) present
    in a FFFF-group, in stream order. Empty if this is not a choice group."""
    return [w for w in group if _is_choice_marker(w)]


def split_choice_group(group):
    """Split a choice FFFF-group into:
        leading_ctrls, question_words, [(marker, option_words), ...]
    The question is everything before the first marker; each marker owns the
    text words up to the next marker (or end of group).
    """
    # Leading contiguous controls (>= 0xFB00) at the very start.
    lead_end = 0
    for i, g in enumerate(group):
        if g < 0xFB00:
            lead_end = i
            break
    else:
        lead_end = len(group)
    leading = list(group[:lead_end])
    body = group[lead_end:]

    # First marker position within body.
    first_marker = None
    for i, g in enumerate(body):
        if _is_choice_marker(g):
            first_marker = i
            break
    if first_marker is None:
        return (leading, list(body), [])

    question = list(body[:first_marker])
    options = []
    i = first_marker
    n = len(body)
    while i < n:
        marker = body[i]
        j = i + 1
        while j < n and not _is_choice_marker(body[j]):
            j += 1
        options.append((marker, list(body[i + 1:j])))
        i = j
    return (leading, question, options)


def encode_choice_group(original_group, english_text):
    """Rebuild a choice group, preserving the original marker sequence and
    substituting English for the question and each option segment.

    The English convention: split on ' / ' (and ' // '). The LAST N segments
    (N = number of markers) are the options, one per marker. Everything before
    them is the question (its internal ' / '/' // ' become FFFE/FFD2 breaks).

    Returns (new_group, None) on success, or (None, reason) to keep original.
    """
    leading, _question_old, options_old = split_choice_group(original_group)
    markers = [m for (m, _txt) in options_old]
    n_markers = len(markers)
    if n_markers == 0:
        return (None, "no choice markers in original group")

    # Split English into segments on the ' / ' delimiter family. Use a sentinel
    # so ' // ' page breaks survive into the question encoding.
    text = english_text.strip()
    if text.endswith(" /") and not text.endswith(" //"):
        text = text + " "
    # Tokenize on ' / ' but remember which gaps were ' // ' (page breaks).
    # Simplest robust approach: split on ' / ' (page breaks ' // ' contain ' / '
    # so they split too, leaving an empty piece we re-join as a page marker).
    raw_parts = text.split(" / ")
    # Reconstruct: a ' // ' produced an empty segment between two parts; mark it.
    segments = []  # list of (kind, text) where kind in {"text"}
    # We rebuild question text with explicit delimiters preserved, then let
    # clean_and_encode handle question wrapping. For options we take plain text.
    parts = [p.strip() for p in raw_parts]

    if len(parts) < n_markers + 1:
        return (None,
                "english has {} ' / ' segments, need >= {} (question + {} options)".format(
                    len(parts), n_markers + 1, n_markers))

    option_texts = parts[-n_markers:]
    question_parts = parts[:-n_markers]

    # Re-join question parts with ' / ' and encode through clean_and_encode so
    # that any ' // ' page breaks the author put in the question are honored.
    question_str = " / ".join(p for p in question_parts if p != "")
    question_glyphs = clean_and_encode(question_str) if question_str else []

    new_group = list(leading) + list(question_glyphs)
    for idx, marker in enumerate(markers):
        opt_glyphs = _encode_segment(option_texts[idx])
        new_group.append(marker)
        new_group.extend(opt_glyphs)
    return (new_group, None)


# Map: resource -> { msg_index: english_text }. We store the raw English string
# (not pre-encoded glyphs) so inject_resource() can parse choice groups against
# their original FFC0/FFC1 markers. We still run clean_and_encode here as a
# validation pass (to surface encode errors / skip empties).
encoded_by_res = {}  # resource -> { msg_index: english_text }
errors = 0
skipped = 0

for (res, msg), entry in trans_map.items():
    eng = (entry.get("english") or "").strip()
    jpn = (entry.get("japanese") or "").strip()

    # Skip identity translations
    if eng == jpn:
        skipped += 1
        continue

    try:
        glyphs = clean_and_encode(eng)  # validation only
        if glyphs:
            encoded_by_res.setdefault(res, {})[msg] = eng
    except Exception as e:
        errors += 1
        if errors <= 10:
            print("  ERROR encoding R" + str(res) + "/msg" + str(msg) + ": " + str(e))

total_encoded = sum(len(v) for v in encoded_by_res.values())
print("  Encoded " + str(total_encoded) + " messages for " + str(len(encoded_by_res)) + " resources")
if skipped:
    print("  Skipped " + str(skipped) + " identity translations")
if errors:
    print("  Encoding errors: " + str(errors))


# ---------------------------------------------------------------------------
# STEP 3 -- Parse and inject into each resource
# ---------------------------------------------------------------------------
print()
print("STEP 3: Injecting into type-2 resources ...")
os.makedirs(OUT_DIR, exist_ok=True)


def parse_sec2_groups(sec2_data):
    """Parse Section 2 into FFFF-delimited message groups."""
    n_words = len(sec2_data) // 2
    words = [struct.unpack_from(">H", sec2_data, i * 2)[0] for i in range(n_words)]

    groups = []
    msg_start = 0
    for wi in range(n_words):
        if words[wi] == 0xFFFF:
            groups.append(words[msg_start:wi])
            msg_start = wi + 1

    # If there is trailing data after the last FFFF (rare but preserve it)
    if msg_start < n_words:
        trailing = words[msg_start:]
        if any(w != 0x0000 for w in trailing):
            groups.append(trailing)

    return groups


def split_control_and_text(group):
    """
    Split a FFFF-group into leading controls, text glyphs, and trailing controls.

    Control codes are >= 0xFB00. Speaker tags and other control sequences at the
    start/end of the group are preserved. The text portion is everything between
    the leading and trailing control regions. FFFE (line break) within the text
    region is considered part of the text.

    Returns (leading_ctrls, text_portion, trailing_ctrls).
    """
    if not group:
        return ([], [], [])

    # Leading controls: contiguous control codes (>= 0xFB00) at the start
    lead_end = 0
    for i, g in enumerate(group):
        if g < 0xFB00:
            lead_end = i
            break
    else:
        # Entire group is control codes
        return (list(group), [], [])

    # Trailing controls: contiguous control codes (>= 0xFB00) at the end
    trail_start = len(group)
    for i in range(len(group) - 1, lead_end - 1, -1):
        if group[i] < 0xFB00:
            trail_start = i + 1
            break

    leading = group[:lead_end]
    text = group[lead_end:trail_start]
    trailing = group[trail_start:]

    return (list(leading), list(text), list(trailing))


def inject_resource(res_idx, msg_translations):
    """
    Inject translated messages into a single type-2 resource.

    msg_translations: dict { msg_index: [glyph_list] }

    Returns (output_filename, status_string) or (None, error_string).
    """
    # Find the raw file
    raw_path = os.path.join(RAW_DIR, "{:04d}_type02.raw".format(res_idx))
    if not os.path.isfile(raw_path):
        print("  SKIP R{:04d}: no _type02.raw found, not a dialogue resource".format(res_idx))
        return (None, "skipped (no _type02.raw)")

    raw = bytearray(open(raw_path, "rb").read())

    if len(raw) < 0x1C:
        return (None, "file too small ({} bytes)".format(len(raw)))

    # Parse header to find Section 2
    sec2_size = struct.unpack_from("<I", raw, 0x14)[0]
    sec2_offset = struct.unpack_from("<I", raw, 0x18)[0]

    if sec2_offset == 0 or sec2_offset >= len(raw):
        return (None, "invalid sec2_offset=0x{:x}".format(sec2_offset))
    if sec2_size < 4:
        return (None, "sec2_size too small ({})".format(sec2_size))

    sec2_end = sec2_offset + sec2_size

    # Preserve everything before Section 2 (Section 1 + header)
    section1 = bytes(raw[:sec2_offset])

    # Preserve anything after Section 2 (rare but possible)
    after_sec2 = bytes(raw[sec2_end:])

    # Parse Section 2 into FFFF-delimited groups
    sec2_data = raw[sec2_offset:sec2_end]
    groups = parse_sec2_groups(sec2_data)

    if not groups:
        return (None, "no FFFF groups found in Section 2")

    # Replace translated messages. msg_translations maps msg_idx -> english text
    # (raw string) so that choice groups can be parsed against their markers.
    replaced = 0
    choices = 0
    for msg_idx, eng_text in msg_translations.items():
        if msg_idx < 0 or msg_idx >= len(groups):
            print("    WARNING: R{} msg_index {} out of range (0..{}), skipping".format(
                res_idx, msg_idx, len(groups) - 1))
            continue

        original_group = groups[msg_idx]

        # CHOICE-AWARE PATH: if the ORIGINAL group carries option markers
        # (FFC0/FFC1/FFC2...), preserve them and substitute English per segment.
        if group_choice_markers(original_group):
            new_group, reason = encode_choice_group(original_group, eng_text)
            if new_group is None:
                print("    WARNING: R{} msg{} choice group kept untranslated -- {}".format(
                    res_idx, msg_idx, reason))
                continue
            groups[msg_idx] = new_group
            replaced += 1
            choices += 1
            continue

        # PLAIN PATH: encode the English then splice between leading/trailing
        # controls, preserving the original control framing.
        eng_glyphs = clean_and_encode(eng_text)
        if not eng_glyphs:
            continue
        leading, _old_text, trailing = split_control_and_text(original_group)
        new_group = leading + eng_glyphs + trailing
        groups[msg_idx] = new_group
        replaced += 1

    # Rebuild Section 2 from groups
    new_sec2 = bytearray()
    for group in groups:
        for g in group:
            new_sec2 += struct.pack(">H", g)
        new_sec2 += struct.pack(">H", 0xFFFF)  # terminate each group

    new_sec2_size = len(new_sec2)

    # Update sec2_size in the header
    new_section1 = bytearray(section1)
    struct.pack_into("<I", new_section1, 0x14, new_sec2_size)
    # sec2_offset stays the same since Section 1 is unchanged

    # Assemble: section1 (with updated header) + new section 2 + after_sec2
    block = bytes(new_section1) + bytes(new_sec2) + after_sec2

    # Pad to sector boundary
    sc = math.ceil(len(block) / SECTOR)
    if len(block) < sc * SECTOR:
        block += b"\x00" * (sc * SECTOR - len(block))

    # Write output
    out_name = os.path.basename(raw_path)
    out_path = os.path.join(OUT_DIR, out_name)
    open(out_path, "wb").write(block)

    old_sc = len(raw) // SECTOR if len(raw) >= SECTOR else 1
    size_delta = new_sec2_size - sec2_size

    status_parts = [
        "replaced {}/{}".format(replaced, len(groups)),
        "({} choice groups)".format(choices) if choices else None,
        "sec2 {}->{}".format(sec2_size, new_sec2_size),
        "({:+d} bytes)".format(size_delta),
        "{}->{} sectors".format(old_sc, sc),
    ]
    status_parts = [p for p in status_parts if p]
    return (out_name, " ".join(status_parts))


# Process each resource
modified = 0
failed = 0

for res_idx in sorted(encoded_by_res.keys()):
    msg_trans = encoded_by_res[res_idx]
    result = inject_resource(res_idx, msg_trans)
    out_name, status = result

    if out_name:
        print("  R{:04d} ({}): {}".format(res_idx, out_name, status))
        modified += 1
    else:
        print("  R{:04d}: FAILED -- {}".format(res_idx, status))
        failed += 1

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
print()
print("=" * 60)
print("  INJECTION COMPLETE")
print("  {} messages encoded across {} resources".format(total_encoded, len(encoded_by_res)))
print("  {} resources patched -> {}/".format(modified, OUT_DIR))
if failed:
    print("  {} resources FAILED".format(failed))
if skipped:
    print("  {} identity translations skipped".format(skipped))
if errors:
    print("  {} encoding errors".format(errors))
print("=" * 60)
