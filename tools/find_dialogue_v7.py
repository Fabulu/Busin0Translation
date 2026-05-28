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

# Full structural match with all 6 repeat groups
# But allow text length to be 30-36 (not exactly 33) in case I miscounted

results = []
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
            
            # Filter: keep only non-zero, non-control glyphs
            # Control codes are >= 0xFFC0
            # Also filter 0 (null), 1 (space), 2, 3, 4 (likely special)
            tg = [g for g in gl if 5 <= g < 0xFFC0]
            
            if 28 <= len(tg) <= 50:
                c = Counter(tg)
                for glyph, count in c.items():
                    if count >= 4 and glyph > 10:  # skip low values
                        positions = [p for p, g in enumerate(tg) if g == glyph]
                        for start in positions:
                            # Try text lengths 30-36
                            for tlen in range(30, 37):
                                if start + tlen > len(tg):
                                    break
                                sub = tg[start:start+tlen]
                                
                                # Check glyph at pos 0 appears 4x in the sub
                                na = sub[0]
                                na_pos = [p for p, g in enumerate(sub) if g == na]
                                if len(na_pos) < 4:
                                    continue
                                
                                # sub[1] should appear at least once more
                                a = sub[1]
                                a_count = sub.count(a)
                                if a_count < 2:
                                    continue
                                
                                # sub[2] should appear at least 2 more times
                                comma = sub[2]
                                comma_count = sub.count(comma)
                                if comma_count < 3:
                                    continue
                                
                                # All three (na, a, comma) must be distinct
                                if na == a or na == comma or a == comma:
                                    continue
                                
                                # sub[2] should be different from sub[3-5]
                                # (、 is punctuation, followed by kanji)
                                
                                # sub[1] == sub[~15] (あ at start and middle)
                                # The second あ should be roughly at position 13-17
                                a_pos = [p for p, g in enumerate(sub) if g == a]
                                found_mid_a = any(12 <= p <= 18 for p in a_pos if p > 0)
                                if not found_mid_a:
                                    continue
                                
                                results.append((idx, sn, i, start, tlen, sub, na, a, comma))
            
            sn += 1
            i = j
        else:
            i += 2

print("Found %d matches" % len(results))
for idx, sn, foff, toff, tlen, sub, na, a, comma in results[:30]:
    print("res=%d s=%d off=0x%X toff=%d tlen=%d na=%d a=%d comma=%d" % (idx, sn, foff, toff, tlen, na, a, comma))
    print("  sub=%s" % sub[:40])
print("DONE")
