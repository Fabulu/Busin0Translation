import sys, os, struct, json
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,'tools')
from sec1_disasm import walk
import patch_section1_offsets as P
RAW='extracted/packdata_raw'
def beu16(b,o): return struct.unpack_from('>H',b,o)[0]
def beu32(b,o): return struct.unpack_from('>I',b,o)[0]

def analyze(res_idx):
    path=f'{RAW}/{res_idx:04d}_type02.raw'
    if not os.path.isfile(path): return None
    data=open(path,'rb').read()
    so=struct.unpack_from('<I',data,0x18)[0]; ss=struct.unpack_from('<I',data,0x14)[0]
    sec1=data[0x20:so]; sec2=data[so:so+ss]
    ok,instrs=walk(sec1)
    groups,trail=P.parse_sec2_group_offsets(sec2)
    words=[beu16(sec2,i*2) for i in range(len(sec2)//2)]
    pcs=sorted(instrs)
    # For each 0x04, look at the WINDOW of opcodes since the previous 0x04
    # (the "block" for this displayed message). Collect signals.
    rows=[]
    last04_pc=None
    # precompute per-pc list
    # group of each 0x04 + whether preceding 0x0C(SET_NAME)/0x60/0x14 within window
    prev_idx=0
    op_seq=[(pc,instrs[pc]) for pc in pcs]
    for i,(pc,op) in enumerate(op_seq):
        if op!=0x04: continue
        off=beu32(sec1,pc+2); cnt=beu32(sec1,pc+6)
        if cnt==0: continue
        gi=P._find_group(groups,off)
        # window = opcodes from previous 0x04 (exclusive) to this 0x04
        j=i-1; saw_0c=False; saw_60=False; saw_14=False; saw_14_here=False
        while j>=0 and op_seq[j][1]!=0x04:
            o2=op_seq[j][1]
            if o2 in (0x0C,0x0D): saw_0c=True
            if o2==0x60: saw_60=True
            if o2==0x14: saw_14=True
            j-=1
        # JP group content signals
        gwords = words[groups[gi][0]:groups[gi][1]] if gi is not None else []
        has_ffd2 = 0xFFD2 in gwords
        n_ffd2 = gwords.count(0xFFD2)
        n_fffe = gwords.count(0xFFFE)
        glyphlen = sum(1 for w in gwords if w<0xFB00)
        rows.append(dict(pc=pc,gi=gi,off=off,cnt=cnt,saw_0c=saw_0c,saw_60=saw_60,
                         saw_14=saw_14,has_ffd2=has_ffd2,n_ffd2=n_ffd2,n_fffe=n_fffe,glyphlen=glyphlen))
    return dict(res=res_idx,ok=ok,ng=len(groups),rows=rows)

if __name__=='__main__':
    for r in [int(x) for x in sys.argv[1:]]:
        a=analyze(r)
        if not a: print(r,'none'); continue
        rows=a['rows']
        n=len(rows)
        c0c=sum(r['saw_0c'] for r in rows)
        c60=sum(r['saw_60'] for r in rows)
        c14=sum(r['saw_14'] for r in rows)
        cffd2=sum(r['has_ffd2'] for r in rows)
        print("R%d  0x04(cnt>0)=%d  with_0C(speaker)=%d  with_0x60=%d with_0x14=%d  JP_has_FFD2=%d"
              %(r,n,c0c,c60,c14,cffd2))
