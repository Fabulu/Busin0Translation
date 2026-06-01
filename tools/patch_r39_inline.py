#!/usr/bin/env python3
"""
Patch ALL inline Japanese glyph IDs in R39's extra data section with English equivalents.
Runs AFTER inject_r39_v2.py (reads from build/packdata_resources/0039_type15.raw).

The extra data section (bytes 2702+) contains 559 FFFF-delimited records including:
  - Spell names (records 2-57): katakana spell names
  - Combat skill names (records 117-125)
  - NPC names (records 428-440): katakana NPC names
  - Equipment category labels (records 443-469)
  - Weapon type names (records 470-486)
  - Armor/accessory type names (records 497-510)
  - Body part chip names (records 517-526)

Each record is replaced IN-PLACE: same number of uint16 words.
Shorter English text is padded with 0x0000 (null glyphs).
Longer English text is truncated with a warning.
"""

import struct, json, os, sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

BASE = 'C:/Programmieren/wizardrytranslation'
os.chdir(BASE)

EXTRA_DATA_START = 2702  # bytes 2702+ is the extra data section

# ---------------------------------------------------------------------------
# 1. Load glyph table for English encoding
# ---------------------------------------------------------------------------
glyph_table = json.load(open('data/english_glyph_table.json', encoding='utf-8'))

def char_to_glyph(ch):
    """Convert a single character to its glyph ID."""
    if ch in glyph_table:
        return int(glyph_table[ch])
    if ch.lower() in glyph_table:
        return int(glyph_table[ch.lower()])
    if ch == ' ':
        return 0
    return 31  # '?' fallback

def encode_english(text):
    """Encode English text to a list of BE uint16 glyph IDs."""
    return [char_to_glyph(ch) for ch in text]

# ---------------------------------------------------------------------------
# 2. Define ALL inline text replacements
# ---------------------------------------------------------------------------
# Format: record_index -> English replacement string
# Each record's content (between FFFE and FFFF) will be replaced.
# The replacement must fit within the original content word count.

REPLACEMENTS = {}

# --- Spell names (records 2-57) ---
# These are Wizardry spell names in katakana.
# Slot capacity = number of content glyph words (excluding FFFE, FFFF)
SPELL_NAMES = {
    # Slot count = number of Japanese katakana chars (1 glyph each)
    # English must fit in that many characters
    2:  "Crt",          # クレタ (3 slots) - Creta
    3:  "Crd",          # クルド (3 slots) - Crud
    4:  "Teal",         # ティール (4 slots)
    5:  "Anlyz",        # アナライズ (5 slots) - Analyze
    6:  "Weak",         # ウィーク (4 slots)
    7:  "Dlay",         # ディレイ (4 slots) - Delay
    8:  "Dpt",          # デプス (3 slots) - Depth
    9:  "Febl",         # フィブル (4 slots) - Feeble
    10: "Shrad",        # シュラード (5 slots) - Shrad
    11: "Suprm",        # スプリーム (5 slots) - Supreme
    12: "Slm",          # サロメ (3 slots) - Salome
    13: "Escpe",        # エスケープ (5 slots) - Escape
    14: "ZCrt",         # ザクレタ (4 slots)
    15: "ZCrd",         # ザクルド (4 slots)
    16: "ZTeal",        # ザティール (5 slots)
    17: "Tru",          # スルー (3 slots) - Thru
    18: "ZLrd",         # ザラード (4 slots)
    19: "Drn",          # ドレイン (4 slots) - Drain
    20: "Rpl",          # リピール (4 slots) - Repel
    21: "Canb",         # カニバル (4 slots) - Cannibal
    22: "JCret",        # ジャクレタ (5 slots)
    23: "JCrud",        # ジャクルド (5 slots)
    24: "JTeal",        # ジャティル (5 slots)
    25: "Lat",          # レイト (3 slots) - Late
    26: "JLord",        # ジャラード (5 slots)
    27: "Valhl",        # ヴァルハラ (5 slots) - Valhalla
    28: "Rflct",        # リフレクト (5 slots) - Reflect
    29: "MDth",         # メガデス (4 slots) - MegaDeath
    30: "Feel",         # フィール (4 slots) - Feel
    31: "Rap",          # リープ (3 slots) - Reap
    32: "Valt",         # バレォツ (4 slots) - Valet
    33: "CFire",        # シーファイ (5 slots) - CeaseFire
    34: "Yba",          # ヤイバ (3 slots) - Yaiba
    35: "Cot",          # コート (3 slots) - Coat
    36: "Bls",          # ブレス (3 slots) - Bless
    37: "Prtct",        # プロテクト (5 slots) - Protect
    38: "Amok",         # アモーク (4 slots) - Amok
    39: "Feels",        # フィールズ (5 slots) - Feels
    40: "Pois",         # ポイズン (4 slots) - Poison
    41: "Stran",        # ストレイン (5 slots) - Strain
    42: "PCure",        # ポイズケア (5 slots) - Poison Cure
    43: "ParaC",        # パラズケア (5 slots) - Paralyze Cure
    44: "FearC",        # フィアケア (5 slots) - Fear Cure
    45: "Vitl",         # バイタル (4 slots) - Vital
    46: "Crcs",         # カーカス (4 slots) - Carcass
    47: "Wil",          # ウィル (3 slots) - Will
    48: "Luml",         # リュミル (4 slots) - Lumil
    49: "Undad",        # アンデッド (5 slots) - Undead
    50: "Trns",         # トランス (4 slots) - Trans
    51: "Rcvr",         # リカバー (4 slots) - Recover
    52: "UCurs",        # アンカーズ (5 slots) - Uncurse
    53: "Flot",         # フロート (4 slots) - Float
    54: "Stigm",        # スティグマ (5 slots) - Stigma
    55: "RFeel",        # ラフィール (5 slots) - Re-Feel
    56: "Offst",        # オフセット (5 slots) - Offset
    57: "Reviv",        # リヴィヴ (5 slots) - Revive
}
REPLACEMENTS.update(SPELL_NAMES)

