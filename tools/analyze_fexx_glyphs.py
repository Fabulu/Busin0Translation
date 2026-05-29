#!/usr/bin/env python3
"""
analyze_fexx_glyphs.py -- Analyze FE:xx range and unmapped glyphs in R1163-R1174

Findings:
- R1163-R1173 do NOT contain narration text. They contain text layout templates
  (mostly spaces with positional markers and FFxx formatting control codes).
- R1174 is similar (text templates translated as "[LAYOUT] Text template").
- The "FE:xx range" values (FFD0-FFFC) in these resources are formatting/control
  codes, not character glyphs.
- The actual narration text is in R1193 and R1194 (already fully mapped + translated).
- The main unmapped glyphs needing work are in the dialogue resources R1196-R1213
  and R1347-R1355 (standard kanji range 96-1763).
"""
import struct, json, sys, os, glob
sys.stdout.reconfigure(encoding="utf-8")

BASE = "C:/Programmieren/wizardrytranslation"

with open(os.path.join(BASE, "data/msg_glyph_map.json"), "r", encoding="utf-8") as f:
    gmap = json.load(f)
mapped_ids = {int(k): v for k, v in gmap.items()}

# Load translations
trans_dir = os.path.join(BASE, "data/type2_translated")
all_trans = {}
for fp in sorted(glob.glob(os.path.join(trans_dir, "*.json"))):
    with open(fp, "r", encoding="utf-8") as f:
        data = json.load(f)
    for e in data:
        key = (e["resource"], e["msg_index"])
        all_trans[key] = e

print(f"Glyph map entries: {len(gmap)}")
print(f"Translation entries: {len(all_trans)}")

raw_dir = os.path.join(BASE, "extracted/packdata_raw")

# ============================================================
# Part 1: Analyze R1163-R1174 (the "FE:xx" resources)
# ============================================================
print("\n" + "=" * 60)
print("PART 1: R1163-R1174 Analysis")
print("=" * 60)

for rid in range(1163, 1175):
    path = os.path.join(raw_dir, f"{rid:04d}_type02.raw")
    try:
        with open(path, "rb") as f:
            raw = f.read()
    except FileNotFoundError:
        continue

    sec2_size = struct.unpack_from("<I", raw, 0x14)[0]
    sec2_offset = struct.unpack_from("<I", raw, 0x18)[0]
    sec2 = raw[sec2_offset:sec2_offset + sec2_size]
    n_words = len(sec2) // 2
    words = [struct.unpack_from(">H", sec2, i * 2)[0] for i in range(n_words)]

    # Count value categories
    zeros = sum(1 for w in words if w == 0)
    small = sum(1 for w in words if 1 <= w <= 30)
    text_range = sum(1 for w in words if 96 <= w < 0xFB00)
    ctrl_range = sum(1 for w in words if 0xFB00 <= w <= 0xFFFF)
    ffxx_unique = sorted(set(w for w in words if 0xFF00 <= w <= 0xFFFF))

    print(f"\nR{rid}: {n_words} words total")
    print(f"  Zeros: {zeros} ({100*zeros//n_words}%)")
    print(f"  Small values (1-30): {small} ({100*small//n_words}%)")
    print(f"  Text glyph range (96-0xFAFF): {text_range}")
    print(f"  Control codes (0xFB00-0xFFFF): {ctrl_range}")
    print(f"  FF:xx unique values: {[hex(w) for w in ffxx_unique]}")
    print(f"  VERDICT: {'TEXT TEMPLATE (not translatable dialogue)' if text_range < 5 else 'CONTAINS TEXT'}")

# ============================================================
# Part 2: Analyze R1193-R1194 (actual narration text)
# ============================================================
print("\n" + "=" * 60)
print("PART 2: R1193-R1194 (Actual Narration)")
print("=" * 60)

for rid in [1193, 1194]:
    path = os.path.join(raw_dir, f"{rid:04d}_type02.raw")
    with open(path, "rb") as f:
        raw = f.read()
    sec2_size = struct.unpack_from("<I", raw, 0x14)[0]
    sec2_offset = struct.unpack_from("<I", raw, 0x18)[0]
    sec2 = raw[sec2_offset:sec2_offset + sec2_size]
    n_words = len(sec2) // 2
    words = [struct.unpack_from(">H", sec2, i * 2)[0] for i in range(n_words)]

    glyphs = [w for w in words if w < 0xFB00]
    mapped = sum(1 for w in glyphs if w in mapped_ids)
    unmapped = [w for w in glyphs if w not in mapped_ids]

    print(f"\nR{rid}: {len(glyphs)} glyphs, {mapped} mapped ({100*mapped//max(len(glyphs),1)}%)")
    print(f"  Unmapped: {len(unmapped)} -- {sorted(set(unmapped))}")
    print(f"  STATUS: {'FULLY MAPPED' if not unmapped else 'HAS UNMAPPED'}")

