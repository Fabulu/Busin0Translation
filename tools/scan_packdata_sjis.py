#!/usr/bin/env python3
"""
Scan PACKDATA.DIG for Shift-JIS Japanese text strings - v3 with strict filtering.
Key insight: real Japanese text has consecutive hiragana runs (particles, verb endings).
Binary noise rarely produces consecutive hiragana.
"""
import sys, os, time
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

INPUT_FILE = r"C:\Programmieren\wizardrytranslation\extracted\PACKDATA.DIG"
OUTPUT_FILE = r"C:\Programmieren\wizardrytranslation\dumps\packdata_sjis_scan.txt"
CHUNK_SIZE = 16 * 1024 * 1024
OVERLAP = 4096
MIN_CHARS = 4
# Require at least 3 consecutive hiragana/katakana chars somewhere, OR at least 4 total JP chars
MIN_CONSECUTIVE_KANA = 3
MIN_TOTAL_JP_ALT = 4

def is_sjis_lead(b): return (0x81 <= b <= 0x9F) or (0xE0 <= b <= 0xEF)
def is_sjis_trail(b): return (0x40 <= b <= 0x7E) or (0x80 <= b <= 0xFC)
def is_ascii_printable(b): return 0x20 <= b <= 0x7E

def classify_char(cp):
    """Return char class: 'h'=hiragana, 'k'=katakana, 'j'=kanji, 'p'=jp_punct, 'f'=fullwidth, None=other"""
    if 0x3040 <= cp <= 0x309F: return 'h'
    if 0x30A0 <= cp <= 0x30FF: return 'k'
    if 0x4E00 <= cp <= 0x9FFF: return 'j'
    if 0x3000 <= cp <= 0x303F: return 'p'
    if 0xFF00 <= cp <= 0xFFEF: return 'f'
    return None

def is_real_japanese(char_classes):
    """
    Determine if a sequence of char classes represents real Japanese text.
    Real text has: consecutive kana runs, or kanji+kana patterns.
    """
    # Count consecutive hiragana or katakana runs
    max_kana_run = 0
    current_kana_run = 0
    total_jp = 0
    total_kana = 0
    for c in char_classes:
        if c in ('h', 'k'):
            current_kana_run += 1
            max_kana_run = max(max_kana_run, current_kana_run)
            total_jp += 1
            total_kana += 1
        elif c in ('j', 'p', 'f'):
            current_kana_run = 0
            total_jp += 1
        else:
            current_kana_run = 0

    # Strong signal: consecutive kana run
    if max_kana_run >= MIN_CONSECUTIVE_KANA:
        return True

    # Alternative: many JP chars with at least some kana (kanji-heavy text)
    if total_jp >= MIN_TOTAL_JP_ALT and total_kana >= 2:
        return True

    # Pure kanji strings of length >= 4 (item names, etc.)
    kanji_count = sum(1 for c in char_classes if c == 'j')
    if kanji_count >= 4:
        return True

    return False

def scan_chunk(data, base_offset, seen_offsets):
    results = []
    i = 0
    length = len(data)
    while i < length:
        start = i
        chars = 0
        byte_seq = bytearray()
        char_classes = []  # track character types for validation

        while i < length:
            b = data[i]
            if is_sjis_lead(b):
                if i + 1 < length and is_sjis_trail(data[i + 1]):
                    try:
                        ch = bytes([b, data[i+1]]).decode('shift_jis')
                        if len(ch) != 1:
                            break
                        cls = classify_char(ord(ch))
                        if cls is None:
                            # Valid SJIS but not Japanese (symbols, etc) - allow some
                            # but treat as non-JP for classification
                            char_classes.append('o')
                        else:
                            char_classes.append(cls)
                    except (UnicodeDecodeError, ValueError):
                        break
                    byte_seq.append(b)
                    byte_seq.append(data[i + 1])
                    chars += 1
                    i += 2
                else:
                    break
            elif is_ascii_printable(b):
                byte_seq.append(b)
                char_classes.append('a')
                chars += 1
                i += 1
            elif b == 0x0A or b == 0x0D:
                byte_seq.append(b)
                i += 1
            else:
                break

        if chars >= MIN_CHARS and is_real_japanese(char_classes):
            actual_offset = base_offset + start
            if actual_offset not in seen_offsets:
                seen_offsets.add(actual_offset)
                try:
                    decoded = bytes(byte_seq).decode('shift_jis', errors='replace')
                    decoded_stripped = decoded.strip()
                    if len(decoded_stripped) >= MIN_CHARS:
                        results.append((actual_offset, len(byte_seq), decoded_stripped))
                except: pass
        if i == start: i += 1
    return results