# --- Combat skill names (records 117-125) ---
COMBAT_SKILLS = {
    117: "OK",           # 決定 (2 slots)
    118: "WSlash",       # Wスラッシュ (6 content words)
    119: "StSmash",      # スタンスマッシュ (8 content words)
    120: "HoldAtk",      # ホールドアタック (8 content words)
    121: "SPJAtk",       # S{Jアタック (7 content words, has ASCII prefix)
    122: "SlyCrush",     # スレイクラッシュ (8 content words)
    123: "XCageKil",     # クロスケージキル (8 content words)
    124: "FrtGard",      # フロントガード (7 content words)
    125: "MagcSld",      # マジックシールド (7 content words -- rec has 7 content slots)
}
REPLACEMENTS.update(COMBAT_SKILLS)

# --- NPC names (records 428-440) ---
# These are romanized versions of the katakana NPC names
NPC_NAMES = {
    428: "Vigor",        # ヴィガー + [904][956] (6 content words)
    429: "Mil",          # ミリィ (3 slots)
    430: "Moo",          # モーチ (3 slots)
    431: "Noo",          # ノーチ (3 slots)
    432: "Kunl",         # クンナル (4 slots)
    433: "Melan",        # メラーニエ (5 slots)
    434: "Lid",          # リディ (3 slots)
    435: "Lucy",         # ルーシー (4 slots)
    436: "Yopn",         # ヨーペン (4 slots)
    # 437-440 have kanji mixed in, skip those for safety
}
REPLACEMENTS.update(NPC_NAMES)

# --- Equipment categories (records 453-469) ---
EQUIP_CATEGORIES = {
    453: "Accsry",       # アクセサリー (6 slots)
    458: "Item",         # アイテム (4 slots)
    462: "AutoShop",     # オートマタショップ (9 slots)
    470: "Dgr",          # ダガー (3 slots) - Dagger
    471: "ShrtSwd",      # ショートソード (7 slots)
    472: "LngSwd",       # ロングソード (6 slots)
    473: "GrtSwrd",      # グレートソード (7 slots)
    479: "Mac",          # メイス (3 slots) - Mace
    480: "Flal",         # フレイル (4 slots) - Flail
    481: "ThrowDgr",     # スローイングダガー (9 slots)
    482: "XBow",         # クロスボウ (5 slots) - Crossbow
    483: "LBow",         # ロングボウ (5 slots) - Longbow
    485: "PoleAxe",      # ポールアックス (7 slots)
    486: "Glov",         # グローブ (4 slots) - Glove
    509: "Bot",          # ブーツ (3 slots) - Boots
    510: "Clk",          # マント (3 slots) - Cloak
}
REPLACEMENTS.update(EQUIP_CATEGORIES)

# --- Body part chip names (records 517-526) ---
CHIP_NAMES = {
    517: "HandCp",       # ハンドチップ (6 content words)
    518: "?HndCp",       # ?ハンドチップ (7 content words)
    519: "BodyCp",       # ボディチップ (6 content words)
    520: "?BdyCp",       # ?ボディチップ (7 content words)
    521: "ArmChp",       # アームチップ (6 content words)
    522: "?ArmCp",       # ?アームチップ (7 content words)
    523: "LegChp",       # レッグチップ (6 content words)
    524: "?LgChp",       # ?レッグチップ (7 content words)
    525: "BrnChp",       # ブレインチップ (7 content words)
    526: "?BrnCp",       # ?ブレインチップ (8 content words)
}
REPLACEMENTS.update(CHIP_NAMES)

