import sys, os, struct, json, glob
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath('tools'))
from sec1_disasm import walk, extract_records
GM=json.load(open('data/msg_glyph_map.json',encoding='utf-8'))
HEADER_SIZE=0x20; CLOSE=61; OPEN=59
def load_sec(d):
    s=struct.unpack_from('<I',d,0x14)[0]; o=struct.unpack_from('<I',d,0x18)[0]
    return bytes(d[HEADER_SIZE:o]), bytes(d[o:o+s])
def parse_groups(sec2):
    n=len(sec2)//2; words=[struct.unpack_from('>H',sec2,i*2)[0] for i in range(n)]
    groups=[];start=0
    for i,w in enumerate(words):
        if w==0xFFFF: groups.append((start,i)); start=i+1
    return groups,words,start
def find_group(groups,w):
    for gi,(gs,ge) in enumerate(groups):
        if gs<=w<=ge: return gi
    return None
def dec(seg,lim=60):
    out=[]
    for w in seg[:lim]:
        if w==0xFFFE: out.append('/')
        elif w==0xFFD2: out.append('|')
        elif 0xFFE0<=w<=0xFFE7: out.append('«N»')
        elif w>=0xFB00: out.append('·')
        else: out.append(GM.get(str(w),'?'))
    return ''.join(out)

# THE decisive test for the user's hypothesis:
# Of ALL DISPLAY blocks that contain FFD2 (JP page-break = "JP decided to paginate"),
# does EVERY ONE also contain glyph-61 (proven-clean dialogue marker)?
# If yes: 'block has FFD2' <=> dialogue, with NO narration leak. 100% safe.
fail=[]; ok_count=0; total=0
for f in sorted(glob.glob('extracted/packdata_raw/*_type02.raw')):
    rid=int(os.path.basename(f).split('_')[0])
    d=open(f,'rb').read()
    try: sec1,sec2=load_sec(d)
    except: continue
    groups,words,_=parse_groups(sec2)
    if not groups: continue
    ok,instrs=walk(sec1); recs=extract_records(sec1,instrs)
    for r in recs['display']:
        if r['cnt']==0: continue
        gi0=find_group(groups,r['off'])
        if gi0 is None: continue
        gi1=find_group(groups,min(r['off']+r['cnt']-1,groups[-1][1])) or gi0
        seg=[]
        for gi in range(gi0,gi1+1):
            gs,ge=groups[gi]; seg+=list(words[gs:ge])
        if 0xFFD2 in seg:
            total+=1
            if CLOSE in seg or OPEN in seg: ok_count+=1
            else: fail.append((rid,list(range(gi0,gi1+1)),dec(seg)))
print(f"DISPLAY blocks containing FFD2: {total}")
print(f"  ...that ALSO contain glyph-61(ゴ) or glyph-59(イ) [dialogue bracket]: {ok_count}")
print(f"  ...that contain NEITHER (potential narration page-break): {len(fail)}")
for rid,gl,txt in fail[:20]:
    print(f"   R{rid} g{gl}: {txt}")
