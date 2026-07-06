import sys, os, struct
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,'tools')
from sec1_disasm import walk
import patch_section1_offsets as P
RAW='extracted/packdata_raw'
def beu16(b,o): return struct.unpack_from('>H',b,o)[0]
def beu32(b,o): return struct.unpack_from('>I',b,o)[0]

def load(res_idx):
    path=f'{RAW}/{res_idx:04d}_type02.raw'
    if not os.path.isfile(path): return None
    data=open(path,'rb').read()
    so=struct.unpack_from('<I',data,0x18)[0]; ss=struct.unpack_from('<I',data,0x14)[0]
    sec1=data[0x20:so]; sec2=data[so:so+ss]
    ok,instrs=walk(sec1)
    groups,trail=P.parse_sec2_group_offsets(sec2)
    words=[beu16(sec2,i*2) for i in range(len(sec2)//2)]
    return ok,instrs,sec1,groups,words

def groups_in_span(groups, off, cnt):
    """Return list of group indices whose [start..ffff] intersect [off, off+cnt)."""
    end=off+cnt
    res=[]
    for gi,(gs,ge) in enumerate(groups):
        # group occupies words gs..ge (ge=ffff terminator). content gs..ge.
        if gs < end and ge >= off:   # overlap (ge inclusive as ffff)
            res.append(gi)
    return res

def per_group_signals(res_idx):
    L=load(res_idx)
    if not L: return None
    ok,instrs,sec1,groups,words=L
    pcs=sorted(instrs)
    op_seq=[(pc,instrs[pc]) for pc in pcs]
    # build per-0x04 block signals, then assign to EACH group in its span
    out={}  # gi -> dict
    for i,(pc,op) in enumerate(op_seq):
        if op!=0x04: continue
        off=beu32(sec1,pc+2); cnt=beu32(sec1,pc+6)
        if cnt==0: continue
        # window back to previous 0x04
        j=i-1; saw_0c=saw_60=saw_14=False
        while j>=0 and op_seq[j][1]!=0x04:
            o2=op_seq[j][1]
            if o2 in (0x0C,0x0D): saw_0c=True
            if o2==0x60: saw_60=True
            if o2==0x14: saw_14=True
            j-=1
        gis=groups_in_span(groups,off,cnt)
        for k,gi in enumerate(gis):
            gw=words[groups[gi][0]:groups[gi][1]]
            out[gi]=dict(gi=gi,blk_pc=pc,blk_off=off,blk_cnt=cnt,span_len=len(gis),
                         pos_in_span=k, saw_0c=saw_0c,saw_60=saw_60,saw_14=saw_14,
                         n_ffd2=gw.count(0xFFD2), n_fffe=gw.count(0xFFFE),
                         glyphlen=sum(1 for w in gw if w<0xFB00))
    return ok,groups,words,out

if __name__=='__main__':
    res=int(sys.argv[1]); gis=[int(x) for x in sys.argv[2:]]
    ok,groups,words,out=per_group_signals(res)
    for g in gis:
        r=out.get(g)
        if not r: print(f"R{res} g{g}: not in any 0x04 span (untargeted/binary)"); continue
        print(f"R{res} g{g}: blk(off={r['blk_off']},cnt={r['blk_cnt']},span={r['span_len']},pos={r['pos_in_span']}) "
              f"0C={r['saw_0c']} 60={r['saw_60']} 14={r['saw_14']} JP_FFD2={r['n_ffd2']} FFFE={r['n_fffe']} glyph={r['glyphlen']}")
