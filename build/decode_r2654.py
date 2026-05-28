import struct, json, collections, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

with open("C:/Programmieren/wizardrytranslation/extracted/packdata_resources/2654_type44.bin","rb") as f:
    data = f.read()
with open("C:/Programmieren/wizardrytranslation/data/msg_glyph_map.json","r", encoding="utf-8") as f:
    gmap = json.load(f)

glyph_start = 842
messages = []
i = glyph_start
while i < len(data) - 1:
    v = struct.unpack(">H", data[i:i+2])[0]
    if v == 0xFFFF:
        glyphs = []
        j = i + 2
        while j < len(data) - 1:
            w = struct.unpack(">H", data[j:j+2])[0]
            if w == 0xFFFF: break
            glyphs.append(w)
            j += 2
        messages.append(glyphs)
        i = j
    else:
        i += 2

unk_freq = collections.Counter()
for msg in messages:
    for g in msg:
        if g != 0xFFFE and g != 0 and str(g) not in gmap:
            unk_freq[g] += 1

print("Top unknown glyphs by frequency:")
for gid, cnt in unk_freq.most_common(100):
    contexts = []
    for mi, msg in enumerate(messages):
        for pi, g in enumerate(msg):
            if g == gid:
                ctx = []
                for di in range(max(0,pi-4), min(len(msg), pi+5)):
                    gg = msg[di]
                    if gg == 0xFFFE: ctx.append("||")
                    elif gg == gid: ctx.append("***")
                    else:
                        ch = gmap.get(str(gg))
                        ctx.append(ch if ch else f"[{gg}]")
                contexts.append("".join(ctx))
                if len(contexts) >= 4: break
        if len(contexts) >= 4: break
    print(f"  {gid}: {cnt}x  {contexts}")
