import sys, os, struct, json
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath("tools"))
from sec1_disasm import walk, extract_records
from patch_section1_offsets import parse_sec2_group_offsets, HEADER_SIZE

def load(path):
    raw = open(path,'rb').read()
    s2size = struct.unpack_from("<I", raw, 0x14)[0]
    s2off  = struct.unpack_from("<I", raw, 0x18)[0]
    sec1 = raw[HEADER_SIZE:s2off]
    sec2 = raw[s2off:s2off+s2size]
    groups,_ = parse_sec2_group_offsets(sec2)
    n=len(sec2)//2
    words=[struct.unpack_from(">H",sec2,i*2)[0] for i in range(n)]
    return raw, sec1, words, groups

for label,path in [("PRISTINE","extracted/packdata_raw/1197_type02.raw"),
                   ("BUILT","build/packdata_resources/1197_type02.raw")]:
    raw,sec1,words,groups = load(path)
    gs,ge = groups[917]
    print("=== %s g917 word range [%d,%d] (FFFF at %d) ===" % (label,gs,ge,ge))
    ok,instrs = walk(sec1)
    recs = extract_records(sec1, instrs)
    for kind in ("display","label","name_ref"):
        for r in recs.get(kind,[]):
            off=r.get("off"); cnt=r.get("cnt")
            if off is None: continue
            end=off+(cnt or 0)
            # does this record's span touch group 917?
            if off<=ge and end>gs:
                print("  %-8s pc=0x%X off=%d cnt=%d end=%d  (first word at off = %04X)"
                      % (kind, r["pc"], off, cnt, end, words[off] if off<len(words) else 0))
    print()
