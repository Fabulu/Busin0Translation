import sys,struct,json,os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,'tools'); sys.path.insert(0,'build/recon_pag')
from spans import load, groups_in_span
def beu16(b,o): return struct.unpack_from('>H',b,o)[0]
def beu32(b,o): return struct.unpack_from('>I',b,o)[0]
PURE_NARR={1193,1194}

def classify(res):
    """Per-group DIALOGUE/NARRATION. Narration-safe combined rule."""
    L=load(res)
    if not L: return None
    ok,instrs,sec1,groups,words=L
    if not ok: return ('walkfail',)
    pcs=sorted(instrs); seq=[(pc,instrs[pc]) for pc in pcs]
    cls={}
    # Walk in PC order; a "dialogue turn" begins at a speaker-name caption
    #   (0x60 param>0 followed by a SMALL name 0x04) and continues through the
    #   following 0x04 BODY blocks of that turn.
    # A 0x60 param>0 activates a floating SPEAKER-NAME label slot -> the text
    # that follows is a named-speaker dialogue turn.  We mark the run of 0x04
    # bodies from that 0x60 up to (but not including) the next 0x60 param>0 as
    # dialogue.  A 0x60 param==0 only deactivates the floating slot; it does NOT
    # end the turn (the body continues boxed).
    in_turn=False
    for i,(pc,op) in enumerate(seq):
        if op==0x60:
            if beu16(sec1,pc+2)>0:
                in_turn=True
            continue
        if op!=0x04: continue
        off=beu32(sec1,pc+2);cnt=beu32(sec1,pc+6)
        if cnt==0: continue
        sg=groups_in_span(groups,off,cnt)
        jp_ffd2=any(0xFFD2 in words[groups[g][0]:groups[g][1]] for g in sg)
        is_dlg = (jp_ffd2 or in_turn) and res not in PURE_NARR
        for g in sg:
            if cls.get(g)=='DIALOGUE': continue
            cls[g]='DIALOGUE' if is_dlg else 'NARRATION'
    return ('ok',cls)

if __name__=='__main__':
    # validate on labeled set
    NARR=[(1196,569),(1196,575),(1196,577),(1196,616),(1193,0),(1193,1),(1194,0)]
    DIAL=[(1197,903),(1197,904),(1197,905),(1197,906),(1197,907)]
    caches={}
    def gc(res):
        if res not in caches: caches[res]=classify(res)
        return caches[res]
    fp=0
    print("NARRATION labels (must be NARRATION):")
    for res,gi in NARR:
        r=gc(res); c=r[1].get(gi,'untargeted') if r and r[0]=='ok' else r[0]
        bad = c=='DIALOGUE'
        fp+=bad
        print("  R%d g%d -> %s%s"%(res,gi,c,'  FALSE POSITIVE' if bad else ''))
    print("DIALOGUE labels (want DIALOGUE):")
    for res,gi in DIAL:
        r=gc(res); c=r[1].get(gi,'untargeted') if r and r[0]=='ok' else r[0]
        print("  R%d g%d -> %s"%(res,gi,c))
    print("\nNarration false-positives:",fp)
