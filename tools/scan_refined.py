import struct, json, os

os.chdir('C:/Programmieren/wizardrytranslation')
gmap = json.load(open('data/msg_glyph_map.json', encoding='utf-8'))
manifest = json.load(open('extracted/packdata_resources/manifest.json', encoding='utf-8'))

# Already translated resources
translated_t1 = {34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,720,1053,1908,2124,2654}

# Check known-good resource to understand the MSG header structure
# Real MSG files have: 4-byte header with message count, then offset table, then messages

def try_msg_header(data):
    """Try to parse as proper MSG format with header."""
    if len(data) < 8:
        return None

    # Try BE uint32 message count at offset 0
    count_be = struct.unpack_from('>I', data, 0)[0]
    # Try LE uint32
    count_le = struct.unpack_from('<I', data, 0)[0]

    results = []
    for count, endian, label in [(count_be, '>', 'BE'), (count_le, '<', 'LE')]:
        if count == 0 or count > 10000:
            continue
        # Check if offset table looks valid
        offset_table_size = 4 + count * 4
        if offset_table_size > len(data):
            continue

        # Read offsets
        valid = True
        offsets = []
        for i in range(count):
            off = struct.unpack_from(f'{endian}I', data, 4 + i*4)[0]
            if off >= len(data):
                valid = False
                break
            offsets.append(off)

        if valid and offsets:
            results.append((count, endian, offsets))

    return results if results else None

def decode_msg_at(data, offset, gmap):
    """Decode a single message starting at offset."""
    chars = []
    j = offset
    while j < len(data) - 1:
        val = struct.unpack_from('>H', data, j)[0]
        if val == 0xFFFF:
            break
        elif val == 0xFFFE:
            chars.append('\n')
        elif val >= 0xFB00:
            pass  # control
        elif str(val) in gmap:
            chars.append(gmap[str(val)])
        elif val < 1200:
            chars.append(f'[{val:04X}]')
        else:
            chars.append(f'<{val:04X}>')
        j += 2
    return ''.join(chars)

# Scan all type-01 resources
real_text_resources = []
structural_resources = []
noise_resources = []

for i, entry in enumerate(manifest):
    if entry.get('skipped'): continue
    if i in translated_t1: continue

    tc = entry['type_code']
    if tc != 1: continue

    fname = f"{i:04d}_type{tc:02d}.raw"
    path = f'extracted/packdata_raw/{fname}'
    if not os.path.exists(path): continue

    data = open(path, 'rb').read()
    if len(data) < 20: continue

    # Try MSG header parse
    header_results = try_msg_header(data)

    # Also do brute-force scan
    messages = []
    msg_chars = []
    mapped_count = 0
    unmapped_count = 0

    for j in range(0, len(data)-1, 2):
        val = struct.unpack_from('>H', data, j)[0]
        if val == 0xFFFF:
            if len(msg_chars) >= 3:
                text = ''.join(msg_chars)
                # Check quality: need mostly real Japanese characters
                jp_chars = sum(1 for c in text if ord(c) > 0x3000)
                latin_chars = sum(1 for c in text if c.isascii() and c.isalpha())
                bracket_seqs = text.count('[')
                real_char_ratio = (jp_chars + latin_chars) / max(1, len(text.replace('\n','')))

                if jp_chars + latin_chars >= 3 and real_char_ratio > 0.3:
                    messages.append({
                        'text': text,
                        'jp_chars': jp_chars,
                        'ratio': real_char_ratio
                    })
            msg_chars = []
            mapped_count = 0
            unmapped_count = 0
        elif val == 0xFFFE:
            msg_chars.append('\n')
        elif val >= 0xFB00:
            pass
        elif str(val) in gmap:
            c = gmap[str(val)]
            msg_chars.append(c)
            mapped_count += 1
        elif val < 1200:
            msg_chars.append(f'[{val:04X}]')
            unmapped_count += 1
        else:
            if msg_chars and len(msg_chars) < 3:
                msg_chars = []

    if not messages:
        continue

    # Classify: real text vs structural/noise
    avg_ratio = sum(m['ratio'] for m in messages) / len(messages)
    avg_jp = sum(m['jp_chars'] for m in messages) / len(messages)

    # Real text: good ratio, decent JP char count per message
    # Look for messages that look like actual sentences (has hiragana/katakana mix, length > 10)
    sentence_like = [m for m in messages if m['jp_chars'] >= 5 and len(m['text']) >= 10 and m['ratio'] > 0.5]

    info = {
        'resource': i,
        'size': len(data),
        'total_msgs': len(messages),
        'sentence_like': len(sentence_like),
        'avg_ratio': round(avg_ratio, 2),
        'avg_jp_chars': round(avg_jp, 1),
        'has_header': header_results is not None,
        'sample': sentence_like[0]['text'][:80] if sentence_like else messages[0]['text'][:80]
    }

    if sentence_like:
        real_text_resources.append(info)
    else:
        structural_resources.append(info)

real_text_resources.sort(key=lambda x: -x['sentence_like'])

print(f"=== SCAN RESULTS ===")
print(f"Resources with sentence-like text: {len(real_text_resources)}")
print(f"  Total sentence-like messages: {sum(r['sentence_like'] for r in real_text_resources)}")
print(f"Resources with only structural/noise text: {len(structural_resources)}")
print()

print("Top 40 resources with real text:")
for r in real_text_resources[:40]:
    hdr = 'H' if r['has_header'] else ' '
    print(f"  R{r['resource']:4d} [{hdr}]: {r['sentence_like']:5d} sentences / {r['total_msgs']:5d} total, {r['size']:8d}B | {r['sample'][:70]}")

print()
print("Size distribution of real-text resources:")
for lo, hi, label in [(0, 1000, '<1KB'), (1000, 10000, '1-10KB'), (10000, 100000, '10-100KB'),
                        (100000, 1000000, '100KB-1MB'), (1000000, 99999999, '>1MB')]:
    bracket = [r for r in real_text_resources if lo <= r['size'] < hi]
    if bracket:
        print(f"  {label}: {len(bracket)} resources, {sum(r['sentence_like'] for r in bracket)} sentences")

# Save
json.dump(real_text_resources, open('data/remaining_real_text.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print(f"\nSaved {len(real_text_resources)} entries to data/remaining_real_text.json")
