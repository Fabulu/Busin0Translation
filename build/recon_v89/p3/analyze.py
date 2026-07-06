import sys, os, struct, json
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath("tools"))
from patch_section1_offsets import (parse_sec2_group_offsets, group_choice_markers,
    _split_control_and_text, HEADER_SIZE)

def load_groups(path):
    raw = open(path,'rb').read()
    sec2_size = struct.unpack_from("<I", raw, 0x14)[0]
    sec2_off  = struct.unpack_from("<I", raw, 0x18)[0]
    sec2 = raw[sec2_off:sec2_off+sec2_size]
    groups, trailing = parse_sec2_group_offsets(sec2)
    n = len(sec2)//2
    words = [struct.unpack_from(">H", sec2, i*2)[0] for i in range(n)]
    return words, groups

words, groups = load_groups("extracted/packdata_raw/1197_type02.raw")
gs,ge = groups[917]
g = words[gs:ge]
print("pristine g917 choice markers:", [hex(w) for w in group_choice_markers(g)])
lead, text, trail = _split_control_and_text(g)
print("leading ctrls:", [hex(w) for w in lead])
print("trailing ctrls:", [hex(w) for w in trail])

# How common is a leading FFF0 across all type-02 groups? Is it usually preserved & does it render?
# Count groups starting with FFF0 in pristine R1197
cnt_fff0 = sum(1 for (a,b) in groups if b>a and words[a]==0xFFF0)
print("R1197 groups starting with FFF0:", cnt_fff0, "of", len(groups))

# Show a few other FFF0-leading groups
shown=0
for gi,(a,b) in enumerate(groups):
    if b>a and words[a]==0xFFF0 and gi!=917:
        gm = json.load(open("data/msg_glyph_map.json",encoding="utf-8")) if shown==0 else gm
        print("  g%d: %s" % (gi, " ".join("%04X"%w for w in words[a:min(b,a+8)])))
        shown+=1
        if shown>=8: break
