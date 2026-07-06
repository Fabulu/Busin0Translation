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
    for g in seg:
        if g==0xFFFE: out.append('/'); continue
        if g==0xFFD2: out.append('||'); continue
        if g>=0xFB00: out.append(f'<{g:04X}>'); continue
        out.append(GM.get(str(g),'?'))
    return ''.join(out)

# representative critical blocks: mix of suspected narration (R1196) and dialogue (R1197)
cases=[(1196,0x2E08),(1196,0x747B),(1197,0x507A),(1197,0x74DE),
       (1197,0x52CC),(1205,0x88A1),(1211,0x361E)]

for rid,pc_target in cases:
    f=f'extracted/packdata_raw/{rid:04d}_type02.raw'
    d=open(f,'rb').read(); sec1,sec2=load_sec(d)
    groups,words,trailing=parse_groups(sec2)
    ok,instrs=walk(sec1); recs=extract_records(sec1,instrs)
    nameisland={}
    for r in recs['label']:
        gi=find_group(groups,r['off'])
        if gi is not None: nameisland.setdefault(gi,[]).append((r['off']-groups[gi][0],r['cnt']))
    # name_ref instr positions (0x0C/0x0D) - these are Section-1 ordered; map by pc proximity
    nrefs=sorted([(r['pc'],r['op'],r['param'],r['idx']) for r in recs['name_ref']])
    # find the 0x04 with this pc
    blk=None
    for r in recs['display']:
        if r['pc']==pc_target: blk=r; break
    off=blk['off']; cnt=blk['cnt']
    gi0=find_group(groups,off); gi1=find_group(groups,min(off+cnt-1,groups[-1][1]))
    gl=list(range(gi0,gi1+1))
    # nearby name_ref within +-0x40 bytes of pc
    near=[nr for nr in nrefs if abs(nr[0]-pc_target)<=0x60]
    print(f"=== R{rid} pc=0x{pc_target:X} groups={gl} ===")
    print(f"  name_ref(0C/0D) within 0x60 of pc: {[(hex(p),hex(op),param,idx) for p,op,param,idx in near]}")
    for gi in gl:
        gs,ge=groups[gi]; seg=words[gs:ge]
        ni = f' NAME-ISLAND{nameisland[gi]}' if gi in nameisland else ''
        print(f"  g{gi}{ni}: {dec(seg)}")
    print()
