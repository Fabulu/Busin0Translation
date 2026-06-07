"""
Extract ALL untranslated type-2 dialogue from PACKDATA raw resources
into a markdown file for translation.
"""
import struct, json, glob, os, sys, re

BASE = "C:/Programmieren/wizardrytranslation"
RAW_DIR = os.path.join(BASE, "extracted/packdata_raw")
GLYPH_MAP_PATH = os.path.join(BASE, "data/msg_glyph_map.json")
OVERRIDES_PATH = os.path.join(BASE, "data/type2_glyph_overrides.json")
BATCH_GLOB = os.path.join(BASE, "data/type2_translated/batch_*.json")
OUTPUT_MD = os.path.join(BASE, "data/untranslated_type2_dialogue.md")

sys.stdout.reconfigure(encoding="utf-8")

# --- Load glyph map with overrides ---
with open(GLYPH_MAP_PATH, "r", encoding="utf-8") as f:
    glyph_map = {int(k): v for k, v in json.load(f).items()}

if os.path.exists(OVERRIDES_PATH):
    with open(OVERRIDES_PATH, "r", encoding="utf-8") as f:
        overrides = json.load(f)
    for gid_str, info in overrides.items():
        glyph_map[int(gid_str)] = info["t2"]
    print(f"Loaded {len(overrides)} glyph overrides")

print(f"Loaded {len(glyph_map)} glyph mappings")

# --- Load already-translated (resource, msg_index) pairs ---
translated_set = set()  # (resource, msg_index)
translated_resources = set()

for batch_path in sorted(glob.glob(BATCH_GLOB)):
    with open(batch_path, "r", encoding="utf-8") as f:
        batch = json.load(f)
    for entry in batch:
        r = entry.get("resource")
        m = entry.get("msg_index")
        eng = (entry.get("english") or "").strip()
        if r is not None and m is not None and eng:
            translated_set.add((r, m))
            translated_resources.add(r)

print(f"Already translated: {len(translated_set)} messages across {len(translated_resources)} resources")

# --- Find all type-2 raw files ---
raw_files = sorted(glob.glob(os.path.join(RAW_DIR, "*_type02.raw")))
print(f"Found {len(raw_files)} type-2 raw resource files")


def decode_glyph(g):
    """Decode a single glyph ID to text."""
    if g == 0xFFFE:
        return " / "
    if g == 0xFFD2:
        return " // "
    if 0 <= g <= 94:
        return chr(g + 0x20)
    if g in glyph_map:
        return glyph_map[g]
    return f"[0x{g:04X}]"


def decode_message(glyphs):
    """Decode a list of glyph IDs (excluding FFFF terminator) to text."""
    parts = []
    for g in glyphs:
        if g >= 0xFB00:
            # Control codes -- skip silently
            continue
        parts.append(decode_glyph(g))
    return "".join(parts)


def is_meaningful_text(glyphs):
    """Check if a glyph stream likely contains real dialogue text."""
    text_glyphs = [g for g in glyphs if g < 0xFB00 and g != 0xFFFE and g != 0xFFD2]
    if len(text_glyphs) < 5:
        return False
    # Reject extremely long "messages" -- real dialogue is under 500 glyphs
    if len(text_glyphs) > 500:
        return False
    # Check if enough glyphs map to known characters
    mapped = sum(1 for g in text_glyphs if g <= 94 or g in glyph_map)
    if len(text_glyphs) == 0:
        return False
    coverage = mapped / len(text_glyphs)
    if coverage < 0.50 or mapped < 5:
        return False
    # Check for consecutive runs of mapped NON-SPACE characters
    # Real dialogue has long runs; garbage has isolated mapped chars
    max_run = 0
    current_run = 0
    for g in text_glyphs:
        is_mapped = (g <= 94 or g in glyph_map)
        is_space = (g <= 1)  # glyph 0 and 1 are both spaces
        if is_mapped and not is_space:
            current_run += 1
            max_run = max(max_run, current_run)
        else:
            current_run = 0
    # Require at least 4 consecutive mapped non-space characters
    return max_run >= 4


