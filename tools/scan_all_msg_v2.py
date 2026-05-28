"""
Scan ALL type-01 resources using the same decode approach as decode_r40.py:
find first FFFF, then split on FFFF/FFFE boundaries.
Uses .bin files from packdata_resources/.
"""
import struct, json, os, sys, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

os.chdir('C:/Programmieren/wizardrytranslation')
gmap = json.load(open('data/msg_glyph_map.json', encoding='utf-8'))

# Already translated type-01 resources
translated_t1 = {34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,720,1053,1908,2124,2654}

# Collect all type-01 .bin files
import glob
type01_files = sorted(glob.glob('extracted/packdata_resources/*_type01.bin'))
print(f"Total type-01 .bin files: {len(type01_files)}")

results = []
total_new_messages = 0

for fpath in type01_files:
    fname = os.path.basename(fpath)
    rid = int(fname.split('_')[0])
    if rid in translated_t1:
        continue

    data = open(fpath, 'rb').read()
    if len(data) < 20:
        continue

    # Find first FFFF
    first_ffff = None
    for off in range(0, len(data) - 1, 2):
        val = struct.unpack_from('>H', data, off)[0]
        if val == 0xFFFF:
            first_ffff = off
            break

    if first_ffff is None:
        continue

    # Decode from first FFFF onwards
    stream = data[first_ffff:]
    n = len(stream) // 2
    vals = struct.unpack(f'>{n}H', stream[:n*2])

    messages = []
    cur = []
    for v in vals:
        if v == 0xFFFF:
            if cur:
                messages.append(cur)
            cur = []
        elif v == 0xFFFE:
            if cur:
                messages.append(cur)
            cur = []
        elif v >= 0xFFC0:
            pass  # control codes
        else:
            cur.append(v)
    if cur:
        messages.append(cur)

    if not messages:
        continue

    # Decode messages to text and assess quality
    decoded_msgs = []
    for msg_glyphs in messages:
        text = ''
        mapped = 0
        unmapped = 0
        for g in msg_glyphs:
            gs = str(g)
            if gs in gmap:
                text += gmap[gs]
                mapped += 1
            else:
                text += f'[{g}]'
                unmapped += 1

        if len(text) >= 1:
            decoded_msgs.append({
                'text': text,
                'mapped': mapped,
                'unmapped': unmapped,
                'total': mapped + unmapped,
                'ratio': mapped / max(1, mapped + unmapped)
            })

    if not decoded_msgs:
        continue

    # Quality assessment: compute aggregate stats
    total_mapped = sum(m['mapped'] for m in decoded_msgs)
    total_unmapped = sum(m['unmapped'] for m in decoded_msgs)
    overall_ratio = total_mapped / max(1, total_mapped + total_unmapped)

    # Count "real" messages: ratio >= 0.7, length >= 3 chars (excluding bracket notation)
    real_msgs = []
    for m in decoded_msgs:
        clean = m['text']
        # Remove [xxx] bracket notation
        import re
        clean_text = re.sub(r'\[\d+\]', '', clean)
        if len(clean_text) >= 3 and m['ratio'] >= 0.7:
            real_msgs.append(m)

    # Sentence-like: has hiragana (common in real Japanese text)
    # Hiragana range: U+3040-U+309F
    sentence_msgs = []
    for m in decoded_msgs:
        has_hiragana = any('\u3040' <= c <= '\u309f' for c in m['text'])
        has_kanji = any('\u4e00' <= c <= '\u9fff' for c in m['text'])
        has_katakana = any('\u30a0' <= c <= '\u30ff' for c in m['text'])
        if (has_hiragana or (has_kanji and has_katakana)) and m['ratio'] >= 0.7 and len(m['text']) >= 5:
            sentence_msgs.append(m)

    sample = ''
    if sentence_msgs:
        sample = sentence_msgs[0]['text'][:80]
    elif real_msgs:
        sample = real_msgs[0]['text'][:80]
    elif decoded_msgs:
        sample = decoded_msgs[0]['text'][:80]

    results.append({
        'resource': rid,
        'size': len(data),
        'first_ffff': first_ffff,
        'total_msgs': len(decoded_msgs),
        'real_msgs': len(real_msgs),
        'sentence_msgs': len(sentence_msgs),
        'overall_ratio': round(overall_ratio, 3),
        'sample': sample
    })
    total_new_messages += len(sentence_msgs)

# Sort by sentence-like message count
results.sort(key=lambda x: (-x['sentence_msgs'], -x['real_msgs']))

print(f"\n{'='*70}")
print(f"Type-01 resources scanned (excluding {len(translated_t1)} already translated): {len(results)}")
print(f"Resources with sentence-like messages: {sum(1 for r in results if r['sentence_msgs'] > 0)}")
print(f"Total sentence-like messages: {total_new_messages}")
print(f"Resources with 'real' messages (mapped>=70%): {sum(1 for r in results if r['real_msgs'] > 0)}")
print(f"Total real messages: {sum(r['real_msgs'] for r in results)}")
print()

# Show resources with sentence-like text
has_sentences = [r for r in results if r['sentence_msgs'] > 0]
print(f"=== Resources with sentence-like text ({len(has_sentences)}) ===")
for r in has_sentences[:60]:
    print(f"  R{r['resource']:4d}: {r['sentence_msgs']:4d} sentences / {r['total_msgs']:5d} total, ratio={r['overall_ratio']:.0%}, {r['size']:8d}B ffff@{r['first_ffff']}")
    print(f"         {r['sample'][:75]}")

print()
print("=== Summary by bracket ===")
for lo, hi, label in [(1,5,'1-4'), (5,20,'5-19'), (20,100,'20-99'), (100,500,'100-499'), (500,99999,'500+')]:
    bracket = [r for r in has_sentences if lo <= r['sentence_msgs'] < hi]
    if bracket:
        msgs = sum(r['sentence_msgs'] for r in bracket)
        print(f"  {label} sentence msgs: {len(bracket)} resources, {msgs} messages total")

# Save
json.dump(results, open('data/remaining_msg_scan_v2.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print(f"\nFull results saved to data/remaining_msg_scan_v2.json")
