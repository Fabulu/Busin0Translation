#!/usr/bin/env python3
"""
Deep analysis of key EXE regions containing Japanese glyph IDs.
Focuses on the regions identified as genuine text/label tables.
"""
import json, struct, sys

sys.stdout.reconfigure(encoding='utf-8')

EXE_PATH = "C:/Programmieren/wizardrytranslation/extracted/SLPM_653.78"
GLYPH_MAP_PATH = "C:/Programmieren/wizardrytranslation/data/msg_glyph_map.json"
OUT_PATH = "C:/Programmieren/wizardrytranslation/runs/CLAUDE-RUNS/RUN-20260528-remaining-japanese/exe_glyph_scan.md"

def main():
    glyph_map = json.load(open(GLYPH_MAP_PATH, 'r', encoding='utf-8'))
    with open(EXE_PATH, 'rb') as f:
        exe = f.read()

    def decode(val):
        if val == 0: return '\u00B7'
        if 1 <= val <= 94: return chr(val + 0x20)
        ch = glyph_map.get(str(val))
        return ch if ch else f'[?{val}]'

    def is_kanji(val):
        return 95 <= val <= 881 and str(val) in glyph_map

    findings = []

    # ===================================================================
    # REGION A: 0x3B3226-0x3B368A - Glyph charset ordering table
    # This is a lookup table that maps character positions in the font atlas.
    # Contains ALL hiragana, katakana, and kanji glyph IDs in order.
    # This is NOT user-visible text - it's the font ordering table.
    # VERDICT: NOT a translation target (font infrastructure)
    # ===================================================================
    findings.append({
        'region': 'A',
        'offset': '0x3B3226-0x3B368A',
        'size': 0x3B368A - 0x3B3226,
        'description': 'Font glyph charset ordering table',
        'action': 'NO ACTION NEEDED - font infrastructure, not displayed text',
        'decoded': 'Full hiragana + katakana + kanji glyph ordering (544 entries)',
    })

    # ===================================================================
    # REGION B: 0x3B36A0-0x3B3752 - UI label glyph IDs
    # Contains: 遺/王/噂/彼/対/無, then compound words:
    # 光/冒険/広/刻/息/登録/開帰/専所/出/新兵/召喚/能力/職/削除/隊/前/性
    # These look like menu option glyph ID arrays for rendering UI labels.
    # ===================================================================
    print("\n=== REGION B: UI Label Glyph Arrays ===")
    print("0x3B36A0-0x3B3752")

    # Dump with structure analysis - these seem to be pairs (glyph, glyph)
    for i in range(0x3B3690, 0x3B3760, 2):
        val = struct.unpack_from('<H', exe, i)[0]
        if is_kanji(val):
            ch = decode(val)
            print(f"  0x{i:06X}: {val:5d} = {ch}")

    # ===================================================================
    # REGION C: 0x3B376A-0x3B3838 - Glyph index tables
    # Two sub-tables:
    # 1. Hiragana indices: あけちのむるぐだべゅ (10 chars)
    # 2. Mixed katakana+kanji: クチノムルグダベュヴ使悪士飲開頼賊中邪暗然見店地半侍願直約質大主
    # 3. More kanji: 刻出地種飽交間消屋色嫌受費属方箱看求突血高誰元体解街命可足幸聖美高器形内回失打先巨嘆護声穏空組草携札
    # ===================================================================
    print("\n=== REGION C: Glyph Index Tables ===")
    print("0x3B376A-0x3B3838")

    # Sub-table 1: 10 hiragana
    sub1_start = 0x3B376C
    sub1 = []
    for i in range(sub1_start, sub1_start + 20, 2):
        val = struct.unpack_from('<H', exe, i)[0]
        sub1.append(decode(val))
    print(f"  Sub-table 1 (hiragana indices): {''.join(sub1)}")

    # Sub-table 2: katakana+kanji
    sub2_start = 0x3B3782
    sub2 = []
    for i in range(sub2_start, sub2_start + 70, 2):
        val = struct.unpack_from('<H', exe, i)[0]
        if val == 0:
            break
        sub2.append(decode(val))
    print(f"  Sub-table 2 (katakana+kanji): {''.join(sub2)}")

    # Sub-table 3: more kanji
    sub3_start = 0x3B37CA
    sub3 = []
    for i in range(sub3_start, sub3_start + 200, 2):
        val = struct.unpack_from('<H', exe, i)[0]
        if val == 0 or not is_kanji(val):
            if val == 0:
                break
            continue
        sub3.append(decode(val))
    print(f"  Sub-table 3 (more kanji): {''.join(sub3)}")

    findings.append({
        'region': 'C',
        'offset': '0x3B376A-0x3B3838',
        'size': 0x3B3838 - 0x3B376A,
        'description': 'Glyph index tables for UI rendering',
        'action': 'INVESTIGATE - may be lookup tables for menu/UI glyph rendering',
        'decoded': 'Hiragana indices + katakana/kanji character sets',
    })

    # ===================================================================
    # REGION D: 0x3B3DAE-0x3B3E90 - String index tables
    # Contains glyph IDs that look like indices into string arrays.
    # Pattern: sequential glyph IDs used as lookup keys.
    # Sub-tables contain game vocabulary: 祠使鎧大魔忍武力言中悔除外両苦転地報頼封復
    # 紹大記会横辺王 / 広専能隊性怪交代仲追与己嫌同前度少品思看
    # ===================================================================
    print("\n=== REGION D: String Index/Hash Tables ===")
    print("0x3B3DAE-0x3B3E90")

    # Dump in 2-byte units showing structure
    for base in [0x3B3DAE, 0x3B3E0A, 0x3B3E1A, 0x3B3E44, 0x3B3E84]:
        chars = []
        for i in range(base, base + 80, 2):
            if i >= 0x3B3E90:
                break
            val = struct.unpack_from('<H', exe, i)[0]
            if val == 0:
                break
            if is_kanji(val):
                chars.append(decode(val))
            else:
                chars.append(f'({val})')
        text = ''.join(chars)
        print(f"  0x{base:06X}: {text}")

    findings.append({
        'region': 'D',
        'offset': '0x3B3DAE-0x3B3E90',
        'size': 0x3B3E90 - 0x3B3DAE,
        'description': 'String index/hash tables with game vocabulary',
        'action': 'INVESTIGATE - indices referencing game terms, may need translation if displayed',
        'decoded': 'Game vocabulary indices (stats, classes, items, abilities)',
    })

    # ===================================================================
    # REGION E: 0x3B5FC0-0x3B6136 - Katakana/Hiragana sort order table
    # This appears to be a character sorting/mapping table for the full
    # kana charset. Not user-visible text.
    # VERDICT: NOT a translation target (sorting infrastructure)
    # ===================================================================
    findings.append({
        'region': 'E',
        'offset': '0x3B5FC0-0x3B6136',
        'size': 0x3B6136 - 0x3B5FC0,
        'description': 'Kana sort order / character mapping table',
        'action': 'NO ACTION NEEDED - sorting infrastructure',
        'decoded': 'Full kana character set in sort order',
    })

    # ===================================================================
    # REGION F: 0x3C5F00-0x3C6700 - Name entry keyboard grids
    # ===================================================================
    print("\n=== REGION F: Name Entry Keyboard Grids ===")
    print("0x3C5F00-0x3C6700")

    # Look for the keyboard layout structure
    # The chargen grid at 0x3C83C0 is handled, but these earlier grids
    # might be the actual keyboard input grids
    for grid_start in [0x3C5F1E, 0x3C65D8]:
        print(f"\n  Grid starting 0x{grid_start:06X}:")
        for row in range(10):
            chars = []
            for col in range(5):
                off = grid_start + (row * 5 + col) * 6  # 6 bytes per entry?
                if off + 2 > len(exe):
                    break
                val = struct.unpack_from('<H', exe, off)[0]
                chars.append(decode(val))
            print(f"    Row {row}: {'  '.join(chars)}")

    findings.append({
        'region': 'F',
        'offset': '0x3C5F00-0x3C6700',
        'size': 0x6700 - 0x5F00,
        'description': 'Name entry keyboard grids (hiragana/katakana input)',
        'action': 'NEEDS TRANSLATION - keyboard grid labels if replacing with English input',
        'decoded': 'Hiragana/katakana input grids for character naming',
    })

    # ===================================================================
    # REGION G: 0x3C8180-0x3C83C0 - Pre-chargen data
    # Additional character grid data before the main chargen grid
    # ===================================================================
    print("\n=== REGION G: Pre-chargen Data ===")
    print("0x3C81E0-0x3C83C0")

    # This looks like another set of character grids
    for i in range(0x3C81E0, 0x3C83C0, 2):
        val = struct.unpack_from('<H', exe, i)[0]
        if is_kanji(val):
            print(f"  0x{i:06X}: {val:4d} = {decode(val)}")

    findings.append({
        'region': 'G',
        'offset': '0x3C8180-0x3C83C0',
        'size': 0x83C0 - 0x8180,
        'description': 'Pre-chargen character grid data',
        'action': 'LIKELY HANDLED with chargen grid (R38) - verify',
        'decoded': 'Additional kana character grid entries',
    })

    # ===================================================================
    # REGION H: 0x3C9A34-0x3C9D54 - POST-CHARGEN VOCABULARY TABLE
    # *** THIS IS THE MOST IMPORTANT FIND ***
    # Structured records containing game vocabulary:
    # - Katakana class/race names
    # - Kanji compound words for game concepts
    # - Appears to be a string table for game labels
    # ===================================================================
    print("\n=== REGION H: Post-chargen Vocabulary Table (KEY FIND) ===")
    print("0x3C9A34-0x3C9D54")

    # Analyze the structure: records seem to be 16 bytes with pattern:
    # [index_byte] [hiragana] [katakana] [kanji1] [kanji2] [kanji3] ... [padding]
    # Let's dump systematically

    print("\n  Record analysis (10-byte stride):")
    for i in range(0x3C9A34, 0x3C9D54, 10):
        vals = []
        for j in range(0, 10, 2):
            if i + j + 2 > len(exe):
                break
            v = struct.unpack_from('<H', exe, i + j)[0]
            vals.append(v)
        text = ''.join(decode(v) for v in vals)
        kanji_text = ''.join(decode(v) for v in vals if is_kanji(v))
        if any(is_kanji(v) for v in vals):
            print(f"  0x{i:06X}: {text:20s}  kanji={kanji_text}")

    findings.append({
        'region': 'H',
        'offset': '0x3C9A34-0x3C9D54',
        'size': 0x3C9D54 - 0x3C9A34,
        'description': 'Game vocabulary/label table - MAIN TRANSLATION TARGET',
        'action': 'NEEDS TRANSLATION - game term labels (stats, classes, items, combat, status)',
        'decoded': 'Comprehensive game vocabulary: stats, classes, races, items, combat terms, status effects',
    })

    # ===================================================================
    # REGION I: 0x3DDC40-0x3DE0D6 - Struct with 族/下/難 patterns
    # Repeated "ブ族下下難難難難" pattern - likely struct templates
    # ===================================================================
    print("\n=== REGION I: Repeated struct patterns ===")
    print("0x3DDC40-0x3DE0D6")

    for base in [0x3DDC40, 0x3DDD40, 0x3DDE40, 0x3DDF40]:
        vals = [struct.unpack_from('<H', exe, base + j)[0] for j in range(0, 16, 2)]
        text = ''.join(decode(v) for v in vals)
        hex_str = ' '.join(f'{v:04X}' for v in vals)
        print(f"  0x{base:06X}: {text}  hex: {hex_str}")

    # These glyph IDs might be coincidental - let's check if the raw values
    # make sense as something else
    for base in [0x3DDC40]:
        raw = exe[base:base+16]
        print(f"\n  Raw bytes: {raw.hex(' ')}")
        # As uint32s:
        u32s = [struct.unpack_from('<I', raw, j)[0] for j in range(0, 16, 4)]
        print(f"  As uint32: {[f'0x{v:08X}' for v in u32s]}")
        # As float32s:
        f32s = [struct.unpack_from('<f', raw, j)[0] for j in range(0, 16, 4)]
        print(f"  As float32: {f32s}")

    findings.append({
        'region': 'I',
        'offset': '0x3DDC40-0x3DE0D6',
        'size': 0x3DE0D6 - 0x3DDC40,
        'description': 'Repeated struct patterns with 族/下/難',
        'action': 'LIKELY FALSE POSITIVE - struct data that coincidentally maps to glyph range',
        'decoded': 'ブ族下下難難難難 (repeated 4x) + ベ*10 + 族*10',
    })

    # ===================================================================
    # REGION J: 0x3DEFA2-0x3DEFBC - Character creation flags?
    # Contains: 男下帰性必, 男下全呪, 難下
    # ===================================================================
    print("\n=== REGION J: Character creation data ===")
    print("0x3DEFA2-0x3DEFBC")

    for i in range(0x3DEF90, 0x3DEFC0, 2):
        val = struct.unpack_from('<H', exe, i)[0]
        if is_kanji(val):
            print(f"  0x{i:06X}: {val:4d} = {decode(val)}")
        elif val != 0 and val <= 0xFFFF:
            if val < 1000:
                print(f"  0x{i:06X}: {val:4d} = {decode(val)}")

    findings.append({
        'region': 'J',
        'offset': '0x3DEFA2-0x3DEFBC',
        'size': 0x3DEFBC - 0x3DEFA2,
        'description': 'Character creation flags/data',
        'action': 'INVESTIGATE - contains 男/女/性/呪/難 possibly gender/difficulty labels',
        'decoded': '男下帰性必 / 男下全呪 / 難下',
    })

    # ===================================================================
    # REGION K: 0x3BF0FE-0x3BF250 - Misc isolated kanji in code section
    # ===================================================================
    print("\n=== REGION K: Isolated kanji clusters in code section ===")
    for base, size in [(0x3BF0F0, 0x60), (0x3BD6F0, 0x20)]:
        print(f"\n  0x{base:06X}:")
        for i in range(base, base + size, 2):
            val = struct.unpack_from('<H', exe, i)[0]
            if is_kanji(val):
                print(f"    0x{i:06X}: {val:4d} = {decode(val)}")

    # ===================================================================
    # CODE SECTION PATTERNS (0x3B8000-0x3BD000)
    # The "ブブ" pattern at regular intervals in code section
    # These are MIPS assembly: val 0x0267 = glyph ブ, but as MIPS instruction
    # this is likely part of branch/load instructions.
    # VERDICT: FALSE POSITIVES - MIPS code coincidence
    # ===================================================================
    findings.append({
        'region': 'CODE',
        'offset': '0x3B8000-0x3BD000',
        'size': 0x5000,
        'description': 'MIPS code section with coincidental glyph-range values',
        'action': 'NO ACTION NEEDED - false positives from MIPS instruction encoding',
        'decoded': 'ブブ patterns = MIPS instructions, not text',
    })

    # Now write the final report
    write_final_report(findings)
    print(f"\n\nFinal report written to {OUT_PATH}")


