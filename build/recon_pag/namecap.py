import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,'tools'); sys.path.insert(0,'build/recon_pag')
from spans import load, groups_in_span
def beu16(b,o): return struct.unpack_from('>H',b,o)[0]
def beu32(b,o): return struct.unpack_from('>I',b,o)[0]

def analyze(res):
    L=load(res)
    if not L: return None
    ok,instrs,sec1,groups,words=L
    if not ok: return ('walkfail',)
    pcs=sorted(instrs); seq=[(pc,instrs[pc]) for pc in pcs]
    # Detect the speaker-name-caption SEQUENCE:
    #   0x60(param>0) ; 0x04(name, small) ; 0x60(param=0) ; 0x04(BODY)
    # The BODY 0x04 right after a [0x60 p=0 preceded by 0x60 p>0 + name 0x04] is DIALOGUE.
    out=[]
    for i,(pc,op) in enumerate(seq):
        if op!=0x04: continue
        off=beu32(sec1,pc+2);cnt=beu32(sec1,pc+6)
        if cnt==0: continue
        sg=groups_in_span(groups,off,cnt)
        # look back over the immediate control run (0x60/0x14/0x04 name) since prev BODY
        # pattern: is there a 0x60 p>0 within 6 ops before this, AND a 0x60 p=0 between?
        had_60pos=False; had_60zero_after_pos=False
        k=i-1; steps=0; seen60pos=False
        while k>=0 and steps<10:
            o2=seq[k][1]; p2=seq[k][0]
            if o2==0x04 and not (seq[k][0]==pc):
                # a previous display; stop if it's a BODY (large) — but name displays are small
                pcnt=beu32(sec1,p2+6)
                if pcnt>20:  # previous large display = previous body, stop
                    break
            if o2==0x60:
                pm=beu16(sec1,p2+2)
                if pm>0: seen60pos=True
            k-=1; steps+=1
        is_caption_dialogue=seen60pos
        out.append(dict(gis=sg,nspan=len(sg),caption=is_caption_dialogue,
                        jp_ffd2=any(0xFFD2 in words[groups[g][0]:groups[g][1]] for g in sg)))
    return ('ok',out)
if __name__=='__main__':
    import sys
    for res in [int(x) for x in sys.argv[1:]]:
        r=analyze(res)
        if not r or r[0]!='ok': print(res,r[0] if r else 'none'); continue
        out=r[1]
        cap=sum(b['caption'] for b in out)
        ffd2=sum(b['jp_ffd2'] for b in out)
        ffd2_no_cap=sum(1 for b in out if b['jp_ffd2'] and not b['caption'])
        print("R%d blocks=%d caption(dlg)=%d JP_FFD2=%d  FFD2_without_caption=%d"%(res,len(out),cap,ffd2,ffd2_no_cap))
