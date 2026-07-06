import sys, os, struct
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath('tools'))
import sec1_disasm as S
import patch_section1_offsets as P
def beu16(b,o): return struct.unpack_from('>H',b,o)[0]

def classify(data):
    ok, instrs, sec1, s2 = S.walk_resource(data)
    groups, _ = P.parse_sec2_group_offsets(data[s2:])
    recs = S.extract_records(sec1, instrs)
    label_at = {}
    for r in recs['label']:
        label_at.setdefault(r['pc'], []).append(r)
    disp = {d['pc']: d for d in recs['display']}
    slot_cnt = {}   # dynamic: param -> current name cnt (PC order)
    active = -1     # ctx+0x298 init -1
    out = []
    for pc in sorted(instrs):
        op = instrs[pc]
        if op == 0x14:
            for r in label_at.get(pc, []):
                slot_cnt[r['param']] = r['cnt']
        elif op == 0x60:
            v = beu16(sec1, pc+2)
            if v < 10:
                active = v
        elif op == 0x04 and pc in disp:
            d = disp[pc]
            if d['cnt'] == 0: continue
            gf = P._find_group(groups, d['off']); gl = P._find_group(groups, d['off']+d['cnt']-1)
            has = active != -1 and slot_cnt.get(active,0) > 0
            out.append({'pc':pc,'g_first':gf,'g_last':gl,'active':active,
                        'slot_cnt':slot_cnt.get(active,0),'dialogue':has})
    return ok, out, groups

def block_for(blocks, gi):
    for b in blocks:
        if b['g_first'] is not None and b['g_last'] is not None and b['g_first']<=gi<=b['g_last']:
            return b
    return None

if __name__=='__main__':
    tests=[('extracted/packdata_raw/1197_type02.raw',905,True,'R1197 Barkeep g905'),
           ('extracted/packdata_raw/1196_type02.raw',569,False,'R1196 narration g569'),
           ('extracted/packdata_raw/1196_type02.raw',575,False,'R1196 narration g575')]
    for path,gi,expect,label in tests:
        data=open(path,'rb').read(); ok,blocks,groups=classify(data)
        b=block_for(blocks,gi); got=b['dialogue'] if b else None
        v='PASS' if got==expect else '*** FAIL ***'
        print(f"{v}  {label}: g[{b['g_first']}..{b['g_last']}] active={b['active']} slot_cnt={b['slot_cnt']} dialogue={got} expect={expect}")
