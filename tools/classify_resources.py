import json, struct, os, sys
RESOURCE_DIR = 'C:/Programmieren/wizardrytranslation/extracted/packdata_resources'
MANIFEST_PATH = os.path.join(RESOURCE_DIR, 'manifest.json')
OUTPUT_PATH = 'C:/Programmieren/wizardrytranslation/dumps/resource_classification.json'
def read_file(path):
    with open(path, 'rb') as f: return f.read()
def check_magic(data):
    if len(data) < 4: return None
    h4 = data[:4]
    h8 = data[:8] if len(data) >= 8 else b''
    if h4 == b'RIFF': return 'audio_riff'
    if h4 == b'VAGp': return 'audio_vag'
    if h4 == b'TIM2': return 'texture_tim2'
    if h4 == b'TMX0': return 'texture_tmx0'
    if h4 == bytes([0x12,0x12,0x12,0x12]): return 'compressed_tmz'
    if h8 == b'\x89PNG\r\n\x1a\n': return 'image_png'
    if h4[:3] == b'\x00\x00\x01': return 'video_mpeg'
    if h4[:2] == b'BM': return 'image_bmp'
    return None
def count_msg_markers(data):
    ffff = fffe = 0
    if len(data) < 2: return 0, 0
    for i in range(0, len(data)-1, 2):
        w = (data[i] << 8) | data[i+1]
        if w == 0xFFFF: ffff += 1
        elif w == 0xFFFE: fffe += 1
    return ffff, fffe
def count_sjis_pairs(data):
    count = i = 0
    while i < len(data)-1:
        lead, trail = data[i], data[i+1]
        if (0x81 <= lead <= 0x9F or 0xE0 <= lead <= 0xEF):
            if (0x40 <= trail <= 0x7E or 0x80 <= trail <= 0xFC):
                count += 1; i += 2; continue
        i += 1
    return count
def check_floats(data):
    chunk = data[:1024]
    if len(chunk) < 4: return 0
    c = 0
    for i in range(0, len(chunk)-3, 4):
        val = struct.unpack_from('<f', chunk, i)[0]
        if val != 0.0 and abs(val) > 1e-6 and abs(val) < 1e6:
            eb = (chunk[i+3] & 0x7F) << 1 | (chunk[i+2] >> 7)
            if 20 < eb < 230: c += 1
    return c
def find_ascii_runs(data, min_len=4):
    runs = cur = 0
    for b in data:
        if 0x20 <= b <= 0x7E: cur += 1
        else:
            if cur >= min_len: runs += 1
            cur = 0
    if cur >= min_len: runs += 1
    return runs
def classify_resource(entry):
    fp = os.path.join(RESOURCE_DIR, entry['filename'])
    if not os.path.exists(fp): return {'error': 'file_not_found'}
    data = read_file(fp)
    size = len(data)
    first16 = data[:16].hex() if len(data) >= 16 else data.hex()
    cls = []
    magic = check_magic(data)
    if magic:
        cls.append(magic)
    else:
        ffff, fffe = count_msg_markers(data)
        if ffff >= 5 and fffe >= 3: cls.append('msg_structure')
        sjis = count_sjis_pairs(data)
        if sjis >= 10: cls.append('has_sjis')
        fc = check_floats(data)
        if fc >= 20: cls.append('likely_3d_model')
        ar = find_ascii_runs(data)
        if ar >= 5: cls.append('has_ascii_strings')
    if not cls: cls.append('unknown')
    r = {'index': entry['index'], 'type_code': entry.get('type_code',-1), 'size': size, 'first_16_bytes': first16, 'classifications': cls}
    if not magic:
        if 'msg_structure' in cls: r['ffff_count']=ffff; r['fffe_count']=fffe
        if 'has_sjis' in cls: r['sjis_pair_count']=sjis
        if 'likely_3d_model' in cls: r['float_count']=fc
        if 'has_ascii_strings' in cls: r['ascii_run_count']=ar
    return r
def main():
    with open(MANIFEST_PATH) as f: manifest = json.load(f)
    print(f'Classifying {len(manifest)} resources...')
    results = []; cats = {}; msg_idx = []; sjis_idx = []; skipped = 0
    for i, entry in enumerate(manifest):
        if entry.get('skipped'): skipped += 1; continue
        r = classify_resource(entry)
        results.append(r)
        for c in r.get('classifications',[]): cats[c] = cats.get(c,0)+1
        if 'msg_structure' in r.get('classifications',[]): msg_idx.append(entry['index'])
        if 'has_sjis' in r.get('classifications',[]): sjis_idx.append(entry['index'])
        if (i+1) % 500 == 0: print(f'  Processed {i+1}/{len(manifest)}...')
    output = {'total_resources': len(manifest), 'classified': len(results), 'skipped_outliers': skipped, 'summary': cats, 'msg_resource_indices': msg_idx, 'sjis_resource_indices': sjis_idx, 'resources': results}
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, 'w') as f: json.dump(output, f, indent=1)
    print(f'\nWrote classification to {OUTPUT_PATH}')
    print('\n' + '='*60)
    print('RESOURCE CLASSIFICATION SUMMARY')
    print('='*60)
    print(f'Total resources in manifest: {len(manifest)}')
    print(f'Classified: {len(results)}')
    print(f'Skipped (outliers): {skipped}')
    print()
    for cat in sorted(cats.keys()): print(f'  {cat:25s}: {cats[cat]:5d}')
    print()
    print(f'MSG resources (dialogue): {len(msg_idx)}')
    if msg_idx: print(f'  Indices: {msg_idx}')
    print()
    print(f'SJIS resources (text data): {len(sjis_idx)}')
    if sjis_idx:
        for j in range(0, len(sjis_idx), 20): print(f'  {sjis_idx[j:j+20]}')
    print()
    tex = cats.get('texture_tim2',0)+cats.get('texture_tmx0',0)+cats.get('compressed_tmz',0)
    aud = cats.get('audio_riff',0)+cats.get('audio_vag',0)
    mod = cats.get('likely_3d_model',0)
    unk = cats.get('unknown',0)
    print(f'Texture resources: {tex}')
    print(f'Audio resources:   {aud}')
    print(f'3D model (likely): {mod}')
    print(f'Unknown:           {unk}')
if __name__ == '__main__': main()
