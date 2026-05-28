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

# Parse FFFF blocks and split by FFFE into parts
# Target: [speaker(4)] FFFE [line1(~11)] FFFE [line2(~14)] FFFE [line3(~8)] FFFE
# Or:     [speaker(4)+delim] FFFE ...
# Total text: 4 + 33 = 37 (or 5 + 33 = 38 with delimiter)

# Structural match for the 33-char text split across 3 lines:
# Line1 (11 chars): pos[0]==pos[21-11=10 in L2]... no, positions are within lines
# Let me think differently. The text across 3 FFFE-separated parts:
# Part1: な あ 、 教 え て く れ よ ～ 。  (11 chars)
# Part2: 俺 、 早 く あ の 事 を 言 わ な き ゃ 、  (14 chars) 
# Part3: な ら な い ん だ よ 。  (8 chars)
#
# Cross-part repetitions:
# な = Part1[0], Part2[10], Part3[0], Part3[2]  -- same glyph in all 4 positions
# 、 = Part1[2], Part2[1], Part2[13]  -- same glyph
# く = Part1[6], Part2[3]  -- same glyph
# あ = Part1[1], Part2[4]  -- same glyph
# よ = Part1[8], Part3[6]  -- same glyph
# 。 = Part1[10], Part3[7]  -- same glyph

def check_text_match(p1, p2, p3):
    """Check structural match across 3 parts."""
    if len(p1) != 11 or len(p2) != 14 or len(p3) != 8:
        return False
    # な: p1[0]==p2[10]==p3[0]==p3[2]
    if not (p1[0] == p2[10] == p3[0] == p3[2]):
        return False
    # 、: p1[2]==p2[1]==p2[13]
    if not (p1[2] == p2[1] == p2[13]):
        return False
    # く: p1[6]==p2[3]
    if p1[6] != p2[3]:
        return False
    # あ: p1[1]==p2[4]
    if p1[1] != p2[4]:
        return False
    # よ: p1[8]==p3[6]
    if p1[8] != p3[6]:
        return False
    # 。: p1[10]==p3[7]
    if p1[10] != p3[7]:
        return False
    return True

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
            
            # Split by FFFE into parts, filtering control codes >= 0xFFC0
            parts = []
            cur = []
            for g in gl:
                if g == 0xFFFE:
                    parts.append(cur)
                    cur = []
                elif g >= 0xFFC0:
                    pass  # skip control codes
                else:
                    cur.append(g)
            if cur:
                parts.append(cur)
            
            # Try: parts = [speaker, line1, line2, line3, ...]
            # Check if any 3 consecutive parts match the text pattern
            for start in range(len(parts) - 2):
                p1 = parts[start]
                p2 = parts[start + 1]
                p3 = parts[start + 2]
                if check_text_match(p1, p2, p3):
                    speaker = parts[start - 1] if start > 0 else None
                    results.append((idx, sn, i, start, speaker, p1, p2, p3))
            
            sn += 1
            i = j
        else:
            i += 2

print("Found %d matches" % len(results))
for idx, sn, off, start, speaker, p1, p2, p3 in results[:10]:
    print("res=%d s=%d off=0x%X partstart=%d" % (idx, sn, off, start))
    if speaker:
        print("  speaker=%s" % speaker)
    print("  line1=%s" % p1)
    print("  line2=%s" % p2)
    print("  line3=%s" % p3)
    print("  na=%d a=%d comma=%d ku=%d yo=%d maru=%d" % (p1[0], p1[1], p1[2], p1[6], p1[8], p1[10]))
print("DONE")
