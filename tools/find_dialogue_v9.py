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

# New hypothesis for hiragana glyph IDs (from resource 37 display table):
# あ=112 い=113 う=114 え=115 お=116
# か=117 き=118 く=119 け=120 こ=121
# さ=122 し=123 す=124 せ=125 そ=126
# た=127 ち=128 つ=129 て=130 と=131
# な=132 に=133 ぬ=134 ね=135 の=136
# は=137 ひ=138 ふ=139 へ=140 ほ=141
# ま=142 み=143 む=144 め=145 も=146
# や=147 ゆ=148 よ=149
# ら=93 り=94
# る=150 れ=151 ろ=152
# わ=153 を=154 ん=155

# Target: なあ、教えてくれよ～。俺、早くあの事を言わなきゃ、ならないんだよ。
# Known hiragana positions:
# な=132 at pos 0, 21, 25, 27 (or wherever in the message)
# あ=112 at pos 1, 15
# え=115 at pos 4
# て=130 at pos 5
# く=119 at pos 6, 14
# れ=151 at pos 7
# よ=149 at pos 8, 31
# の=136 at pos 16
# を=154 at pos 18
# わ=153 at pos 20
# き=118 at pos 22
# ら=93 at pos 26
# な=132 at pos 27
# い=113 at pos 28
# ん=155 at pos 29
# だ=? (not in hiragana mapping yet -- dakuten!)

# Wait -- ゃ (small ya) and だ (da) are dakuten variants, which need separate glyph IDs.
# The 48-glyph table might include these in the right column or elsewhere.

# For now, let me search for the HIRAGANA subsequence pattern:
# Positions with known hiragana:
# 0:な(132) 1:あ(112) 4:え(115) 5:て(130) 6:く(119) 7:れ(151) 8:よ(149)
# 14:く(119) 15:あ(112) 16:の(136) 18:を(154) 20:わ(153) 21:な(132)
# 22:き(118) 25:な(132) 26:ら(93) 27:な(132) 28:い(113) 29:ん(155) 31:よ(149)

# Let me search for any FFFF block containing:
# - glyph 132 (な) at least 4 times
# - glyph 112 (あ) at least 2 times
# - glyph 119 (く) at least 2 times
# - glyph 149 (よ) at least 2 times
# - glyph 113 (い) at least 1 time

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
            
            c132 = tg.count(132)  # な
            c112 = tg.count(112)  # あ
            c119 = tg.count(119)  # く
            c149 = tg.count(149)  # よ
            c113 = tg.count(113)  # い
            
            if c132 >= 4 and c112 >= 2 and c119 >= 2 and c149 >= 2 and c113 >= 1:
                if 25 <= len(tg) <= 50:
                    print("HIT: res=%d s=%d off=0x%X tlen=%d" % (idx, sn, i, len(tg)))
                    print("  na=%d a=%d ku=%d yo=%d i=%d" % (c132, c112, c119, c149, c113))
                    # Show parts
                    parts = []
                    cur = []
                    for g in gl:
                        if g == 0xFFFE:
                            if cur:
                                parts.append(cur)
                            cur = []
                        else:
                            cur.append(g)
                    if cur:
                        parts.append(cur)
                    for pi, p in enumerate(parts):
                        print("    p[%d]: %s" % (pi, p))
            
            sn += 1
            i = j
        else:
            i += 2

print("DONE")