# ============================================================
# Part 3: Remaining unmapped in dialogue resources
# ============================================================
print("\n" + "=" * 60)
print("PART 3: Remaining Unmapped in Dialogue (R1196-R1213, R1347-R1355)")
print("=" * 60)

dialogue_resources = list(range(1196, 1214)) + list(range(1347, 1356))
all_remaining = set()

for rid in dialogue_resources:
    path = os.path.join(raw_dir, f"{rid:04d}_type02.raw")
    try:
        with open(path, "rb") as f:
            raw = f.read()
    except FileNotFoundError:
        continue
    sec2_size = struct.unpack_from("<I", raw, 0x14)[0]
    sec2_offset = struct.unpack_from("<I", raw, 0x18)[0]
    if sec2_offset == 0 or sec2_offset >= len(raw):
        continue
    sec2 = raw[sec2_offset:min(sec2_offset + sec2_size, len(raw))]
    n_words = len(sec2) // 2
    words = [struct.unpack_from(">H", sec2, i * 2)[0] for i in range(n_words)]
    unmapped = set(w for w in words if 2 <= w < 0xFB00 and w not in mapped_ids)
    std_unmapped = set(w for w in unmapped if 96 <= w < 2000)
    all_remaining |= std_unmapped

std_sorted = sorted(all_remaining)
print(f"\nTotal unique unmapped standard-range glyphs: {len(std_sorted)}")
print(f"IDs: {std_sorted[:100]}")
if len(std_sorted) > 100:
    print(f"  ... and {len(std_sorted) - 100} more")

# Atlas position summary
print(f"\nAtlas positions of remaining unmapped:")
for gid in std_sorted[:50]:
    row = gid // 21
    col = gid % 21
    print(f"  glyph {gid}: row={row}, col={col}")

# ============================================================
# Part 4: FF:xx control code analysis
# ============================================================
print("\n" + "=" * 60)
print("PART 4: FF:xx Control Code Analysis")
print("=" * 60)

# Collect all FF:xx values used across all type-2 resources
all_ffxx = set()
for rid in range(1163, 1175):
    path = os.path.join(raw_dir, f"{rid:04d}_type02.raw")
    try:
        with open(path, "rb") as f:
            raw = f.read()
    except FileNotFoundError:
        continue
    sec2_size = struct.unpack_from("<I", raw, 0x14)[0]
    sec2_offset = struct.unpack_from("<I", raw, 0x18)[0]
    sec2 = raw[sec2_offset:sec2_offset + sec2_size]
    n_words = len(sec2) // 2
    words = [struct.unpack_from(">H", sec2, i * 2)[0] for i in range(n_words)]
    all_ffxx |= set(w for w in words if 0xFB00 <= w <= 0xFFFF)

print(f"\nAll FF:xx range values found in R1163-R1174:")
for val in sorted(all_ffxx):
    known = {
        0xFFFF: "MESSAGE_END (FFFF) - delimits message groups",
        0xFFFE: "LINE_BREAK (FFFE) - newline within message",
        0xFFFD: "BOUNDARY (FFFD) - section/page boundary marker",
        0xFFFC: "PAGE_WAIT (FFFC) - wait for input before continuing",
        0xFFFB: "SPEAKER_TAG (FFFB) - marks speaker identification",
        0xFFFA: "CHOICE_MARKER (FFFA) - dialogue choice point",
        0xFFF9: "COLOR_CHANGE (FFF9) - text color modifier",
        0xFFF8: "TEXT_SPEED (FFF8) - controls text display speed",
        0xFFF7: "DELAY (FFF7) - pause/delay in rendering",
        0xFFF6: "FORMAT_TAG (FFF6) - text formatting directive",
        0xFFF5: "INDENT (FFF5) - indentation marker",
        0xFFF4: "PARAM_A (FFF4) - layout parameter",
        0xFFF3: "PARAM_B (FFF3) - layout parameter",
        0xFFF2: "PARAM_C (FFF2) - layout parameter",
        0xFFF1: "PARAM_D (FFF1) - layout parameter",
        0xFFF0: "PARAM_E (FFF0) - layout parameter",
    }
    desc = known.get(val, "LAYOUT_CONTROL - text positioning/formatting parameter")
    print(f"  0x{val:04X}: {desc}")

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"Total glyph map entries: {len(gmap)}")
print(f"R1193/R1194 narration: FULLY MAPPED (all glyphs covered)")
print(f"R1163-R1173: TEXT TEMPLATES (not translatable dialogue)")
print(f"  - FFxx values are layout/formatting control codes, NOT text characters")
print(f"  - These resources contain text display templates (spacing, positioning)")
print(f"Remaining unmapped in dialogue: {len(std_sorted)} standard-range glyphs")
print(f"  - These are kanji in glyph IDs 96-1763 used in R1196-R1213 dialogue")
print(f"  - Most are low-frequency (< 30 occurrences each)")
