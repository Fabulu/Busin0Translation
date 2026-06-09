"""
Deep scan of ALL type-2 PACKDATA resources for untranslated text.
Uses RELAXED filters compared to extract_untranslated_type2.py.
"""
import struct, json, glob, os, sys, re

BASE = "C:/Programmieren/wizardrytranslation"
RAW_DIR = os.path.join(BASE, "extracted/packdata_raw")
GLYPH_MAP_PATH = os.path.join(BASE, "data/msg_glyph_map.json")
OVERRIDES_PATH = os.path.join(BASE, "data/type2_glyph_overrides.json")
BATCH_GLOB = os.path.join(BASE, "data/type2_translated/batch_*.json")
OUTPUT_MD = os.path.join(BASE, "data/deep_scan_type2.md")

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
translated_set = set()
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
    parts = []
    for g in glyphs:
        if g >= 0xFB00:
            continue
        parts.append(decode_glyph(g))
    return "".join(parts)


# Unicode ranges for classification
HIRAGANA = re.compile(r'[\u3040-\u309F]')
KATAKANA = re.compile(r'[\u30A0-\u30FF]')
KANJI = re.compile(r'[\u4E00-\u9FFF]')
CJK_CHAR = re.compile(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF\u3000-\u303F]')


def classify_entry(clean_text, glyphs):
    """Classify an entry as DIALOGUE, SHORT_LABEL, or NOISE."""
    # Remove hex placeholders for analysis
    text = re.sub(r"\[0x[0-9A-Fa-f]{4}\]", "", clean_text).strip()
    text_no_space = text.replace(" ", "").replace("/", "").replace("`", "").replace("@", "")

    if len(text_no_space) == 0:
        return "NOISE"

    has_hiragana = bool(HIRAGANA.search(text))
    has_katakana = bool(KATAKANA.search(text))
    has_kanji = bool(KANJI.search(text))

    # Count meaningful CJK characters
    cjk_count = len(CJK_CHAR.findall(text))

    # SHORT_LABEL: 1-4 meaningful characters
    if len(text_no_space) <= 4:
        if has_hiragana or has_katakana or has_kanji:
            return "SHORT_LABEL"
        # Pure ASCII short labels (like "HP", "MP")
        if text_no_space.isascii() and text_no_space.isalpha():
            return "SHORT_LABEL"
        return "NOISE"

    # DIALOGUE: Contains hiragana + kanji forming sentences
    if has_hiragana and (has_kanji or has_katakana):
        return "DIALOGUE"

    # Hiragana-only can still be dialogue
    if has_hiragana and cjk_count >= 3:
        return "DIALOGUE"

    # Katakana words (names, loanwords) -- 3+ katakana in a row
    if bool(re.search(r'[\u30A0-\u30FF]{3,}', text)):
        if cjk_count >= 3:
            return "DIALOGUE" if len(text_no_space) > 4 else "SHORT_LABEL"

    # Kanji-only sequences (item names, labels)
    if has_kanji and cjk_count >= 2:
        return "SHORT_LABEL" if len(text_no_space) <= 6 else "DIALOGUE"

    # ASCII text that forms words
    if text_no_space.isascii() and len(text_no_space) >= 3:
        # Check if it has actual word-like patterns
        if re.search(r'[A-Za-z]{3,}', text):
            return "SHORT_LABEL" if len(text_no_space) <= 8 else "DIALOGUE"

    return "NOISE"


