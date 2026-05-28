import struct
import os
import json

RESDIR = "C:/Programmieren/wizardrytranslation/extracted/packdata_resources"

def read_resource(idx):
    for f in os.listdir(RESDIR):
        if f.startswith(f"{idx:04d}_"):
            path = os.path.join(RESDIR, f)
            with open(path, "rb") as fh:
                return fh.read()
    return None

def extract_messages(data):
    messages = []
    i = 0
    while i < len(data) - 1:
        val = struct.unpack(">H", data[i:i+2])[0]
        if val == 0xFFFF:
            glyphs = []
            j = i + 2
            while j < len(data) - 1:
                g = struct.unpack(">H", data[j:j+2])[0]
                if g == 0xFFFE or g == 0xFFFF:
                    break
                glyphs.append(g)
                j += 2
            messages.append({"offset": i, "glyphs": glyphs, "length": len(glyphs)})
            if j < len(data) - 1:
                nextval = struct.unpack(">H", data[j:j+2])[0]
                if nextval == 0xFFFE:
                    i = j + 2
                else:
                    i = j
            else:
                i = j + 2
        else:
            i += 2
    return messages

target_indices = list(range(34, 50)) + [636, 638]

print("Searching for first dialogue pattern...")
print("Text: na a , oshie e te ku re yo ~ . ore , haya ku a no koto wo i wa na ki xya , na ra na i n da yo .")
print("Expected ~32 glyphs, glyph 86(a) 2x, 93(ku) 2x, 89(e) 1x")
print()

candidates = []

for idx in target_indices:
    data = read_resource(idx)
    if data is None:
        continue

    msgs = extract_messages(data)

    for mi in range(len(msgs)):
        msg = msgs[mi]
        gl = msg["glyphs"]

        c86 = gl.count(86)
        c93 = gl.count(93)
        c89 = gl.count(89)
        c92 = gl.count(92)
        c87 = gl.count(87)

        if len(gl) >= 25 and len(gl) <= 40:
            if c86 >= 2 and c93 >= 2 and c89 >= 1:
                score = 0
                if len(gl) > 1 and gl[1] == 86:
                    score += 10
                if len(gl) > 4 and gl[4] == 89:
                    score += 5
                if len(gl) > 6 and gl[6] == 93:
                    score += 5

                candidates.append({
                    "resource": idx,
                    "msg_index": mi,
                    "length": len(gl),
                    "glyphs": gl,
                    "score": score,
                    "counts": {"86_a": c86, "87_i": c87, "93_ku": c93, "89_e": c89, "92_ki": c92}
                })
                print(f"  Match: res {idx}, msg {mi}, len={len(gl)}, score={score}")
                print(f"    Counts: a(86)={c86}, i(87)={c87}, ku(93)={c93}, e(89)={c89}, ki(92)={c92}")
                print(f"    Glyphs: {gl}")

    for mi in range(len(msgs)):
        msg = msgs[mi]
        gl = msg["glyphs"]
        if len(gl) == 4 and gl[1] == 126 and gl[2] == 87:
            print(f"  Speaker match: res {idx}, msg {mi}, glyphs={gl}")

print("\n=== All messages from resources 36-49 ===\n")
for idx in range(36, 50):
    data = read_resource(idx)
    if data is None:
        continue
    msgs = extract_messages(data)
    print(f"Resource {idx}: {len(msgs)} messages")
    for mi, msg in enumerate(msgs[:8]):
        gl = msg["glyphs"]
        print(f"  msg[{mi}]: len={len(gl)} glyphs={gl[:30]}{'...' if len(gl)>30 else ''}")
    if len(msgs) > 8:
        print(f"  ... ({len(msgs)} total)")
    print()

candidates.sort(key=lambda x: -x["score"])
print("\n=== Top candidates ===")
for c in candidates[:5]:
    print(f"  res={c['resource']}, msg={c['msg_index']}, len={c['length']}, score={c['score']}")
    print(f"    glyphs={c['glyphs']}")
