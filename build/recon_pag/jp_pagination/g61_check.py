import sys, os, struct, json, glob
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath('tools'))
from sec1_disasm import walk, extract_records
GM=json.load(open('data/msg_glyph_map.json',encoding='utf-8'))
HEADER_SIZE=0x20
OPEN=59; CLOSE=61
def load_sec(d):
    s=struct.unpack_from('<I',d,0x14)[0]; o=struct.unpack_from('<I',d,0x18)[0]
    return bytes(d[HEADER_SIZE:o]), bytes(d[o:o+s])
def parse_groups(sec2):
    n=len(sec2)//2; words=[struct.unpack_from('>H',sec2,i*2)[0] for i in range(n)]
    groups=[];start=0
    for i,w in enumerate(words):
        if w==0xFFFF: groups.append((start,i)); start=i+1
    return groups,words,start

# (A) KNOWN narration block R1196 g567-578: does any contain glyph 61 (ゴ) or 59 (イ)?
d=open('extracted/packdata_raw/1196_type02.raw','rb').read()
sec1,sec2=load_sec(d); groups,words,_=parse_groups(sec2)
print("=== KNOWN narration R1196 g567-578: glyph 59/61 presence ===")
for gi in range(567,579):
    gs,ge=groups[gi]; seg=words[gs:ge]
    o59=[k for k,w in enumerate(seg) if w==59]
    o61=[k for k,w in enumerate(seg) if w==61]
    txt=''.join(GM.get(str(w),'·') if w<0xFB00 else '/' for w in seg)
    print(f"  g{gi}: 59@{o59} 61@{o61}  first={seg[0] if seg else '-'} last={seg[-1] if seg else '-'}")

# (B) Corpus: for blocks where glyph 61 appears, is it a structural TERMINATOR?
#  Check: in DIALOGUE-suspected groups, does each text run end with 61 right
#  before a FFFE/FFD2/FFFF?  And does glyph 59 OPEN right after group-start/name?
# Count blocks where 61 is the LAST non-control glyph of the block.
def block_groups(words,groups,off,cnt,find):
    pass
# Simpler: across all groups, classify group as dialogue if last non-control glyph==61
def last_text(seg):
    for w in reversed(seg):
        if w<0xFB00: return w
    return None
def first_text(seg):
    for w in seg:
        if w<0xFB00: return w
    return None
tot=0; end61=0; has61_notend=0; ffd2_groups=0; ffd2_end61=0
narr_61_inside=0
for f in sorted(glob.glob('extracted/packdata_raw/*_type02.raw')):
    d=open(f,'rb').read()
    try: sec1,sec2=load_sec(d)
    except: continue
    groups,words,_=parse_groups(sec2)
    for gs,ge in groups:
        seg=words[gs:ge]
        if not seg: continue
        tot+=1
        lt=last_text(seg)
        h61=61 in seg
        hf=0xFFD2 in seg
        if lt==61: end61+=1
        if h61 and lt!=61: has61_notend+=1
        if hf:
            ffd2_groups+=1
            if lt==61: ffd2_end61+=1
print()
print(f"=== Corpus group-level glyph-61 terminator test ===")
print(f"total groups: {tot}")
print(f"groups ending in glyph 61 (dialogue-close): {end61}")
print(f"groups containing 61 but NOT ending in it: {has61_notend}")
print(f"FFD2 groups: {ffd2_groups}; of which end in 61: {ffd2_end61}")
