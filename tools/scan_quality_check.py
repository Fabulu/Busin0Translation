import struct, json, os

os.chdir('C:/Programmieren/wizardrytranslation')
gmap = json.load(open('data/msg_glyph_map.json', encoding='utf-8'))

def decode_resource(res_id):
    """Decode a resource and return quality metrics."""
    path = f'extracted/packdata_raw/{res_id:04d}_type01.raw'
    if not os.path.exists(path):
        return None
    data = open(path, 'rb').read()

    messages = []
    msg_chars = []
    msg_glyph_hits = 0
    msg_unmapped = 0

    for j in range(0, len(data)-1, 2):
        val = struct.unpack_from('>H', data, j)[0]
        if val == 0xFFFF:
            if len(msg_chars) >= 3:
                text = ''.join(msg_chars)
                messages.append((text, msg_glyph_hits, msg_unmapped))
            msg_chars = []
            msg_glyph_hits = 0
            msg_unmapped = 0
        elif val == 0xFFFE:
            msg_chars.append('\n')
        elif val >= 0xFB00:
            pass
        elif str(val) in gmap:
            msg_chars.append(gmap[str(val)])
            msg_glyph_hits += 1
        elif val < 1200:
            msg_chars.append(f'[{val:04X}]')
            msg_unmapped += 1
        else:
            if msg_chars and len(msg_chars) < 3:
                msg_chars = []
                msg_glyph_hits = 0
                msg_unmapped = 0

    return messages

# Check a sample of resources to assess quality
# Compare known-good (R34) vs suspicious large resources
check_ids = [34, 2096, 2095, 2090, 1285, 1286, 2435, 2451, 2343,
             # Some smaller ones from the scan
             ]

# Also load the full scan to pick some mid-range ones
scan = json.load(open('data/remaining_msg_scan.json', encoding='utf-8'))
mid_range = [r for r in scan if 10 <= r['messages'] <= 50]
check_ids.extend([r['resource'] for r in mid_range[:10]])

for rid in check_ids:
    msgs = decode_resource(rid)
    if msgs is None:
        print(f"R{rid}: file not found")
        continue

    # Quality: ratio of mapped glyphs to unmapped
    total_hits = sum(m[1] for m in msgs)
    total_unmapped = sum(m[2] for m in msgs)
    total_ratio = total_hits / max(1, total_hits + total_unmapped)

    # Show first 3 messages with decent length
    good_msgs = [(t,h,u) for t,h,u in msgs if len(t) >= 5 and h > u]
    noisy_msgs = [(t,h,u) for t,h,u in msgs if u > h]

    print(f"\nR{rid}: {len(msgs)} msgs, quality={total_ratio:.1%}, good={len(good_msgs)}, noisy={len(noisy_msgs)}")
    if good_msgs:
        for t, h, u in good_msgs[:3]:
            print(f"  GOOD: {t[:80]}")
    if noisy_msgs:
        for t, h, u in noisy_msgs[:2]:
            print(f"  NOISY: {t[:80]}")
