import struct, json, os

os.chdir('C:/Programmieren/wizardrytranslation')
gmap = json.load(open('data/msg_glyph_map.json', encoding='utf-8'))
manifest = json.load(open('extracted/packdata_resources/manifest.json', encoding='utf-8'))

# Already translated resources
translated_t1 = {34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,720,1053,1908,2124,2654}

results = []
total_new_messages = 0

for i, entry in enumerate(manifest):
    if entry.get('skipped'): continue
    if i in translated_t1: continue

    tc = entry['type_code']
    if tc != 1: continue  # focus on type-01 for now

    fname = f"{i:04d}_type{tc:02d}.raw"
    path = f'extracted/packdata_raw/{fname}'
    if not os.path.exists(path): continue

    data = open(path, 'rb').read()
    if len(data) < 20: continue

    # Scan for MSG-like patterns: consecutive BE uint16 values in glyph range followed by FFFF
    messages = []
    msg_chars = []

    for j in range(0, len(data)-1, 2):
        val = struct.unpack_from('>H', data, j)[0]
        if val == 0xFFFF:
            if len(msg_chars) >= 3:
                text = ''.join(msg_chars)
                if len(text) >= 3:
                    messages.append(text)
            msg_chars = []
        elif val == 0xFFFE:
            msg_chars.append('\n')
        elif val >= 0xFB00:
            pass  # control code
        elif str(val) in gmap:
            msg_chars.append(gmap[str(val)])
        elif val < 1200:
            msg_chars.append(f'[{val:04X}]')
        else:
            # Not a valid glyph - might be binary data
            if msg_chars and len(msg_chars) < 3:
                msg_chars = []

    if messages:
        # Filter: keep only resources with substantial text (not just noise)
        real_msgs = [m for m in messages if len(m.replace('[','').replace(']','')) >= 3]
        if real_msgs:
            sample = real_msgs[0][:60] if real_msgs else ''
            results.append({
                'resource': i,
                'type': tc,
                'size': len(data),
                'messages': len(real_msgs),
                'sample': sample
            })
            total_new_messages += len(real_msgs)

# Sort by message count
results.sort(key=lambda x: -x['messages'])

print(f'Type-01 resources with MSG text (excluding already translated): {len(results)}')
print(f'Total new messages found: {total_new_messages}')
print()
print('Top 30 by message count:')
for r in results[:30]:
    print(f"  R{r['resource']:4d}: {r['messages']:5d} msgs, {r['size']:8d} bytes | {r['sample']}")
print()
print('Resources with 10+ messages:')
big = [r for r in results if r['messages'] >= 10]
print(f'  Count: {len(big)}')
print(f'  Total messages: {sum(r["messages"] for r in big)}')
print()
print('All results summary by message-count bracket:')
for lo, hi, label in [(1,4,'1-3 msgs'), (4,10,'4-9 msgs'), (10,50,'10-49 msgs'), (50,200,'50-199 msgs'), (200,99999,'200+ msgs')]:
    bracket = [r for r in results if lo <= r['messages'] < hi]
    if bracket:
        print(f'  {label}: {len(bracket)} resources, {sum(r["messages"] for r in bracket)} messages')

# Save full results
json.dump(results, open('data/remaining_msg_scan.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print(f'\nSaved to data/remaining_msg_scan.json')
