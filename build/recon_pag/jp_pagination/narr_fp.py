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
def dec(seg, lim=40):
    out=[]
    for g in seg[:lim]:
        if g==0xFFFE: out.append('/'); continue
        if g==0xFFD2: out.append('|'); continue
        if 0xFFE0<=g<=0xFFE7: out.append(f'«{g&0xF}»'); continue
        if g>=0xFB00: out.append('·'); continue
        out.append(GM.get(str(g),'?'))
    return ''.join(out)

# For every name=N ffd2=Y BLOCK, decode the FFD2-containing group and judge:
# Is it narration prose (no name markers, no dialogue voice) or unnamed dialogue?
# Heuristic markers of DIALOGUE in JP busin text:
#  - inline name marker FFE0..FFE7
#  - The group is bracketed at runtime by box-mode (we approximate via: does ANY
#    group in this 0x04's contiguous run, OR its immediate predecessors, carry a
#    name marker?)
jp_blocks=json.load(open('build/recon_pag/jp_pagination/jp_blocks.json'))
crit=[(b[0],b[1],b[2]) for b in jp_blocks if (not b[4]) and b[3]]
# group resources
byres={}
for rid,pc,gl in crit: byres.setdefault(rid,[]).append((pc,gl))
namemark_in_block=0; namemark_in_window=0; pure_narr=0; pure_narr_ex=[]
for rid,items in sorted(byres.items()):
    f=f'extracted/packdata_raw/{rid:04d}_type02.raw'
    d=open(f,'rb').read(); sec1,sec2=load_sec(d)
    groups,words,trailing=parse_groups(sec2)
    def gnm(gi):
        gs,ge=groups[gi]; return any(0xFFE0<=w<=0xFFE7 for w in words[gs:ge])
    for pc,gl in items:
        inblk=any(gnm(g) for g in gl)
        # window: +-3 groups
        lo=max(0,gl[0]-3); hi=min(len(groups)-1,gl[-1]+3)
        inwin=any(gnm(g) for g in range(lo,hi+1))
        if inblk: namemark_in_block+=1
        elif inwin: namemark_in_window+=1
        else:
            pure_narr+=1
            if len(pure_narr_ex)<25:
                g=gl[0]; gs,ge=groups[g]
                pure_narr_ex.append((rid,gl,dec(words[gs:ge])))
print(f"name=N ffd2=Y blocks total: {len(crit)}")
print(f"  with name marker INSIDE block: {namemark_in_block}")
print(f"  with name marker in +-3 window: {namemark_in_window}")
print(f"  NO name marker anywhere near (pure-narration-LOOKING): {pure_narr}")
print()
print("=== pure-narration-looking name=N ffd2=Y examples (decode FFD2 group) ===")
for rid,gl,txt in pure_narr_ex:
    print(f"  R{rid} g{gl}: {txt}")
