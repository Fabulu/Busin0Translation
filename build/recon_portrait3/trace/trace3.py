import sys, struct, json, glob, os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, 'tools'); sys.path.insert(0,'build')
import patch_section1_offsets as P
P._load_tables()

RAW='extracted/packdata_raw/1196_type02.raw'
raw=open(RAW,'rb').read()
sec2_off=struct.unpack_from('<I',raw,0x18)[0]
sec2_size=struct.unpack_from('<I',raw,0x14)[0]
sec2=raw[sec2_off:sec2_off+sec2_size]
groups,trail=P.parse_sec2_group_offsets(sec2)

def words(gi):
    gs,ge=groups[gi]
    return [struct.unpack_from('>H',sec2,(gs+k)*2)[0] for k in range(ge-gs)]

ENG_REV=P._ENG_REV
def show(w):
    o=[]
    for g in w:
        if g>=0xFB00: o.append('<%04X>'%g)
        elif str(g) in P._GLYPH_MAP: o.append(P._GLYPH_MAP[str(g)])
        elif g in ENG_REV: o.append(ENG_REV[g])
        else: o.append('?%d'%g)
    return ''.join(o)

for mi in [577,653]:
    w=words(mi)
    print(f"\n=== ORIG group {mi} ({len(w)}w) ===")
    print(' '.join('%04X'%x for x in w))
    print("decoded:",show(w))
    lead,txt,tr=P._split_control_and_text(w)
    print("split lead=",['%04X'%x for x in lead]," text=",len(txt),"trail=",['%04X'%x for x in tr])
