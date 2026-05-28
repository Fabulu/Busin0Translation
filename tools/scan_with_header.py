import struct, json, os

os.chdir('C:/Programmieren/wizardrytranslation')
gmap = json.load(open('data/msg_glyph_map.json', encoding='utf-8'))
manifest = json.load(open('extracted/packdata_resources/manifest.json', encoding='utf-8'))

translated_t1 = {34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,720,1053,1908,2124,2654}

# First, study how the known-good resources are structured
print("=== Known-good resource headers ===")
for rid in sorted(translated_t1)[:5]:
    fname = f"{rid:04d}_type01.raw"
    path = f'extracted/packdata_raw/{fname}'
    if not os.path.exists(path):
        print(f"R{rid}: not found")
        continue
    data = open(path, 'rb').read()
    # Show first 32 bytes
    hexdump = ' '.join(f'{b:02X}' for b in data[:32])
    # Try various header interpretations
    v1 = struct.unpack_from('>I', data, 0)[0]
    v2 = struct.unpack_from('<I', data, 0)[0]
    v3 = struct.unpack_from('>H', data, 0)[0]
    v4 = struct.unpack_from('<H', data, 0)[0]
    print(f"R{rid}: size={len(data)} | BE32={v1} LE32={v2} BE16={v3} LE16={v4}")
    print(f"  hex: {hexdump}")
    # If v1 or v2 looks like a message count, check offsets
    for count, endian, label in [(v1, '>', 'BE32'), (v2, '<', 'LE32'), (v3, '>', 'BE16'), (v4, '<', 'LE16')]:
        if 1 <= count <= 5000:
            # Check if offset table makes sense
            hdr_size = 4 if '32' in label else 2
            ofs_size = 4
            table_end = hdr_size + count * ofs_size
            if table_end < len(data):
                # Read first few offsets
                offsets = []
                valid = True
                for k in range(min(count, 5)):
                    off = struct.unpack_from(f'{endian}I', data, hdr_size + k*4)[0]
                    if off >= len(data):
                        valid = False
                        break
                    offsets.append(off)
                if valid and offsets:
                    print(f"  {label} count={count}, first offsets: {offsets}")
                    # Try to decode message at first offset
                    if offsets[0] < len(data) - 2:
                        msg = []
                        pos = offsets[0]
                        for _ in range(100):
                            if pos >= len(data) - 1:
                                break
                            val = struct.unpack_from('>H', data, pos)[0]
                            if val == 0xFFFF:
                                break
                            elif val == 0xFFFE:
                                msg.append('\n')
                            elif str(val) in gmap:
                                msg.append(gmap[str(val)])
                            else:
                                msg.append(f'[{val:04X}]')
                            pos += 2
                        print(f"    msg[0]: {''.join(msg)[:60]}")

print()
print("=== Scanning untranslated type-01 with valid MSG headers ===")

valid_msg_resources = []

for i, entry in enumerate(manifest):
    if entry.get('skipped'): continue
    if i in translated_t1: continue
    tc = entry['type_code']
    if tc != 1: continue

    fname = f"{i:04d}_type{tc:02d}.raw"
    path = f'extracted/packdata_raw/{fname}'
    if not os.path.exists(path): continue
    data = open(path, 'rb').read()
    if len(data) < 8: continue

    # Try the header format we discover from known-good resources
    # Try BE32 count at offset 0, then BE32 offsets
    for endian in ['>', '<']:
        count = struct.unpack_from(f'{endian}I', data, 0)[0]
        if count < 1 or count > 10000:
            continue

        table_end = 4 + count * 4
        if table_end >= len(data):
            continue

        # Validate offset table
        offsets = []
        valid = True
        for k in range(count):
            off = struct.unpack_from(f'{endian}I', data, 4 + k*4)[0]
            if off < table_end or off >= len(data):
                valid = False
                break
            offsets.append(off)

        if not valid or not offsets:
            continue

        # Check if offsets are monotonically increasing (common for MSG)
        monotonic = all(offsets[j] <= offsets[j+1] for j in range(len(offsets)-1))

        # Decode first few messages
        decoded = []
        coherent_count = 0
        for off in offsets[:min(count, 20)]:
            msg = []
            mapped = 0
            unmapped = 0
            pos = off
            for _ in range(500):
                if pos >= len(data) - 1:
                    break
                val = struct.unpack_from('>H', data, pos)[0]
                if val == 0xFFFF:
                    break
                elif val == 0xFFFE:
                    msg.append('\n')
                elif val >= 0xFB00:
                    pass
                elif str(val) in gmap:
                    msg.append(gmap[str(val)])
                    mapped += 1
                elif val < 1200:
                    msg.append(f'[{val:04X}]')
                    unmapped += 1
                else:
                    msg.append(f'<{val:04X}>')
                    unmapped += 1
                pos += 2

            text = ''.join(msg)
            ratio = mapped / max(1, mapped + unmapped)
            if len(text) >= 2 and ratio >= 0.5:
                coherent_count += 1
            decoded.append(text)

        coherence = coherent_count / min(count, 20)

        if coherence >= 0.5 and monotonic:
            sample = next((d for d in decoded if len(d) >= 5), decoded[0] if decoded else '')
            valid_msg_resources.append({
                'resource': i,
                'count': count,
                'endian': 'BE' if endian == '>' else 'LE',
                'monotonic': monotonic,
                'coherence': round(coherence, 2),
                'size': len(data),
                'sample': sample[:80]
            })
            break  # Don't try other endian

valid_msg_resources.sort(key=lambda x: -x['count'])

print(f"Found {len(valid_msg_resources)} resources with valid MSG headers")
print(f"Total messages: {sum(r['count'] for r in valid_msg_resources)}")
print()
for r in valid_msg_resources[:50]:
    print(f"  R{r['resource']:4d}: {r['count']:5d} msgs, {r['endian']}, coh={r['coherence']:.0%}, {r['size']:8d}B | {r['sample'][:65]}")

json.dump(valid_msg_resources, open('data/valid_msg_resources.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print(f"\nSaved to data/valid_msg_resources.json")
