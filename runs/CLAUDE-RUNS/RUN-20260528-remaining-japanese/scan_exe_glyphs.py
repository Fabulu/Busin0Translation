#!/usr/bin/env python3
"""
Scan EXE data section for remaining Japanese glyph ID clusters.
Looks for LE uint16 values in glyph range 95-881 appearing in clusters.
"""
import json, struct, sys

sys.stdout.reconfigure(encoding='utf-8')

EXE_PATH = "C:/Programmieren/wizardrytranslation/extracted/SLPM_653.78"
GLYPH_MAP_PATH = "C:/Programmieren/wizardrytranslation/data/msg_glyph_map.json"
OUT_PATH = "C:/Programmieren/wizardrytranslation/runs/CLAUDE-RUNS/RUN-20260528-remaining-japanese/exe_glyph_scan.md"

# Data section range
SCAN_START = 0x3B0000
SCAN_END   = 0x3FD000

# Known/handled regions to skip
SKIP_REGIONS = [
    (0x3C3000, 0x3C5300, "menu structs (already handled)"),
    (0x3C83C0, 0x3C93A0, "chargen grid (R38, already handled)"),
    (0x3C9DA0, 0x3C9DFC, "name entry tab IDs (Table 2E)"),
]

# Glyph ID range for Japanese kanji
KANJI_MIN = 95
KANJI_MAX = 881

# Cluster detection params
MIN_CLUSTER_SIZE = 3    # min consecutive glyph-range hits
MAX_GAP_BYTES = 20      # max gap between glyph-range values in a cluster

def in_skip_region(offset):
    for start, end, _ in SKIP_REGIONS:
        if start <= offset < end:
            return True
    return False

def main():
    glyph_map = json.load(open(GLYPH_MAP_PATH, 'r', encoding='utf-8'))

    with open(EXE_PATH, 'rb') as f:
        exe_data = f.read()

    scan_data = exe_data[SCAN_START:SCAN_END]
    scan_len = len(scan_data)

    # Pass 1: find all offsets with glyph-range uint16 values
    glyph_hits = []  # (file_offset, glyph_id)
    for i in range(0, scan_len - 1, 2):  # step by 2 for uint16 alignment
        file_offset = SCAN_START + i
        if in_skip_region(file_offset):
            continue
        val = struct.unpack_from('<H', scan_data, i)[0]
        if KANJI_MIN <= val <= KANJI_MAX:
            glyph_hits.append((file_offset, val))

    print(f"Total glyph-range uint16 hits (outside skips): {len(glyph_hits)}")

    # Pass 2: cluster detection
    # Group hits where consecutive hits are within MAX_GAP_BYTES of each other
    clusters = []
    if glyph_hits:
        current_cluster = [glyph_hits[0]]
        for j in range(1, len(glyph_hits)):
            prev_off = glyph_hits[j-1][0]
            curr_off = glyph_hits[j][0]
            if curr_off - prev_off <= MAX_GAP_BYTES:
                current_cluster.append(glyph_hits[j])
            else:
                if len(current_cluster) >= MIN_CLUSTER_SIZE:
                    clusters.append(current_cluster)
                current_cluster = [glyph_hits[j]]
        if len(current_cluster) >= MIN_CLUSTER_SIZE:
            clusters.append(current_cluster)

    print(f"Clusters found (>= {MIN_CLUSTER_SIZE} hits within {MAX_GAP_BYTES}B): {len(clusters)}")

    # Decode and report
    results = []
    for ci, cluster in enumerate(clusters):
        start_off = cluster[0][0]
        end_off = cluster[-1][0] + 2
        region_size = end_off - start_off

        # Decode glyph IDs to characters
        decoded_chars = []
        for off, gid in cluster:
            ch = glyph_map.get(str(gid), f'[?{gid}]')
            decoded_chars.append(ch)
        decoded_text = ''.join(decoded_chars)

        # Also grab full raw bytes for context - read wider region
        ctx_start = max(SCAN_START, start_off - 8)
        ctx_end = min(SCAN_END, end_off + 8)
        raw_bytes = exe_data[ctx_start:ctx_end]
        hex_dump = raw_bytes.hex(' ')

        # Read ALL uint16 values in the cluster range (including non-kanji)
        full_decode = []
        for k in range(start_off, end_off, 2):
            val = struct.unpack_from('<H', exe_data, k)[0]
            if KANJI_MIN <= val <= KANJI_MAX:
                ch = glyph_map.get(str(val), f'[?{val}]')
                full_decode.append(ch)
            elif 0 < val < 95:
                # ASCII-range glyph: char_code = glyph_id + 0x20
                ascii_ch = chr(val + 0x20)
                full_decode.append(ascii_ch)
            elif val == 0:
                full_decode.append('[NUL]')
            else:
                full_decode.append(f'[{val}]')
        full_text = ''.join(full_decode)

        # Try to guess purpose based on location and content
        purpose = guess_purpose(start_off, decoded_text, cluster)

        results.append({
            'index': ci,
            'start': start_off,
            'end': end_off,
            'size': region_size,
            'count': len(cluster),
            'decoded_kanji': decoded_text,
            'full_decode': full_text,
            'hex': hex_dump,
            'purpose': purpose,
        })

        print(f"\n--- Cluster {ci} @ 0x{start_off:06X}-0x{end_off:06X} ({len(cluster)} glyphs, {region_size}B) ---")
        print(f"  Kanji decoded: {decoded_text}")
        print(f"  Full decode:   {full_text}")
        print(f"  Purpose guess: {purpose}")

    # Write report
    write_report(results)
    print(f"\nReport written to {OUT_PATH}")


