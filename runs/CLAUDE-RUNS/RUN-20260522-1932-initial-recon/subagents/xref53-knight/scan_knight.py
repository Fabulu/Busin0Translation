import struct, os, json, sys

RESDIR = r"C:\Programmieren\wizardrytranslation\extracted\packdata_resources"

with open(r"C:\Programmieren\wizardrytranslation\dumps\resource_classification.json") as f:
    cls = json.load(f)
msg_indices = cls["msg_resource_indices"]

def find_resource_file(idx):
    for fname in os.listdir(RESDIR):
        if fname.startswith(f"{idx:04d}_"):
            return os.path.join(RESDIR, fname)
    return None

def parse_messages(data):
    messages = []
    i = 0
    while i < len(data) - 1:
        val = struct.unpack(">H", data[i:i+2])[0]
        if val == 0xFFFF:
            msg_glyphs = []
            fffe_count = 0
            j = i + 2
            while j < len(data) - 1:
                v = struct.unpack(">H", data[j:j+2])[0]
                if v == 0xFFFF:
                    break
                elif v == 0xFFFE:
                    msg_glyphs.append("FFFE")
                    fffe_count += 1
                else:
                    msg_glyphs.append(v)
                j += 2
            messages.append({"glyphs": msg_glyphs, "fffe_count": fffe_count, "offset": i})
            i = j
        else:
            i += 2
    return messages

candidates = []

for idx in msg_indices:
    path = find_resource_file(idx)
    if not path:
        continue
    with open(path, "rb") as f:
        data = f.read()
    
    messages = parse_messages(data)
    
    for mi, msg in enumerate(messages):
        glyphs = msg["glyphs"]
        text_glyphs = [g for g in glyphs if g != "FFFE"]
        
        if len(text_glyphs) != 38 or msg["fffe_count"] != 2:
            continue
        
        count_87 = text_glyphs.count(87)
        if count_87 < 2:
            continue
        
        count_131 = text_glyphs.count(131)
        if count_131 < 1:
            continue
        
        count_97 = text_glyphs.count(97)
        if count_97 < 1:
            continue
        
        lines = []
        current_line = []
        for g in glyphs:
            if g == "FFFE":
                lines.append(current_line)
                current_line = []
            else:
                current_line.append(g)
        lines.append(current_line)
        
        if len(lines) != 3:
            continue
        if len(lines[0]) != 11 or len(lines[1]) != 15 or len(lines[2]) != 12:
            continue
        
        score = 0
        if lines[0][1] == 87: score += 1
        if lines[0][3] == 91: score += 1
        if lines[0][8] == 87: score += 1
        if lines[1][4] == 24: score += 1
        if lines[2][0] == 131: score += 1
        if lines[2][1] == 97: score += 1
        
        candidates.append({
            "resource": idx,
            "msg_index": mi,
            "offset": msg["offset"],
            "score": score,
            "lines": lines,
            "all_glyphs": glyphs
        })
        print(f"Resource {idx}, msg {mi}: score={score}/6, lines={[len(l) for l in lines]}")
        print(f"  Line 0: {lines[0]}")
        print(f"  Line 1: {lines[1]}")
        print(f"  Line 2: {lines[2]}")

print(f"\nTotal candidates: {len(candidates)}")
candidates.sort(key=lambda x: -x["score"])
if candidates:
    best = candidates[0]
    print(f"\nBest match: resource {best['resource']}, msg {best['msg_index']}, score {best['score']}/6")
    print(f"Lines: {best['lines']}")
    
    with open(r"C:\Programmieren\wizardrytranslation\runs\CLAUDE-RUNS\RUN-20260522-1932-initial-recon\subagents\xref53-knight\candidates.json", "w") as f:
        json.dump(candidates, f, indent=2, default=str)
