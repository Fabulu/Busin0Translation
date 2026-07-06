import sys, os, struct, json
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath('tools'))
from sec1_disasm import walk, extract_records
GM=json.load(open('data/msg_glyph_map.json',encoding='utf-8'))
HEADER_SIZE=0x20
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
def dec(seg):
    out=[]
    for w in seg:
        if w==0xFFFE: out.append('/')
        elif w==0xFFD2: out.append('|')
        elif 0xFFE0<=w<=0xFFE7: out.append(f'«{w&0xF}»')
        elif w>=0xFB00: out.append(f'·{w&0xFF:02X}')
        else: out.append(GM.get(str(w),'?'))
    return ''.join(out)
d=open('extracted/packdata_raw/1197_type02.raw','rb').read()
sec1,sec2=load_sec(d); groups,words,_=parse_groups(sec2)
ok,instrs=walk(sec1); recs=extract_records(sec1,instrs)
# which 0x04 covers g905? show its off/cnt and the full group decode
for r in recs['display']:
    gi=find_group(groups,r['off'])
    if gi is not None and gi<=905<=find_group(groups,min(r['off']+r['cnt']-1,groups[-1][1])):
        gi1=find_group(groups,min(r['off']+r['cnt']-1,groups[-1][1]))
        print(f"0x04 pc=0x{r['pc']:X} off={r['off']} cnt={r['cnt']} -> groups {gi}..{gi1}")
print()
for g in [903,904,905,906,907,908,912]:
    gs,ge=groups[g]; seg=words[g if False else gs:ge]
    has59=59 in seg; has61=61 in seg
    print(f"g{g} [59={has59} 61={has61}]: {dec(seg)}")