def extract_resource(raw_path):
    """Extract all messages from a type-2 raw resource file."""
    basename = os.path.basename(raw_path)
    res_idx = int(basename.split("_")[0])

    data = open(raw_path, "rb").read()
    if len(data) < 0x1C:
        return res_idx, []

    sec2_size = struct.unpack_from("<I", data, 0x14)[0]
    sec2_offset = struct.unpack_from("<I", data, 0x18)[0]

    if sec2_offset == 0 or sec2_offset >= len(data):
        return res_idx, []
    if sec2_size < 4:
        return res_idx, []

    sec2_end = min(sec2_offset + sec2_size, len(data))
    sec2_data = data[sec2_offset:sec2_end]

    n_words = len(sec2_data) // 2
    words = [struct.unpack_from(">H", sec2_data, i * 2)[0] for i in range(n_words)]

    # Split into groups by FFFF
    groups = []
    start = 0
    for i in range(n_words):
        if words[i] == 0xFFFF:
            groups.append(words[start:i])
            start = i + 1

    # Skip resources with an unreasonable number of groups (data tables, not dialogue)
    # Real dialogue resources typically have <2000 messages
    if len(groups) > 3000:
        return res_idx, []

    messages = []
    for msg_idx, group in enumerate(groups):
        # Skip if already translated
        if (res_idx, msg_idx) in translated_set:
            continue
        # Skip empty groups
        if not group:
            continue
        # Check if meaningful
        if not is_meaningful_text(group):
            continue

        decoded = decode_message(group)
        # Skip if decoded text is too short after removing placeholders
        clean = re.sub(r"\[0x[0-9A-Fa-f]{4}\]", "", decoded).strip()
        clean = clean.replace(" / ", "").replace(" // ", "")
        # Remove all whitespace for real char count
        real_chars = clean.replace(" ", "").replace("`", "").replace("@", "")
        if len(real_chars) < 4:
            continue
        # Skip if hex placeholders dominate the text (more placeholders than real chars)
        hex_count = len(re.findall(r"\[0x[0-9A-Fa-f]{4}\]", decoded))
        if hex_count > len(real_chars):
            continue
        # Skip entries where the longest word-like run of non-space mapped chars is too short
        # This catches "ち ち ち ち" patterns and isolated character lists
        words_in_clean = re.findall(r"[^\s]{2,}", clean)
        if not words_in_clean:
            continue
        longest_word = max(len(w) for w in words_in_clean)
        if longest_word < 3:
            continue
        # Require at least SOME hiragana or kanji (real Japanese text always has these)
        # Pure katakana + ASCII is almost always binary noise
        has_hiragana_or_kanji = bool(re.search(r"[\u3040-\u309F\u4E00-\u9FFF\u3000-\u303F]", clean))
        if not has_hiragana_or_kanji:
            # Exception: allow if it's clearly a name or short phrase in katakana
            # (at least 3 katakana in a row forming a word)
            has_katakana_word = bool(re.search(r"[\u30A0-\u30FF]{3,}", clean))
            if not has_katakana_word:
                continue

        messages.append((msg_idx, decoded))

    return res_idx, messages


# --- Extract all ---
all_entries = []  # (resource, msg_idx, japanese_text)
resources_with_text = 0
resources_skipped_empty = 0

for i, raw_path in enumerate(raw_files):
    res_idx, messages = extract_resource(raw_path)
    if messages:
        resources_with_text += 1
        for msg_idx, text in messages:
            all_entries.append((res_idx, msg_idx, text))
    else:
        resources_skipped_empty += 1

    if (i + 1) % 100 == 0:
        print(f"  Processed {i+1}/{len(raw_files)}, {len(all_entries)} entries so far...")

print(f"\nExtraction complete:")
print(f"  Resources with untranslated text: {resources_with_text}")
print(f"  Resources skipped (empty/binary): {resources_skipped_empty}")
print(f"  Total untranslated entries: {len(all_entries)}")

# --- Write markdown ---
with open(OUTPUT_MD, "w", encoding="utf-8") as f:
    f.write("# Untranslated Type-2 Dialogue - Busin 0: Wizardry Alternative Neo\n\n")
    f.write("This file contains ALL untranslated dialogue from type-2 resources in PACKDATA.\n")
    f.write("Type-2 resources contain game scripts: dungeon events, NPC conversations, story scenes, combat messages, etc.\n\n")
    f.write("## Format\n\n")
    f.write("Each entry shows the resource number (R) and message index (M).\n")
    f.write("The Japanese text is decoded from glyph streams. Some characters may appear as `[0xNNNN]` if unmapped.\n")
    f.write("Fill in the `English:` line with the translation. Use ` / ` for line breaks and ` // ` for page breaks.\n\n")
    f.write(f"**Total entries: {len(all_entries)}**\n\n")
    f.write("---\n\n")

    current_res = None
    for res_idx, msg_idx, text in all_entries:
        if res_idx != current_res:
            if current_res is not None:
                f.write("\n---\n\n")
            current_res = res_idx
            f.write(f"## Resource {res_idx}\n\n")

        f.write(f"### R{res_idx}:M{msg_idx}\n")
        f.write(f"- Japanese: {text}\n")
        f.write(f"- English: \n\n")

print(f"Written to {OUTPUT_MD}")
print(f"File size: {os.path.getsize(OUTPUT_MD) / 1024:.1f} KB")
