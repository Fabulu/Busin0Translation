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

# KNOWN NARRATION blocks (the bug the user hates - intro narration)
# From CLAUDE memory: R1196 g569 'No one was in sight', g575 'A man approached'
# Decode g569,575,577 + surrounding, look for inline-name markers FFE0-FFE7
narr_cases=[(1196,[567,568,569,570,571,572,573,574,575,576,577,578])]
for rid,gl in narr_cases:
    f=f'extracted/packdata_raw/{rid:04d}_type02.raw'
    d=open(f,'rb').read(); sec1,sec2=load_sec(d)
    groups,words,trailing=parse_groups(sec2)
    print(f"=== R{rid} narration groups {gl[0]}..{gl[-1]} ===")
    for gi in gl:
        gs,ge=groups[gi]; seg=words[gs:ge]
        # check for inline name markers
        has_namemark = any(0xFFE0<=w<=0xFFE7 for w in seg)
        has_ffd2 = 0xFFD2 in seg
        print(f"  g{gi} [{'NAMEMARK ' if has_namemark else ''}{'FFD2 ' if has_ffd2 else ''}]: {dec(seg)}")
