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
d=open('extracted/packdata_raw/1196_type02.raw','rb').read()
sec1,sec2=load_sec(d); groups,words,_=parse_groups(sec2)
ok,instrs=walk(sec1); recs=extract_records(sec1,instrs)
# Show the pc-ordered DISPLAY/LABEL/op22 sequence around groups 560-580 region.
# Find pc range covering groups 560..580
items=sorted(instrs.items())
def beu32(o): return struct.unpack_from('>I',sec1,o)[0]
print("pc-stream around narration g567-578 (DISPLAY/LABEL/0x21/0x22):")
for pc,op in items:
    if op==0x04:
        off=beu32(pc+2); cnt=beu32(pc+6)
        if cnt==0: continue
        g0=find_group(groups,off); g1=find_group(groups,min(off+cnt-1,groups[-1][1]))
        if g0 is None or not (560<=g0<=582 or (g1 and 560<=g1<=582)): continue
        seg=[]
        for g in range(g0,g1+1):
            gs,ge=groups[g]; seg+=list(words[gs:ge])
        h61=61 in seg
        print(f"  0x{pc:04X} DISPLAY g{g0}..{g1} [61={h61}]")
    elif op==0x14:
        g=find_group(groups,beu32(pc+6))
        if g is not None and 560<=g<=582:
            print(f"  0x{pc:04X} LABEL g{g}")
    elif op in (0x21,0x22):
        print(f"  0x{pc:04X} op{op:02X} {'SET-box' if op==0x21 else 'CLEAR-box'}")
