import struct, os, json
from collections import Counter

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

# Super relaxed: look for any FFFF block where text glyphs 28-45 long,
# with one glyph appearing 4+ times AND that glyph is at position 0 or offset+0
# (since な starts the text)

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
            
            if 28 <= len(tg) <= 50:
                c = Counter(tg)
                # Find glyphs that appear 4+ times
                for glyph, count in c.items():
                    if count >= 4:
                        positions = [p for p, g in enumerate(tg) if g == glyph]
                        # Check if any position could be the start of "なあ..."
                        # The key: after the "な" at pos X, the next 33 chars should
                        # contain that same glyph 3 more times
                        for start in positions:
                            if start + 33 <= len(tg):
                                sub = tg[start:start+33]
                                sub_positions = [p for p, g in enumerate(sub) if g == glyph]
                                if len(sub_positions) >= 4 and sub_positions[0] == 0:
                                    # Check if sub[1] appears at position 15 too (あ)
                                    if sub[1] == sub[15] if len(sub) > 15 else False:
                                        # Check 、pattern: sub[2]==sub[12]
                                        if sub[2] == sub[12] if len(sub) > 12 else False:
                                            print("MATCH: res=%d s=%d off=0x%X start=%d gl4=%d" % (idx, sn, i, start, glyph))
                                            print("  sub=%s" % sub)
                                            print("  positions_in_sub=%s" % sub_positions)
            
            sn += 1
            i = j
        else:
            i += 2

print("DONE")