def extract_resource_relaxed(raw_path):
    """Extract messages with RELAXED filters."""
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

    # Skip resources with unreasonable number of groups
    if len(groups) > 5000:
        return res_idx, []

    messages = []
    for msg_idx, group in enumerate(groups):
        # Skip if already translated
        if (res_idx, msg_idx) in translated_set:
            continue
        # Skip empty groups
        if not group:
            continue

        # RELAXED filter: minimum 1 text glyph (was 5)
        text_glyphs = [g for g in group if g < 0xFB00 and g != 0xFFFE and g != 0xFFD2]
        if len(text_glyphs) < 1:
            continue
        # Still skip very long streams (data tables)
        if len(text_glyphs) > 500:
            continue

        # At least 1 mapped character
        mapped = sum(1 for g in text_glyphs if g <= 94 or g in glyph_map)
        if mapped < 1:
            continue

        decoded = decode_message(group)

        # Remove hex placeholders
        clean = re.sub(r"\[0x[0-9A-Fa-f]{4}\]", "", decoded).strip()
        clean = clean.replace(" / ", " ").replace(" // ", " ")

        # Remove whitespace for real char count
        real_chars = clean.replace(" ", "").replace("`", "").replace("@", "")

        # Skip if ALL hex placeholders (no real text)
        if len(real_chars) == 0:
            continue

        # Skip single punctuation or spaces
        if len(real_chars) == 1 and not real_chars.isalpha() and not CJK_CHAR.search(real_chars):
            continue

        # Skip if hex placeholders dominate (more hex tokens than real chars)
        hex_count = len(re.findall(r"\[0x[0-9A-Fa-f]{4}\]", decoded))
        if hex_count > len(real_chars):
            continue

        # Additional: check ratio of mapped glyphs to total glyphs
        # Real text has high mapping ratios; binary noise has low
        mapped = sum(1 for g in text_glyphs if g <= 94 or g in glyph_map)
        if len(text_glyphs) > 0 and mapped / len(text_glyphs) < 0.3:
            continue

        # Detect repeating character patterns (binary noise)
        # If any single character makes up >60% of the real chars, it's noise
        if len(real_chars) >= 4:
            from collections import Counter
            char_counts = Counter(real_chars)
            most_common_char, most_common_count = char_counts.most_common(1)[0]
            if most_common_count / len(real_chars) > 0.6:
                continue

        # Detect structural data patterns -- not text
        # "ブベ", "容ベ", "ベ " patterns are structural headers
        stripped_rc = real_chars.replace(" ", "")
        if any(stripped_rc.startswith(p) for p in ["ブベ", "ベブ", "容ベ", "ベ容", "ベ!"]):
            continue

        # Single character entries from data tables -- skip
        if len(real_chars) <= 1:
            continue

        # Skip entries that are just 2-3 chars with no sentence structure
        # (isolated kanji from data tables). Require either:
        # - hiragana (particles/conjugation = real text)
        # - katakana word of 3+ chars
        # - or 4+ kanji forming a compound
        if len(real_chars) <= 3:
            has_hira = bool(re.search(r'[\u3040-\u309F]', real_chars))
            has_kata_word = bool(re.search(r'[\u30A0-\u30FF]{3,}', real_chars))
            if not has_hira and not has_kata_word:
                continue

        # For entries with many hex placeholders mixed with scattered real chars,
        # require consecutive mapped chars forming a word-like run
        if hex_count >= 2 and len(real_chars) < 6:
            # Too many hex placeholders for such short text -- likely data
            continue

        # Require at least one run of 3+ consecutive CJK or word characters
        # This filters out scattered individual chars among control bytes
        cjk_or_word_runs = re.findall(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF\u3000-\u303FA-Za-z]{3,}', clean)
        if not cjk_or_word_runs and len(real_chars) < 8:
            continue

        # Final sanity: if text has many scattered single CJK chars separated
        # by hex/space, it's binary data. Real text has connected words.
        # Check: ratio of chars in 3+ runs vs total CJK chars
        all_cjk = re.findall(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]', clean)
        chars_in_runs = sum(len(r) for r in re.findall(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]{2,}', clean))
        if len(all_cjk) >= 4 and chars_in_runs / len(all_cjk) < 0.4:
            continue

        # Classify
        category = classify_entry(decoded, group)

        if category == "NOISE":
            continue

        messages.append((msg_idx, decoded, category))

    return res_idx, messages


# --- Extract all ---
all_entries = []  # (resource, msg_idx, japanese_text, category)
resources_with_text = 0
resources_skipped_empty = 0
category_counts = {"DIALOGUE": 0, "SHORT_LABEL": 0}

for i, raw_path in enumerate(raw_files):
    res_idx, messages = extract_resource_relaxed(raw_path)
    if messages:
        resources_with_text += 1
        for msg_idx, text, category in messages:
            all_entries.append((res_idx, msg_idx, text, category))
            category_counts[category] += 1
    else:
        resources_skipped_empty += 1

    if (i + 1) % 100 == 0:
        print(f"  Processed {i+1}/{len(raw_files)}, {len(all_entries)} entries so far...")

print(f"\nExtraction complete:")
print(f"  Resources with untranslated text: {resources_with_text}")
print(f"  Resources skipped (empty/binary): {resources_skipped_empty}")
print(f"  Total untranslated entries: {len(all_entries)}")
print(f"  DIALOGUE: {category_counts['DIALOGUE']}")
print(f"  SHORT_LABEL: {category_counts['SHORT_LABEL']}")

# --- Dedupe check: how many of these were in the previous extraction? ---
# Show per-resource breakdown
res_counts = {}
for res_idx, msg_idx, text, category in all_entries:
    if res_idx not in res_counts:
        res_counts[res_idx] = {"DIALOGUE": 0, "SHORT_LABEL": 0}
    res_counts[res_idx][category] += 1

# --- Write markdown ---
with open(OUTPUT_MD, "w", encoding="utf-8") as f:
    f.write("# Deep Scan: Untranslated Type-2 Text - Busin 0\n\n")
    f.write("Deep scan with RELAXED filters to catch sparse dialogue and short labels.\n\n")
    f.write(f"**Total entries: {len(all_entries)}** ")
    f.write(f"(DIALOGUE: {category_counts['DIALOGUE']}, SHORT_LABEL: {category_counts['SHORT_LABEL']})\n\n")
    f.write(f"**Resources with untranslated text: {resources_with_text}**\n\n")
    f.write("---\n\n")

    current_res = None
    for res_idx, msg_idx, text, category in all_entries:
        if res_idx != current_res:
            if current_res is not None:
                f.write("\n---\n\n")
            current_res = res_idx
            rc = res_counts[res_idx]
            f.write(f"## Resource {res_idx} ({rc['DIALOGUE']}D / {rc['SHORT_LABEL']}L)\n\n")

        f.write(f"### R{res_idx}:M{msg_idx} [{category}]\n")
        f.write(f"- Japanese: {text}\n")
        f.write(f"- English: \n\n")

print(f"Written to {OUTPUT_MD}")
print(f"File size: {os.path.getsize(OUTPUT_MD) / 1024:.1f} KB")

# --- Summary by resource ---
print(f"\n--- Per-resource breakdown (top 30 by count) ---")
sorted_res = sorted(res_counts.items(), key=lambda x: sum(x[1].values()), reverse=True)
for res_idx, counts in sorted_res[:30]:
    total = sum(counts.values())
    print(f"  R{res_idx}: {total} entries (D={counts['DIALOGUE']}, L={counts['SHORT_LABEL']})")

# Also list NEW resources (not in translated_resources)
new_resources = set(res_counts.keys()) - translated_resources
if new_resources:
    print(f"\n--- NEW resources not in any batch ({len(new_resources)} total) ---")
    for r in sorted(new_resources):
        rc = res_counts[r]
        total = sum(rc.values())
        print(f"  R{r}: {total} entries (D={rc['DIALOGUE']}, L={rc['SHORT_LABEL']})")
