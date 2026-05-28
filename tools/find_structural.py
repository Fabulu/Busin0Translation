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

# Target text: なあ、教えてくれよ～。俺、早くあの事を言わなきゃ、ならないんだよ。
# 33 characters
# Structural constraints (0-indexed):
# pos[0]==pos[21]==pos[25]==pos[27]  (な x4)
# pos[1]==pos[15]                    (あ x2)
# pos[2]==pos[12]==pos[24]           (、x3)
# pos[6]==pos[14]                    (く x2)
# pos[8]==pos[31]                    (よ x2)
# pos[10]==pos[32]                   (。x2)
# All unique: pos[3](教),pos[4](え),pos[5](て),pos[7](れ),pos[9](～),
#             pos[11](俺),pos[13](早),pos[16](の),pos[17](事),pos[18](を),
#             pos[19](言),pos[20](わ),pos[22](き),pos[23](ゃ),pos[26](ら),
#             pos[28](い),pos[29](ん),pos[30](だ)

def check_structural_match(tg):
    """Check if glyph array matches the structural pattern of the target text."""
    if len(tg) != 33:
        return False
    # な: pos 0,21,25,27 must be same
    if not (tg[0] == tg[21] == tg[25] == tg[27]):
        return False
    # あ: pos 1,15 must be same
    if tg[1] != tg[15]:
        return False
    # 、: pos 2,12,24 must be same
    if not (tg[2] == tg[12] == tg[24]):
        return False
    # く: pos 6,14 must be same
    if tg[6] != tg[14]:
        return False
    # よ: pos 8,31 must be same
    if tg[8] != tg[31]:
        return False
    # 。: pos 10,32 must be same
    if tg[10] != tg[32]:
        return False
    # All the "same" glyphs must be distinct from each other
    na = tg[0]
    a = tg[1]
    comma = tg[2]
    ku = tg[6]
    yo = tg[8]
    maru = tg[10]
    if len(set([na, a, comma, ku, yo, maru])) != 6:
        return False
    return True

def check_structural_match_relaxed(tg, offset=0):
    """Check with offset into the array (for when text is preceded by speaker name)."""
    if len(tg) < offset + 33:
        return False
    sub = tg[offset:offset+33]
    return check_structural_match(sub)

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
            tg = [g for g in gl if g < 0xFF00]
            
            # Try exact match (text is 33 chars)
            if check_structural_match(tg):
                results.append((idx, sn, i, "exact", tg))
            
            # Try with speaker name prepended (4-8 chars before the 33)
            for off in range(1, 12):
                if check_structural_match_relaxed(tg, off):
                    results.append((idx, sn, i, "offset_%d" % off, tg))
            
            sn += 1
            i = j
        else:
            i += 2

print("Found %d structural matches" % len(results))
for idx, sn, off, mtype, tg in results[:20]:
    print("  res=%d s=%d off=0x%X type=%s tlen=%d" % (idx, sn, off, mtype, len(tg)))
    print("    tg=%s" % tg[:50])
    if mtype.startswith("offset_"):
        o = int(mtype.split("_")[1])
        sub = tg[o:o+33]
        print("    sub=%s" % sub)
        print("    na=%d a=%d comma=%d ku=%d yo=%d maru=%d" % (sub[0], sub[1], sub[2], sub[6], sub[8], sub[10]))
print("DONE")
