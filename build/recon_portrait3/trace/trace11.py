import sys, struct, re
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,'tools')
import patch_section1_offsets as P
P._load_tables()
ENG=P._ENG_TABLE; ENG_REV=P._ENG_REV
def show(w):
    o=[]
    for g in w:
        if g==0xFFFE:o.append('|LB|')
        elif g==0xFFD2:o.append('|PB|')
        elif g==0xFFFF:o.append('|FF|')
        elif g>=0xFB00:o.append('<%04X>'%g)
        elif g in ENG_REV:o.append(ENG_REV[g])
        else:o.append('?%d'%g)
    return ''.join(o)
def enc(c): 
    return ENG.get(c, ENG.get(c.lower(),31))
prefix=b''.join(struct.pack('>H',enc(c)) for c in "No one was in")
for iso in ['build/BUSIN0_EN_v89.iso','build/BUSIN0_EN_v88.iso','build/BUSIN0_EN_v90.iso']:
    data=open(iso,'rb').read()
    idxs=[m.start() for m in re.finditer(re.escape(prefix),data)]
    if not idxs: print(iso,"not found"); continue
    i=idxs[0]; end=i
    while struct.unpack_from('>H',data,end)[0]!=0xFFFF: end+=2
    w=[struct.unpack_from('>H',data,j)[0] for j in range(i,end,2)]
    print(iso,":",show(w))
