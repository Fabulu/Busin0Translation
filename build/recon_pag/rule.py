import sys, os, struct
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,'tools'); sys.path.insert(0,'build/recon_pag')
from sec1_disasm import walk
import patch_section1_offsets as P
from spans import load, groups_in_span
def beu16(b,o): return struct.unpack_from('>H',b,o)[0]
def beu32(b,o): return struct.unpack_from('>I',b,o)[0]

def classify(res_idx):
    L=load(res_idx)
    if not L: return None
    ok,instrs,sec1,groups,words=L
    pcs=sorted(instrs)
    op_seq=[(pc,instrs[pc]) for pc in pcs]
    # For each 0x04, find the IMMEDIATELY PRECEDING 0x60 (with no 0x04 in between).
    # Rule under test:
    #   preceding 0x60 with param==0  -> BOXED dialogue body
    #   preceding 0x60 with param>0   -> centered label (name caption)
    #   no preceding 0x60 (since last 0x04) -> CENTERED narration
    rows=[]
    for i,(pc,op) in enumerate(op_seq):
        if op!=0x04: continue
        off=beu32(sec1,pc+2);cnt=beu32(sec1,pc+6)
        if cnt==0: continue
        # scan back to previous 0x04, capture last 0x60 param
        j=i-1; last60=None; saw_0c=False
        while j>=0 and op_seq[j][1]!=0x04:
            o2=op_seq[j][1]; p2=op_seq[j][0]
            if o2==0x60 and last60 is None:
                last60=beu16(sec1,p2+2)
            if o2 in (0x0C,0x0D): saw_0c=True
            j-=1
        if last60 is None: cls='NARRATION'
        elif last60==0: cls='DIALOGUE'
        else: cls='LABEL'
        gis=groups_in_span(groups,off,cnt)
        rows.append(dict(pc=pc,off=off,cnt=cnt,gis=gis,last60=last60,cls=cls,saw_0c=saw_0c))
    return ok,groups,words,rows

if __name__=='__main__':
    for res in [int(x) for x in sys.argv[1:]]:
        r=classify(res)
        if not r: print(res,'none'); continue
        ok,groups,words,rows=r
        from collections import Counter
        c=Counter(x['cls'] for x in rows)
        # count JP FFD2 by class
        ffd2={'DIALOGUE':0,'NARRATION':0,'LABEL':0}
        for x in rows:
            for gi in x['gis']:
                gw=words[groups[gi][0]:groups[gi][1]]
                if 0xFFD2 in gw: ffd2[x['cls']]+=1
        print("R%d  DIALOGUE=%d NARRATION=%d LABEL=%d  | JP_FFD2 by class: D=%d N=%d L=%d"
              %(res,c['DIALOGUE'],c['NARRATION'],c['LABEL'],ffd2['DIALOGUE'],ffd2['NARRATION'],ffd2['LABEL']))