def categorize_text(text):
    brackets = '\u300c\u300d\u300e\u300f'
    if any(c in text for c in brackets): return "dialogue"
    katakana_count = sum(1 for c in text if 0x30A0 <= ord(c) <= 0x30FF)
    hiragana_count = sum(1 for c in text if 0x3040 <= ord(c) <= 0x309F)
    kanji_count = sum(1 for c in text if 0x4E00 <= ord(c) <= 0x9FFF)
    total = len(text)
    if katakana_count > total * 0.6 and total <= 20: return "name/term"
    if hiragana_count > total * 0.5: return "narrative/dialogue"
    if kanji_count > total * 0.7 and total <= 12: return "label/menu"
    if total > 30: return "long_text"
    return "short_text"

def main():
    file_size = os.path.getsize(INPUT_FILE)
    print(f"Scanning {INPUT_FILE}")
    print(f"File size: {file_size:,} bytes ({file_size/(1024*1024):.1f} MB)")
    print(f"v3: strict kana-run filtering")
    print()
    all_results = []
    region_counts = defaultdict(int)
    seen_offsets = set()
    start_time = time.time()
    with open(INPUT_FILE, 'rb') as f:
        chunk_num = 0
        file_offset = 0
        while file_offset < file_size:
            read_start = max(0, file_offset - OVERLAP) if chunk_num > 0 else 0
            f.seek(read_start)
            data = f.read(CHUNK_SIZE + OVERLAP)
            if not data: break
            results = scan_chunk(data, read_start, seen_offsets)
            all_results.extend(results)
            for offset, length, text in results:
                region_counts[offset // (1024*1024)] += 1
            file_offset += CHUNK_SIZE
            chunk_num += 1
            elapsed = time.time() - start_time
            progress = min(file_offset, file_size) / file_size * 100
            print(f"  Chunk {chunk_num}: {progress:.1f}% - {len(all_results)} strings - {elapsed:.1f}s", flush=True)
    elapsed = time.time() - start_time
    print(f"\nScan complete in {elapsed:.1f}s")
    print(f"Total strings found: {len(all_results)}")
    all_results.sort(key=lambda x: x[0])
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as out:
        out.write(f"PACKDATA.DIG Shift-JIS String Scan Results (v3 - strict)\n")
        out.write(f"File size: {file_size:,} bytes\n")
        out.write(f"Total strings found: {len(all_results)}\n")
        out.write(f"Scan time: {elapsed:.1f}s\n")
        out.write("=" * 80 + "\n\n")
        out.write("REGION SUMMARY (strings per MB):\n")
        out.write("-" * 60 + "\n")
        if region_counts:
            for mb in range(max(region_counts.keys()) + 1):
                count = region_counts.get(mb, 0)
                if count > 0:
                    bar = "#" * min(count, 100)
                    out.write(f"  MB {mb:4d}: {count:6d} strings  {bar}\n")
        out.write("\n" + "=" * 80 + "\n\nDETAILED RESULTS:\n" + "-" * 60 + "\n\n")
        current_mb = -1
        for offset, length, text in all_results:
            mb = offset // (1024 * 1024)
            if mb != current_mb:
                current_mb = mb
                out.write(f"\n--- Region: MB {mb} (0x{mb*1024*1024:08X}) - {region_counts.get(mb,0)} strings ---\n\n")
            dt = text[:200]
            if len(text) > 200: dt += "..."
            dt = dt.replace("\n","\\n").replace("\r","\\r")
            out.write(f"  0x{offset:08X} [{length:4d} bytes] {dt}\n")
        out.write("\n" + "=" * 80 + "\n\nTEXT CATEGORY ANALYSIS (first 2000):\n" + "-" * 60 + "\n")
        cc = defaultdict(int)
        ce = defaultdict(list)
        for o, l, t in all_results[:2000]:
            cat = categorize_text(t)
            cc[cat] += 1
            if len(ce[cat]) < 5: ce[cat].append((o, t[:100]))
        for cat, count in sorted(cc.items(), key=lambda x: -x[1]):
            out.write(f"\n  {cat}: {count} strings\n")
            for off, ex in ce[cat]:
                ed = ex.replace("\n","\\n").replace("\r","\\r")
                out.write(f"    Example @ 0x{off:08X}: {ed}\n")
    print(f"Results saved to: {OUTPUT_FILE}")
    print()
    print("TOP 20 REGIONS BY STRING COUNT:")
    for mb, count in sorted(region_counts.items(), key=lambda x: -x[1])[:20]:
        print(f"  MB {mb:4d} (0x{mb*1024*1024:08X}): {count:6d} strings")
    print()
    print("SAMPLE STRINGS (first 50):")
    for offset, length, text in all_results[:50]:
        d = text[:100].replace("\n","\\n").replace("\r","\\r")
        print(f"  0x{offset:08X}: {d}")
    print()
    print("SAMPLE STRINGS (middle of file):")
    mid = len(all_results) // 2
    for offset, length, text in all_results[mid:mid+30]:
        d = text[:100].replace("\n","\\n").replace("\r","\\r")
        print(f"  0x{offset:08X}: {d}")

if __name__ == '__main__': main()