# --- Weapon sub-type labels with '?' prefix (records 487-496) ---
# These seem to be "unidentified" weapon types
UNID_WEAPONS = {
    493: "?Mac",         # ?メイス (4 content words)
    494: "?Flal",        # ?フレイル (5 content words)
    515: "?Bot",         # ?ブーツ (4 content words)
    516: "?Clk",         # ?マント (4 content words)
}
REPLACEMENTS.update(UNID_WEAPONS)

# ---------------------------------------------------------------------------
# 3. Load the binary (AFTER inject_r39_v2.py has run)
# ---------------------------------------------------------------------------
input_path = 'build/packdata_resources/0039_type15.raw'
if not os.path.exists(input_path):
    print(f"ERROR: {input_path} not found. Run inject_r39_v2.py first.")
    sys.exit(1)

raw = bytearray(open(input_path, 'rb').read())
original_size = len(raw)
# Strip any sector padding to get base size for comparison
base_size = 26624
print(f"R39 loaded: {original_size} bytes (base {base_size})")

# ---------------------------------------------------------------------------
# 4. Parse FFFF-delimited records in the extra data section
# ---------------------------------------------------------------------------
pos = EXTRA_DATA_START
records = []  # list of (start_byte, [(pos, val), ...])
rec_start = pos
current = []

while pos < base_size - 1:
    val = struct.unpack_from('>H', raw, pos)[0]
    current.append((pos, val))
    if val == 0xFFFF:
        records.append((rec_start, current[:]))
        current = []
        rec_start = pos + 2
    pos += 2

if current:
    records.append((rec_start, current[:]))

print(f"Parsed {len(records)} FFFF-delimited records in extra data")

# ---------------------------------------------------------------------------
# 5. Apply replacements
# ---------------------------------------------------------------------------
out = bytearray(raw)
replaced = 0
truncated = 0
skipped = 0

for rec_idx, english_text in sorted(REPLACEMENTS.items()):
    if rec_idx >= len(records):
        print(f"  WARNING: Record {rec_idx} out of range (max {len(records)-1}), skipping")
        skipped += 1
        continue

    rec_start, entries = records[rec_idx]

    # Find content positions: everything except FFFE and FFFF
    content_positions = []
    for byte_pos, val in entries:
        if val == 0xFFFF or val == 0xFFFE:
            continue
        content_positions.append(byte_pos)

    if not content_positions:
        print(f"  WARNING: Record {rec_idx} has no content, skipping")
        skipped += 1
        continue

    capacity = len(content_positions)  # number of uint16 word slots
    en_glyphs = encode_english(english_text)

    if len(en_glyphs) > capacity:
        print(f"  WARNING: Record {rec_idx} truncated: '{english_text}' "
              f"({len(en_glyphs)} glyphs) -> {capacity} slots")
        en_glyphs = en_glyphs[:capacity]
        truncated += 1

    # Write English glyphs into the content positions
    for i, byte_pos in enumerate(content_positions):
        if i < len(en_glyphs):
            struct.pack_into('>H', out, byte_pos, en_glyphs[i])
        else:
            # Pad remaining slots with 0x0000
            struct.pack_into('>H', out, byte_pos, 0x0000)

    replaced += 1

print(f"\nReplaced {replaced} records ({truncated} truncated, {skipped} skipped)")

# ---------------------------------------------------------------------------
# 6. Sanity checks
# ---------------------------------------------------------------------------
# Verify FFFF delimiter count is unchanged
orig_ffff = 0
new_ffff = 0
for i in range(EXTRA_DATA_START, base_size - 1, 2):
    if struct.unpack_from('>H', raw, i)[0] == 0xFFFF:
        orig_ffff += 1
    if struct.unpack_from('>H', out, i)[0] == 0xFFFF:
        new_ffff += 1

assert orig_ffff == new_ffff, f"FFFF count changed! {orig_ffff} -> {new_ffff}"

# Verify FFFE delimiter count is unchanged
orig_fffe = 0
new_fffe = 0
for i in range(EXTRA_DATA_START, base_size - 1, 2):
    if struct.unpack_from('>H', raw, i)[0] == 0xFFFE:
        orig_fffe += 1
    if struct.unpack_from('>H', out, i)[0] == 0xFFFE:
        new_fffe += 1

assert orig_fffe == new_fffe, f"FFFE count changed! {orig_fffe} -> {new_fffe}"

# Verify bytes before extra data are unchanged
assert out[:EXTRA_DATA_START] == raw[:EXTRA_DATA_START], \
    "Pre-extra-data bytes changed!"

print(f"Sanity checks passed: {orig_ffff} FFFFx, {orig_fffe} FFFEx preserved")

# ---------------------------------------------------------------------------
# 7. Write back (preserving sector padding)
# ---------------------------------------------------------------------------
output = bytes(out)
with open(input_path, 'wb') as f:
    f.write(output)
print(f"Written {len(output)} bytes to {input_path}")
print("R39 inline patch complete")
