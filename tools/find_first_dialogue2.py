import struct, os, json

RESDIR = r"C:\Programmieren\wizardrytranslation\extracted\packdata_resources"

def read_resource(idx):
    for f in os.listdir(RESDIR):
        if f.startswith(f"{idx:04d}_"):
            with open(os.path.join(RESDIR, f), "rb") as fh:
                return fh.read()
    return None

def extract_all_glyphs(data):
    seqs = []
    i = 0
    while i < len(data) - 1:
        val = struct.unpack(">H", data[i:i+2])[0]
        if val == 0xFFFF:
            glyphs = []
            j = i + 2
            while j < len(data) - 1:
                g = struct.unpack(">H", data[j:j+2])[0]
                if g == 0xFFFF:
                    break
                glyphs.append(g)
                j += 2
            if glyphs:
                seqs.append({"offset": i, "glyphs": glyphs})
            i = j
        else:
            i += 2
    return seqs

cls_path = r"C:\Programmieren\wizardrytranslation\dumps\resource_classification.json"
with open(cls_path) as f:
    cls = json.load(f)
msg_indices = cls["msg_resource_indices"]

print(f"Searching {len(msg_indices)} MSG resources...")
candidates = []

for page_offset in [0, 57, 114, 171, 228, 285]:
    a_id = 86 + page_offset
    e_id = 89 + page_offset
    ku_id = 93 + page_offset
    i_id = 87 + page_offset
    ki_id = 92 + page_offset

    for idx in msg_indices:
        data = read_resource(idx)
        if data is None:
            continue
        seqs = extract_all_glyphs(data)
        for si, seq in enumerate(seqs):
            gl = seq["glyphs"]
            tg = [g for g in gl if g < 0xFF00]
            if len(tg) < 20:
                continue
            for start in range(min(len(tg) - 5, 10)):
                if tg[start + 1] == a_id and tg[start + 4] == e_id:
                    if ku_id in tg[start + 5:]:
                        score = 10 + page_offset
                        if tg.count(a_id) >= 2: score += 5
                        if ki_id in tg: score += 3
                        if i_id in tg: score += 3
                        candidates.append({
                            "resource": idx, "seq": si, "offset": seq["offset"],
                            "text_glyphs": tg, "glyphs": gl,
                            "score": score, "start": start, "page": page_offset
                        })
                        break

candidates.sort(key=lambda x: -x["score"])
print(f"Found {len(candidates)} candidates")
for c in candidates[:15]:
    print(f"  res={c[chr(114)+chr(101)+chr(115)+chr(111)+chr(117)+chr(114)+chr(99)+chr(101)]}, seq={c[chr(115)+chr(101)+chr(113)]}, page={c[chr(112)+chr(97)+chr(103)+chr(101)]}, score={c[chr(115)+chr(99)+chr(111)+chr(114)+chr(101)]}, tlen={len(c[chr(116)+chr(101)+chr(120)+chr(116)+chr(95)+chr(103)+chr(108)+chr(121)+chr(112)+chr(104)+chr(115)])}")
    print(f"    tg={c[chr(116)+chr(101)+chr(120)+chr(116)+chr(95)+chr(103)+chr(108)+chr(121)+chr(112)+chr(104)+chr(115)][:40]}")

