import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,'tools'); sys.path.insert(0,'build/recon_pag')
from sec1_disasm import walk
import patch_section1_offsets as P
from spans import load, groups_in_span

def beu16(b,o): return struct.unpack_from('>H',b,o)[0]
def beu32(b,o): return struct.unpack_from('>I',b,o)[0]

def blocks(res_idx):
    """Each 0x04 DISPLAY_TEXT = one display block. Returns list of dicts with
    static signals + JP page-break ground truth."""
    L=load(res_idx)
    if not L: return None
    ok,instrs,sec1,groups,words=L
    pcs=sorted(instrs); op_seq=[(pc,instrs[pc]) for pc in pcs]
    out=[]
    # Track speaker-channel state via 0x0C(set)/0x0D(clear) in PC order (approx).
    speaker_active=False
    for i,(pc,op) in enumerate(op_seq):
        if op==0x0C: speaker_active=True
        elif op==0x0D: speaker_active=False
        elif op==0x04:
            off=beu32(sec1,pc+2);cnt=beu32(sec1,pc+6)
            if cnt==0: continue
            sg=groups_in_span(groups,off,cnt)
            # immediate-window signals (since prev 0x04)
            j=i-1; last60=None; near0c=False; near14=False; near21=False
            while j>=0 and op_seq[j][1]!=0x04:
                o2=op_seq[j][1]; p2=op_seq[j][0]
                if o2==0x60 and last60 is None: last60=beu16(sec1,p2+2)
                if o2 in (0x0C,0x0D): near0c=True
                if o2==0x14: near14=True
                if o2==0x21: near21=True
                j-=1
            # block content
            jp_ffd2=any(0xFFD2 in words[groups[g][0]:groups[g][1]] for g in sg)
            glyphlen=sum(sum(1 for w in words[groups[g][0]:groups[g][1]] if w<0xFB00) for g in sg)
            out.append(dict(pc=pc,off=off,cnt=cnt,gis=sg,nspan=len(sg),
                            speaker_active=speaker_active,last60=last60,
                            near0c=near0c,near14=near14,near21=near21,
                            jp_ffd2=jp_ffd2,glyphlen=glyphlen))
    return ok,groups,words,out
