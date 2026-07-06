import json, struct, os, sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath("tools"))
from patch_section1_offsets import parse_sec2_group_offsets
raw=open("extracted/packdata_raw/1197_type02.raw","rb").read()
s2size=struct.unpack_from("<I",raw,0x14)[0]; s2off=struct.unpack_from("<I",raw,0x18)[0]
sec2=raw[s2off:s2off+s2size]; groups,_=parse_sec2_group_offsets(sec2)
n=len(sec2)//2; words=[struct.unpack_from(">H",sec2,i*2)[0] for i in range(n)]
fff0_groups=[gi for gi,(a,b) in enumerate(groups) if b>a and words[a]==0xFFF0]
print("FFF0-leading groups:", fff0_groups)
# how many words of leading FFF0-run before first real glyph?
for gi in fff0_groups:
    a,b=groups[gi]; g=words[a:b]
    lead=[]
    for w in g:
        if w>=0xFB00: lead.append(w)
        else: break
    print("  g%d leading-ctrls: %s  next: %04X" % (gi," ".join("%04X"%w for w in lead), g[len(lead)] if len(lead)<len(g) else 0xFFFF))

# Now cross-ref these to batch_01 to see authored english
d=json.load(open("data/type2_translated/batch_01.json",encoding="utf-8"))
bm={(e["resource"],e["msg_index"]):e for e in d if isinstance(e,dict) and "resource" in e and "msg_index" in e}
for gi in fff0_groups:
    e=bm.get((1197,gi))
    if e:
        print("  g%d JP=%r EN=%r" % (gi, e["japanese"][:40], e["english"][:40]))
    else:
        print("  g%d : NOT in batch_01 (untranslated)" % gi)
