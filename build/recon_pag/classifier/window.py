import sys, os, struct
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath('tools'))
import sec1_disasm as S
import patch_section1_offsets as P
def beu16(b,o): return struct.unpack_from('>H',b,o)[0]

def classify(data, window_disp=2):
    """A DISPLAY block is DIALOGUE iff a 0x14 NAMELBL occurred within the last
    `window_disp` DISPLAY blocks (i.e. <= window_disp display blocks since the
    most recent NAMELBL)."""
    ok, instrs, sec1, s2 = S.walk_resource(data)
    groups, _ = P.parse_sec2_group_offsets(data[s2:])
    recs = S.extract_records(sec1, instrs)
    disp = {d['pc']: d for d in recs['display']}
    name_pcs = {r['pc'] for r in recs['label']}
    since = 99
    out = []
    for pc in sorted(instrs):
        op = instrs[pc]
        if op == 0x14:
            since = 0
        elif op == 0x04 and pc in disp and disp[pc]['cnt'] > 0:
            d = disp[pc]
            gf = P._find_group(groups, d['off']); gl = P._find_group(groups, d['off']+d['cnt']-1)
            out.append({'g_first':gf,'g_last':gl,'since':since,'dialogue':since<=window_disp})
            since += 1
    return out

def block_for(out, gi):
    for b in out:
        if b['g_first'] is not None and b['g_last'] is not None and b['g_first']<=gi<=b['g_last']:
            return b

if __name__=='__main__':
    cases=[('extracted/packdata_raw/1197_type02.raw',903,True),
           ('extracted/packdata_raw/1197_type02.raw',905,True),
           ('extracted/packdata_raw/1196_type02.raw',556,True),
           ('extracted/packdata_raw/1196_type02.raw',569,False),
           ('extracted/packdata_raw/1196_type02.raw',575,False)]
    for K in (1,2,3,4):
        print(f"\n=== window K={K} ===")
        for path,gi,exp in cases:
            out=classify(open(path,'rb').read(),K); b=block_for(out,gi)
            print(f"  {'PASS' if b['dialogue']==exp else 'FAIL'} {os.path.basename(path)} g{gi} since={b['since']} dia={b['dialogue']} exp={exp}")