def guess_purpose(offset, text, cluster):
    """Heuristic purpose classification."""
    # Check for common patterns
    if any(ch in text for ch in ['攻撃', '防御', '魔法', '呪文']):
        return "Battle/combat labels"
    if any(ch in text for ch in ['毒', '麻痺', '石化', '死']):
        return "Status effect labels"
    if any(ch in text for ch in ['戦士', '魔術', '僧侶', '盗賊']):
        return "Class names"
    if any(ch in text for ch in ['人間', 'エルフ', 'ドワーフ']):
        return "Race names"
    if any(ch in text for ch in ['剣', '盾', '鎧', '兜', '杖']):
        return "Equipment/item names"
    if any(ch in text for ch in ['力', '知', '信', '生命', '速']):
        return "Stat labels"
    if any(ch in text for ch in ['はい', 'いいえ', '確認', 'キャンセル']):
        return "UI confirmation labels"
    if 0x3C0000 <= offset < 0x3C3000:
        return "Pre-menu data area"
    if 0x3C5300 <= offset < 0x3C8000:
        return "Post-menu / pre-chargen area"
    if 0x3C9400 <= offset < 0x3CA000:
        return "Post-chargen table area"
    if 0x3CA000 <= offset:
        return "Late data section"
    return "Unknown - needs investigation"


def write_report(results):
    with open(OUT_PATH, 'w', encoding='utf-8') as f:
        f.write("# EXE Remaining Japanese Glyph Scan Results\n\n")
        f.write(f"**Date:** 2026-05-28\n")
        f.write(f"**Scan range:** 0x{SCAN_START:06X} - 0x{SCAN_END:06X}\n")
        f.write(f"**Glyph ID range:** {KANJI_MIN}-{KANJI_MAX} (Japanese kanji)\n")
        f.write(f"**Cluster params:** >= {MIN_CLUSTER_SIZE} hits within {MAX_GAP_BYTES} bytes\n")
        f.write(f"**Total clusters found:** {len(results)}\n\n")

        f.write("## Skip regions (already handled)\n\n")
        for start, end, desc in SKIP_REGIONS:
            f.write(f"- 0x{start:06X}-0x{end:06X}: {desc}\n")
        f.write("\n")

        f.write("## Clusters Found\n\n")

        for r in results:
            f.write(f"### Cluster {r['index']}: 0x{r['start']:06X}-0x{r['end']:06X}\n\n")
            f.write(f"- **Offset:** 0x{r['start']:06X} - 0x{r['end']:06X} ({r['size']} bytes)\n")
            f.write(f"- **Kanji glyph count:** {r['count']}\n")
            f.write(f"- **Kanji decoded:** {r['decoded_kanji']}\n")
            f.write(f"- **Full decode (with ASCII):** {r['full_decode']}\n")
            f.write(f"- **Purpose:** {r['purpose']}\n")
            f.write(f"- **Hex context:** `{r['hex']}`\n")
            f.write("\n")

        f.write("## Summary\n\n")
        purposes = {}
        for r in results:
            p = r['purpose']
            purposes.setdefault(p, []).append(r)
        for p, items in sorted(purposes.items()):
            f.write(f"- **{p}:** {len(items)} cluster(s)\n")
            for item in items:
                f.write(f"  - 0x{item['start']:06X}: {item['decoded_kanji'][:40]}\n")
        f.write("\n")


if __name__ == '__main__':
    main()
