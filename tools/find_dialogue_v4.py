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

# Instead of exact line lengths, search for the core pattern:
# Within a single FFFF block, look for the full 33-char text (ignoring FFFE/controls)
# The text: な あ 、 教 え て く れ よ ～ 。 俺 、 早 く あ の 事 を 言 わ な き ゃ 、 な ら な い ん だ よ 。
# Positions: 0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32

# Structural constraints on the TEXT GLYPHS (after filtering controls):
# [0]==[21]==[25]==[27]  (な, 4x)
# [1]==[15]              (あ, 2x)
# [2]==[12]==[24]        (、, 3x)
# [6]==[14]              (く, 2x)
# [8]==[31]              (よ, 2x)
# [10]==[32]             (。, 2x)

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
            
            # Get just text glyphs (filter out ALL control codes)
            tg = [g for g in gl if g < 0xFFC0]
            
            # Search for the 33-char pattern at any offset within tg
            for off in range(max(0, len(tg) - 40), len(tg) - 32):
                t = tg[off:]
                if len(t) < 33:
                    continue
                t = t[:33]  # take exactly 33
                
                ok = True
                # [0]==[21]==[25]==[27]
                if not (t[0] == t[21] == t[25] == t[27]):
                    ok = False
                if ok and t[1] != t[15]:
                    ok = False
                if ok and not (t[2] == t[12] == t[24]):
                    ok = False
                if ok and t[6] != t[14]:
                    ok = False
                if ok and t[8] != t[31]:
                    ok = False
                if ok and t[10] != t[32]:
                    ok = False
                
                if ok:
                    # Check all 6 repeated groups are distinct
                    groups = [t[0], t[1], t[2], t[6], t[8], t[10]]
                    if len(set(groups)) == 6:
                        results.append((idx, sn, i, off, t, tg))
            
            sn += 1
            i = j
        else:
            i += 2

print("Found %d matches" % len(results))
for idx, sn, foff, toff, t, tg in results[:20]:
    print("res=%d s=%d foff=0x%X toff=%d" % (idx, sn, foff, toff))
    print("  text33=%s" % t)
    print("  na=%d a=%d comma=%d ku=%d yo=%d maru=%d" % (t[0], t[1], t[2], t[6], t[8], t[10]))
    print("  full_tg_len=%d" % len(tg))
print("DONE")
