import sys, os, struct, glob
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath('tools'))
import sec1_disasm as S
import patch_section1_offsets as P
def beu16(b,o): return struct.unpack_from('>H',b,o)[0]

def classify(data):
    """DIALOGUE iff an OP60 (SET_NAME_IDX) appears between the previous DISPLAY
    and this DISPLAY. The named-utterance machine re-asserts the active name slot
    via OP60 before each spoken turn's first display; pure narration displays have
    no OP60 in their immediate setup. Continuation body blocks of one turn DO get
    their own OP60 in the observed data (each DISP run is preceded by op60)."""
    ok, instrs, sec1, s2 = S.walk_resource(data)
    groups, _ = P.parse_sec2_group_offsets(data[s2:])
    recs = S.extract_records(sec1, instrs)
    disp = {d['pc']: d for d in recs['display']}
    out = []
    op60_seen = False
    for pc in sorted(instrs):
        op = instrs[pc]
        if op == 0x60:
            op60_seen = True
        elif op == 0x04 and pc in disp and disp[pc]['cnt'] > 0:
            d = disp[pc]
            gf = P._find_group(groups, d['off']); gl = P._find_group(groups, d['off']+d['cnt']-1)
            out.append({'g_first':gf,'g_last':gl,'dialogue':op60_seen})
            op60_seen = False  # reset; must re-see op60 before next display
    return out

def block_for(out, gi):
    for b in out:
        if b['g_first'] is not None and b['g_last'] is not None and b['g_first']<=gi<=b['g_last']:
            return b

if __name__=='__main__':
    cases=[('extracted/packdata_raw/1197_type02.raw',903,True,'R1197 g903 name'),
           ('extracted/packdata_raw/1197_type02.raw',905,True,'R1197 g905 body'),
           ('extracted/packdata_raw/1196_type02.raw',556,True,'R1196 g556 dial'),
           ('extracted/packdata_raw/1196_type02.raw',561,True,'R1196 g561 dial-cont'),
           ('extracted/packdata_raw/1196_type02.raw',565,True,'R1196 g565 dial-cont'),
           ('extracted/packdata_raw/1196_type02.raw',567,None,'R1196 g567 (cont? narr?)'),
           ('extracted/packdata_raw/1196_type02.raw',568,False,'R1196 g568 NARR'),
           ('extracted/packdata_raw/1196_type02.raw',574,False,'R1196 g574 NARR'),
           ('extracted/packdata_raw/1196_type02.raw',575,False,'R1196 g575 NARR'),
           ('extracted/packdata_raw/1196_type02.raw',577,True,'R1196 g577 dial')]
    for path,gi,exp,lab in cases:
        out=classify(open(path,'rb').read()); b=block_for(out,gi)
        m='?' if exp is None else ('PASS' if b['dialogue']==exp else '*FAIL*')
        print(f"  {m} {lab}: g[{b['g_first']}..{b['g_last']}] dialogue={b['dialogue']} exp={exp}")
