import sys, struct, os, glob, json
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,'tools'); sys.path.insert(0,'build/recon_pag')
from sec1_disasm import walk
import patch_section1_offsets as P
from spans import load, groups_in_span

def beu16(b,o): return struct.unpack_from('>H',b,o)[0]
def beu32(b,o): return struct.unpack_from('>I',b,o)[0]

# Resources known to be narration-heavy (priors). R1193 intro, R1196 prologue.
NARRATION_RES={1193,1196}

def block_signals(res_idx):
    L=load(res_idx)
    if not L: return None
    ok,instrs,sec1,groups,words=L
    if not ok: return ('walkfail',groups,words,[])
    pcs=sorted(instrs); op_seq=[(pc,instrs[pc]) for pc in pcs]
    out=[]
    for i,(pc,op) in enumerate(op_seq):
        if op!=0x04: continue
        off=beu32(sec1,pc+2);cnt=beu32(sec1,pc+6)
        if cnt==0: continue
        sg=groups_in_span(groups,off,cnt)
        # Window since previous 0x04: gather 0x60(+param), 0x14, 0x0C
        j=i-1; preceding60=None; near14=False; near0c=False
        while j>=0 and op_seq[j][1]!=0x04:
            o2=op_seq[j][1]; p2=op_seq[j][0]
            if o2==0x60 and preceding60 is None: preceding60=beu16(sec1,p2+2)
            if o2==0x14: near14=True
            if o2 in (0x0C,0x0D): near0c=True
            j-=1
        jp_ffd2=any(0xFFD2 in words[groups[g][0]:groups[g][1]] for g in sg)
        # english line estimate: re-wrap pristine isn't english; we approximate
        # using glyph count / 19 as a proxy (real english handled in build).
        out.append(dict(pc=pc,gis=sg,nspan=len(sg),preceding60=preceding60,
                        near14=near14,near0c=near0c,jp_ffd2=jp_ffd2))
    return (ok,groups,words,out)

def classify_block(res_idx,b):
    """Return 'DIALOGUE' (safe to paginate) or 'NARRATION' (never paginate)."""
    # Ground-truth anchor: JP page-break => DEFINITELY boxed dialogue.
    if b['jp_ffd2']: return 'DIALOGUE'
    # Caption pattern: a 0x60 with param>0 + 0x14 = floating name caption block
    #   -> the block AFTER the caption (preceding60==0) is the dialogue BODY.
    if b['preceding60']==0: return 'DIALOGUE'
    # 0x60 param>0 selects a floating/centered label slot -> centered draw
    if b['preceding60'] is not None and b['preceding60']>0: return 'NARRATION'
    # no 0x60 since last 0x04 -> inherited mode; treat as NARRATION (safe default)
    return 'NARRATION'

if __name__=='__main__':
    args=[int(x) for x in sys.argv[1:]] if len(sys.argv)>1 else None
    files=sorted(glob.glob('extracted/packdata_raw/*_type02.raw'))
    resids=[int(os.path.basename(f)[:4]) for f in files]
    if args: resids=[r for r in resids if r in args]
    tot_d=tot_n=0; ffd2_in_narration=0; walkfail=0
    detail=[]
    for r in resids:
        res=block_signals(r)
        if res is None: continue
        if res[0]=='walkfail': walkfail+=1; continue
        ok,g,w,bl=res
        for b in bl:
            c=classify_block(r,b)
            if c=='DIALOGUE': tot_d+=1
            else:
                tot_n+=1
                if b['jp_ffd2']: ffd2_in_narration+=1
    print("type02 res scanned=%d (walkfail=%d)"%(len(resids),walkfail))
    print("DIALOGUE blocks=%d  NARRATION blocks=%d"%(tot_d,tot_n))
    print("JP-page-break blocks misclassified as NARRATION (FALSE NEG, harmless)=%d"%ffd2_in_narration)
