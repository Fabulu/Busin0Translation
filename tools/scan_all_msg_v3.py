"""
Fast scan of ALL type-01 resources for MSG text.
Optimized: skip huge files (>500KB), efficient decoding.
"""
import struct, json, os, sys, io, re, glob

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
os.chdir('C:/Programmieren/wizardrytranslation')

gmap = json.load(open('data/msg_glyph_map.json', encoding='utf-8'))
translated_t1 = {34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,720,1053,1908,2124,2654}
bracket_re = re.compile(r'\[\d+\]')

type01_files = sorted(glob.glob('extracted/packdata_resources/*_type01.bin'))
print(f"Total type-01 .bin files: {len(type01_files)}", flush=True)

results = []
skipped_large = 0

for idx, fpath in enumerate(type01_files):
    if idx % 200 == 0:
        print(f"  Processing {idx}/{len(type01_files)}...", flush=True)

    fname = os.path.basename(fpath)
    rid = int(fname.split('_')[0])
    if rid in translated_t1:
        continue

    fsize = os.path.getsize(fpath)
    # Skip files > 500KB - these are not MSG text files, they're graphics/binary
    if fsize > 512000:
        skipped_large += 1
        continue
    if fsize < 20:
        continue

    data = open(fpath, 'rb').read()

    # Find first FFFF
    first_ffff = None
    for off in range(0, len(data) - 1, 2):
        val = struct.unpack_from('>H', data, off)[0]
        if val == 0xFFFF:
            first_ffff = off
            break

    if first_ffff is None:
        continue

    # Decode from first FFFF
    stream = data[first_ffff:]
    n = len(stream) // 2
    if n < 2:
        continue
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
            pass
        else:
            cur.append(v)
    if cur:
        messages.append(cur)

    if not messages:
        continue

    # Decode and assess
    total_mapped = 0
    total_unmapped = 0
    sentence_count = 0
    real_count = 0
    sample = ''

    for msg_glyphs in messages:
        text = ''
        mapped = 0
        unmapped = 0
        has_hiragana = False
        has_kanji = False
        has_katakana = False

        for g in msg_glyphs:
            gs = str(g)
            if gs in gmap:
                ch = gmap[gs]
                text += ch
                mapped += 1
                cp = ord(ch)
                if 0x3040 <= cp <= 0x309F: has_hiragana = True
                elif 0x4E00 <= cp <= 0x9FFF: has_kanji = True
                elif 0x30A0 <= cp <= 0x30FF: has_katakana = True
            else:
                text += f'[{g}]'
                unmapped += 1

        total_mapped += mapped
        total_unmapped += unmapped

        ratio = mapped / max(1, mapped + unmapped)
        clean_text = bracket_re.sub('', text)

        if len(clean_text) >= 3 and ratio >= 0.7:
            real_count += 1

        if (has_hiragana or (has_kanji and has_katakana)) and ratio >= 0.7 and len(text) >= 5:
            sentence_count += 1
            if not sample:
                sample = text[:80]

    if not sample and messages:
        # Just show first decoded message
        first_text = ''
        for g in messages[0]:
            gs = str(g)
            first_text += gmap.get(gs, f'[{g}]')
        sample = first_text[:80]

    overall_ratio = total_mapped / max(1, total_mapped + total_unmapped)

    results.append({
        'resource': rid,
        'size': fsize,
        'first_ffff': first_ffff,
        'total_msgs': len(messages),
        'real_msgs': real_count,
        'sentence_msgs': sentence_count,
        'overall_ratio': round(overall_ratio, 3),
        'sample': sample
    })

results.sort(key=lambda x: (-x['sentence_msgs'], -x['real_msgs']))

has_sentences = [r for r in results if r['sentence_msgs'] > 0]
has_real = [r for r in results if r['real_msgs'] > 0]

print(f"\n{'='*70}")
print(f"Scanned: {len(results)} type-01 resources (skipped {skipped_large} >500KB, {len(translated_t1)} translated)")
print(f"Resources with sentence-like messages: {len(has_sentences)}")
print(f"Total sentence-like messages: {sum(r['sentence_msgs'] for r in has_sentences)}")
print(f"Resources with real (70%+ mapped) messages: {len(has_real)}")
print(f"Total real messages: {sum(r['real_msgs'] for r in has_real)}")
print()

print(f"=== Top 60 resources with sentence-like text ===")
for r in has_sentences[:60]:
    print(f"  R{r['resource']:4d}: {r['sentence_msgs']:4d} sentences / {r['total_msgs']:5d} total, map={r['overall_ratio']:.0%}, {r['size']:7d}B | {r['sample'][:70]}")

print()
print("=== Bracket summary (sentence-like) ===")
for lo, hi, label in [(1,5,'1-4'), (5,20,'5-19'), (20,100,'20-99'), (100,500,'100-499'), (500,99999,'500+')]:
    bracket = [r for r in has_sentences if lo <= r['sentence_msgs'] < hi]
    if bracket:
        msgs = sum(r['sentence_msgs'] for r in bracket)
        print(f"  {label}: {len(bracket)} resources, {msgs} messages")

print()
print("=== Resources with ONLY structural data (real_msgs but no sentences) ===")
struct_only = [r for r in results if r['real_msgs'] > 0 and r['sentence_msgs'] == 0]
print(f"  Count: {len(struct_only)}, total msgs: {sum(r['real_msgs'] for r in struct_only)}")

json.dump(results, open('data/remaining_msg_scan_v3.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print(f"\nSaved to data/remaining_msg_scan_v3.json")