def write_final_report(findings):
    with open(OUT_PATH, 'w', encoding='utf-8') as f:
        f.write("# EXE Remaining Japanese Glyph Scan - Final Report\n\n")
        f.write("**Date:** 2026-05-28\n")
        f.write("**EXE:** extracted/SLPM_653.78\n")
        f.write("**Scan range:** 0x3B0000 - 0x3FD000 (data section)\n\n")

        f.write("## Already Handled Regions\n\n")
        f.write("| Region | Offset | Description |\n")
        f.write("|--------|--------|-------------|\n")
        f.write("| Menu structs | `0x3C3000`-`0x3C5300` | Menu tile replacement (done) |\n")
        f.write("| Chargen grid | `0x3C83C0`-`0x3C93A0` | Character creation grid (R38, done) |\n")
        f.write("| Tab labels | `0x3C9DA0`-`0x3C9DFC` | Name entry tab IDs (Table 2E, done) |\n")
        f.write("\n---\n\n")

        f.write("## Scan Results Summary\n\n")

        # Categorize findings
        needs_translation = [f for f in findings if 'NEEDS TRANSLATION' in f['action']]
        investigate = [f for f in findings if 'INVESTIGATE' in f['action']]
        no_action = [f for f in findings if 'NO ACTION' in f['action'] or 'FALSE' in f['action']]
        handled = [f for f in findings if 'HANDLED' in f['action']]

        f.write(f"- **Needs translation:** {len(needs_translation)} region(s)\n")
        f.write(f"- **Needs investigation:** {len(investigate)} region(s)\n")
        f.write(f"- **No action needed:** {len(no_action)} region(s) (false positives / infrastructure)\n")
        f.write(f"- **Likely already handled:** {len(handled)} region(s)\n\n")

        f.write("---\n\n")

        # Detail each category
        f.write("## NEEDS TRANSLATION\n\n")
        for fi in needs_translation:
            f.write(f"### Region {fi['region']}: {fi['offset']}\n\n")
            f.write(f"- **Size:** {fi['size']} bytes\n")
            f.write(f"- **Description:** {fi['description']}\n")
            f.write(f"- **Content:** {fi['decoded']}\n")
            f.write(f"- **Action:** {fi['action']}\n\n")

        f.write("## NEEDS INVESTIGATION\n\n")
        for fi in investigate:
            f.write(f"### Region {fi['region']}: {fi['offset']}\n\n")
            f.write(f"- **Size:** {fi['size']} bytes\n")
            f.write(f"- **Description:** {fi['description']}\n")
            f.write(f"- **Content:** {fi['decoded']}\n")
            f.write(f"- **Action:** {fi['action']}\n\n")

        f.write("## NO ACTION NEEDED (False Positives / Infrastructure)\n\n")
        for fi in no_action + handled:
            f.write(f"### Region {fi['region']}: {fi['offset']}\n\n")
            f.write(f"- **Size:** {fi['size']} bytes\n")
            f.write(f"- **Description:** {fi['description']}\n")
            f.write(f"- **Action:** {fi['action']}\n\n")

        f.write("---\n\n")
        f.write("## Priority Action Items\n\n")
        f.write("1. **[HIGH] Region H (0x3C9A34-0x3C9D54):** Post-chargen vocabulary table.\n")
        f.write("   Contains ~760 bytes of structured game vocabulary records.\n")
        f.write("   Includes stat names, class names, race names, item types, combat terms,\n")
        f.write("   status effects, and other core game labels. This is the primary remaining\n")
        f.write("   Japanese glyph reference that needs English replacement.\n\n")
        f.write("2. **[MEDIUM] Region F (0x3C5F00-0x3C6700):** Name entry keyboard grids.\n")
        f.write("   Hiragana/katakana input grids for character naming. If the name entry\n")
        f.write("   system is being replaced with English input, these need updating.\n\n")
        f.write("3. **[MEDIUM] Region C (0x3B376A-0x3B3838):** UI label glyph index tables.\n")
        f.write("   Contains glyph IDs used to render menu/UI labels. May already be\n")
        f.write("   handled by menu struct replacement, but should be verified.\n\n")
        f.write("4. **[LOW] Region D (0x3B3DAE-0x3B3E90):** String index tables.\n")
        f.write("   Game vocabulary indices - may be internal lookup tables rather than\n")
        f.write("   directly displayed text. Investigate whether these are read by the\n")
        f.write("   rendering code.\n\n")
        f.write("5. **[LOW] Region J (0x3DEFA2-0x3DEFBC):** Character creation flags.\n")
        f.write("   Contains gender/difficulty labels. Small region, may be struct data.\n\n")


if __name__ == '__main__':
    main()
