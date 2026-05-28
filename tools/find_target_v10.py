import struct, os, json

RESDIR = "C:/Programmieren/wizardrytranslation/extracted/packdata_resources"
with open("C:/Programmieren/wizardrytranslation/dumps/resource_classification.json") as f:
    cls = json.load(f)
msg_indices = cls["msg_resource_indices"]

files = os.listdir(RESDIR)
fmap = {}
for f in files:
    try:
        fmap[int(f[:4])] = os.path.join(RESDIR, f)
    except:
        pass

# Search with confirmed glyph IDs
# Text: なあ、教えてくれよ～。俺、早くあの事を言わなきゃ、ならないんだよ。
# Confirmed: な=132, あ=112, て=130, い=113, の=136
# Pattern: first text glyph = 132 (な), second = 112 (あ)
# So look for 132, 112 adjacent at any position in the block

for idx in msg_indices:
    if idx not in fmap:
        continue
    with open(fmap[idx], "rb") as fh:
        data = fh.read()
    i = 0
    sn = 0
    while i < len(data) - 1:
        val = struct.unpack(">H", data[i:i+2])[0]
        if val == 0xFFFF:
            gl = []
            j = i + 2
            while j < len(data) - 1:
                g = struct.unpack(">H", data[j:j+2])[0]
                if g == 0xFFFF:
                    break
                gl.append(g)
                j += 2
            
            tg = [g for g in gl if g < 0xFFC0]
            
            # Find 132, 112 adjacent (なあ)
            for p in range(len(tg) - 1):
                if tg[p] == 132 and tg[p+1] == 112:
                    # Check: after なあ, within next 30 chars, should see:
                    # て(130) and another な(132) 
                    rest = tg[p+2:p+35]
                    if 130 in rest and rest.count(132) >= 3:
                        # Also check for い(113) and の(136)
                        if 113 in rest and 136 in rest:
                            print("STRONG HIT: res=%d s=%d off=0x%X pos=%d tlen=%d" % (idx, sn, i, p, len(tg)))
                            sub = tg[p:min(p+35, len(tg))]
                            print("  sub=%s" % sub)
                            # Also show FFFE-split parts
                            parts = []
                            cur = []
                            for g in gl:
                                if g == 0xFFFE:
                                    parts.append(cur)
                                    cur = []
                                else:
                                    cur.append(g)
                            if cur:
                                parts.append(cur)
                            for pi, pp in enumerate(parts):
                                tp = [g for g in pp if g < 0xFFC0]
                                if tp:
                                    print("    p[%d]: %s" % (pi, tp))
                    elif 130 in rest:
                        print("  partial: res=%d s=%d pos=%d (has te, na_rest=%d)" % (idx, sn, p, rest.count(132)))
            
            sn += 1
            i = j
        else:
            i += 2

print("DONE")
