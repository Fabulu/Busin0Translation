import sys, struct, re
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,'tools')
import patch_section1_offsets as P
P._load_tables()
ENG=P._ENG_TABLE; ENG_REV=P._ENG_REV
def enc(ch):
    if ch in ENG: return ENG[ch]
    if ch.lower() in ENG: return ENG[ch.lower()]
    return 31
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
# encode "No one was in" fully
g=[enc(c) for c in "No one was in"]
prefix=b''.join(struct.pack('>H',x) for x in g)
ee=open('build/recon_portrait3/extract/OverflowAndTooLongSpaces__ee.bin','rb').read()
idxs=[m.start() for m in re.finditer(re.escape(prefix),ee)]
print("'No one was in' @",[hex(i) for i in idxs])
for i in idxs:
    end=i
    while struct.unpack_from('>H',ee,end)[0]!=0xFFFF: end+=2
    ww=[struct.unpack_from('>H',ee,j)[0] for j in range(i,end,2)]
    print(f"  @{hex(i)} ({len(ww)}w):",show(ww))
