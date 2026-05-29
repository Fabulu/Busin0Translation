#!/usr/bin/env python3
"""
Targeted scan of EXE for Japanese glyph tables.
Focus on regions with real text content, not code coincidences.
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

    def decode_glyph(val):
        if val == 0:
            return '\u00B7'
        if 1 <= val <= 94:
            return chr(val + 0x20)
        ch = glyph_map.get(str(val))
        return ch if ch else f'[?{val}]'

    def is_kanji(val):
        return 95 <= val <= 881 and str(val) in glyph_map

    def dump_uint16_table(start, end, label, stride=None):
        """Dump a region as uint16 glyph IDs."""
        print(f"\n{'='*70}")
        print(f"Region: {label}")
        print(f"Offset: 0x{start:06X} - 0x{end:06X} ({end-start} bytes)")
        print(f"{'='*70}")

        data = exe[start:end]
        if stride:
            # Read as structured records
            for rec_idx in range(0, len(data), stride):
                rec = data[rec_idx:rec_idx+stride]
                if len(rec) < stride:
                    break
                offset = start + rec_idx
                # decode all uint16s in record
                vals = [struct.unpack_from('<H', rec, i)[0] for i in range(0, len(rec)-1, 2)]
                text_parts = []
                kanji_count = 0
                for v in vals:
                    if is_kanji(v):
                        kanji_count += 1
                    text_parts.append(decode_glyph(v))
                text = ''.join(text_parts)
                if kanji_count >= 1:
                    print(f"  0x{offset:06X} [{rec_idx//stride:3d}]: {text}  (k={kanji_count})")
        else:
            # Dump as flat uint16 stream
            kanji_runs = []
            current_run = []
            for i in range(0, len(data)-1, 2):
                val = struct.unpack_from('<H', data, i)[0]
                if is_kanji(val):
                    current_run.append((start+i, val))
                else:
                    if len(current_run) >= 2:
                        kanji_runs.append(current_run)
                    current_run = []
            if len(current_run) >= 2:
                kanji_runs.append(current_run)

            for run in kanji_runs:
                text = ''.join(decode_glyph(v) for _, v in run)
                print(f"  0x{run[0][0]:06X}: {text}")

        return

    # ===== REGION 1: Font/glyph ordering table at 0x3B3226 =====
    # This is likely the glyph ordering table (hiragana, katakana, kanji order)
    # 544 consecutive kanji glyphs - this is the full charset listing
    print("\n" + "#"*70)
    print("# ANALYSIS: Consecutive glyph regions in EXE")
    print("#"*70)

    dump_uint16_table(0x3B3226, 0x3B368A, "Full glyph charset table (glyph ordering)")

    # ===== REGION 2: String table at 0x3B36A0-0x3B3838 =====
    # Contains words like 冒険, 登録, 開帰, 新兵, 召喚, 能力, 職, 削除, 隊, 性
    # These look like UI string labels - let's see the structure
    print("\n")
    dump_uint16_table(0x3B3690, 0x3B3840, "UI string labels (code section)")

    # ===== REGION 3: Mixed table at 0x3B3DAE-0x3B3E82 =====
    # Contains stat-related and class/ability labels
    dump_uint16_table(0x3B3DA0, 0x3B3E90, "Stat/class label indices")

    # ===== REGION 4: Hiragana keyboard grids at 0x3C5F-0x3C67 =====
    # These are the name-entry keyboard character grids
    dump_uint16_table(0x3C5F00, 0x3C6700, "Name entry keyboard grids", stride=None)

    # ===== REGION 5: Pre-chargen glyph tables at 0x3C8200-0x3C83C0 =====
    dump_uint16_table(0x3C8180, 0x3C83C0, "Pre-chargen glyph data")

    # ===== REGION 6: Post-chargen vocabulary at 0x3C9A34-0x3C9D52 =====
    # This contains real game vocabulary in a structured format
    dump_uint16_table(0x3C9A00, 0x3C9E00, "Post-chargen vocabulary table")

    # ===== REGION 7: Late data 0x3DDC00-0x3DE100 =====
    dump_uint16_table(0x3DDC00, 0x3DE100, "Late data - repeating patterns")

    # ===== REGION 8: 0x3DEFA0-0x3DF020 =====
    dump_uint16_table(0x3DEF90, 0x3DF030, "Character creation related")

    # Now do a comprehensive scan for structured text tables
    # Look for arrays of fixed-length records containing glyph IDs
    print("\n" + "#"*70)
    print("# STRUCTURED TABLE SCAN")
    print("# Looking for arrays of fixed-stride records with kanji")
    print("#"*70)

    find_structured_tables(exe, glyph_map)


def find_structured_tables(exe, glyph_map):
    """Find structured tables: fixed-stride arrays where each record has kanji."""
    SCAN_START = 0x3B0000
    SCAN_END = 0x3FD000

    # Skip known regions
    SKIP = [
        (0x3C3000, 0x3C5300),  # menu structs
        (0x3C83C0, 0x3C93A0),  # chargen grid
        (0x3C9DA0, 0x3C9DFC),  # tab IDs
    ]

    def in_skip(off):
        return any(s <= off < e for s, e in SKIP)

    def is_kanji(val):
        return 95 <= val <= 881 and str(val) in glyph_map

    def decode(val):
        if val == 0: return '\u00B7'
        if 1 <= val <= 94: return chr(val + 0x20)
        ch = glyph_map.get(str(val))
        return ch if ch else f'[?{val}]'

    # Strategy: for each position, read N consecutive uint16s
    # and check if most are valid glyphs with some kanji
    # A "text field" should have 4+ consecutive valid glyphs, >= 50% kanji

    # Scan for "dense kanji windows" - 8-byte windows with 3+ kanji uint16s
    dense_windows = []
    data = exe[SCAN_START:SCAN_END]
    data_len = len(data)

    for i in range(0, data_len - 7, 2):
        file_off = SCAN_START + i
        if in_skip(file_off):
            continue

        # Read 4 consecutive uint16s (8 bytes)
        vals = [struct.unpack_from('<H', data, i+j)[0] for j in range(0, 8, 2)]
        kanji_count = sum(1 for v in vals if is_kanji(v))

        if kanji_count >= 3:
            dense_windows.append((file_off, vals, kanji_count))

    # Merge overlapping windows into regions
    if not dense_windows:
        print("No dense kanji windows found.")
        return

    regions = []
    curr_start = dense_windows[0][0]
    curr_end = dense_windows[0][0] + 8
    curr_windows = [dense_windows[0]]

    for w in dense_windows[1:]:
        if w[0] <= curr_end + 4:  # allow small gap
            curr_end = max(curr_end, w[0] + 8)
            curr_windows.append(w)
        else:
            regions.append((curr_start, curr_end, curr_windows))
            curr_start = w[0]
            curr_end = w[0] + 8
            curr_windows = [w]
    regions.append((curr_start, curr_end, curr_windows))

    print(f"\nFound {len(regions)} dense kanji regions:")
    for start, end, windows in regions:
        size = end - start
        # Decode full region
        full_vals = [struct.unpack_from('<H', exe, start+j)[0] for j in range(0, size, 2)]
        text = ''.join(decode(v) for v in full_vals)
        kanji_text = ''.join(decode(v) for v in full_vals if is_kanji(v))
        total_kanji = sum(1 for v in full_vals if is_kanji(v))

        # Only report substantial regions
        if total_kanji >= 3:
            print(f"\n  0x{start:06X}-0x{end:06X} ({size}B, {total_kanji} kanji)")
            if len(text) > 100:
                print(f"    Text: {text[:100]}...")
            else:
                print(f"    Text: {text}")
            print(f"    Kanji: {kanji_text[:80]}")


if __name__ == '__main__':
    main()
