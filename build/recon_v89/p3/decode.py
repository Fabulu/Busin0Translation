import sys, os, struct, json
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath("tools"))
from patch_section1_offsets import parse_sec2_group_offsets, HEADER_SIZE

def load_groups(path):
    raw = open(path,'rb').read()
    sec2_size = struct.unpack_from("<I", raw, 0x14)[0]
    sec2_off  = struct.unpack_from("<I", raw, 0x18)[0]
    sec2 = raw[sec2_off:sec2_off+sec2_size]
    groups, trailing = parse_sec2_group_offsets(sec2)
    n = len(sec2)//2
    words = [struct.unpack_from(">H", sec2, i*2)[0] for i in range(n)]
    return words, groups, trailing

gmap = json.load(open("data/msg_glyph_map.json", encoding="utf-8"))
eng = json.load(open("data/english_glyph_table.json", encoding="utf-8"))
erev = {}
for ch,g in eng.items():
    erev.setdefault(g, ch)

def gly(w):
    if w >= 0xFB00:
        return "<%04X>" % w
    if str(w) in gmap:
        return gmap[str(w)]
    if w in erev:
        return erev[w]
    return "[%d]" % w

def show(path, gi):
    words, groups, trailing = load_groups(path)
    print("== %s  group %d  (total groups=%d) ==" % (os.path.basename(path), gi, len(groups)))
    if gi >= len(groups):
        print("  OUT OF RANGE"); return
    gs, ge = groups[gi]
    g = words[gs:ge]
    print("  words[%d:%d] len=%d" % (gs, ge, len(g)))
    print("  HEX :", " ".join("%04X" % w for w in g))
    print("  DEC :", "".join(gly(w) for w in g))

target = sys.argv[1]
for gi in [63, 917]:
    show(target, gi)
    print()
