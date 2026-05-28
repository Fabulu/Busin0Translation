import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

RES_DIR = "C:/Programmieren/wizardrytranslation/extracted/packdata_resources"

# Check resources near known MSG resources and some specific candidates
test_indices = [33, 50, 635, 637, 639, 691, 703, 705, 707, 709,
                2102, 2175, 2212, 2640, 1192, 2611, 2127, 2600,
                1, 3, 4, 5, 17, 31, 605, 608, 609, 612, 615, 620, 621]

for idx in test_indices:
    candidates = [f for f in os.listdir(RES_DIR) if f.startswith(f'{idx:04d}_')]
    if not candidates:
        continue
    fpath = os.path.join(RES_DIR, candidates[0])
    data = open(fpath, 'rb').read()
    chunks = data.split(b'\x00')
    jp_chunks = []
    for c in chunks:
        if len(c) < 3:
            continue
        try:
            t = c.decode('shift_jis', errors='strict')
            jp = sum(1 for ch in t if '\u3040' <= ch <= '\u9FFF')
            hira = sum(1 for ch in t if '\u3041' <= ch <= '\u3093')
            if jp >= 2 and hira >= 1:
                jp_chunks.append((t[:80], jp, hira))
        except Exception:
            pass
    if jp_chunks:
        print(f'=== Resource {idx} ({candidates[0]}, {len(data)} bytes): {len(jp_chunks)} JP strings ===')
        for s, jp, hira in jp_chunks[:8]:
            print(f'  [{jp}jp {hira}hi] {s}')
    else:
        print(f'--- Resource {idx} ({candidates[0]}, {len(data)} bytes): no JP text ---')
