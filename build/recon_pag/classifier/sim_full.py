"""
Full VM simulation of the render-mode state for type-02 Section 1, applying the
EXACT 0x04 DISPLAY handler decision (VA 0x2F3700):

  mode = MODE1            if (ctx290 & 1)
       = NARRATION(0)     elif (ctx298 == -1)
       = DIALOGUE(2+body)  else

State writers (RE'd):
  op 0x60 @0x2FA0C0: u16 v; if v<10: ctx298 = v
  op 0x62 @0x2FA4C0: u16 v; if v!=0: ctx290 |= 4 ; else: ctx290 &= ~5   (clears bit0+bit2)
  scene init @0x2F2AA8: ctx290=0, ctx298=-1
NOTE: bit0 of ctx290 is set elsewhere (mode1 path). We model only op62's clear.

We walk in PC order (linear address order = execution order for the straight-line
dialogue spine; control flow is mostly fallthrough for these resources).
"""
import sys, os, struct
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath('tools'))
import sec1_disasm as S
import patch_section1_offsets as P
def beu16(b,o): return struct.unpack_from('>H',b,o)[0]

def sim(data):
    ok, instrs, sec1, s2 = S.walk_resource(data)
    groups, _ = P.parse_sec2_group_offsets(data[s2:])
    recs = S.extract_records(sec1, instrs)
    disp = {d['pc']: d for d in recs['display']}
    ctx290 = 0
    ctx298 = -1
    out = []
    for pc in sorted(instrs):
        op = instrs[pc]
        if op == 0x60:
            v = beu16(sec1, pc+2)
            if v < 10: ctx298 = v
        elif op == 0x62:
            v = beu16(sec1, pc+2)
            if v != 0: ctx290 |= 4
            else: ctx290 &= ~5
        elif op == 0x04 and pc in disp:
            d = disp[pc]
            if d['cnt'] == 0: continue
            gf = P._find_group(groups, d['off']); gl = P._find_group(groups, d['off']+d['cnt']-1)
            if ctx290 & 1: mode='MODE1'
            elif ctx298 == -1: mode='NARR'
            else: mode='DIAL'
            out.append({'pc':pc,'g_first':gf,'g_last':gl,'ctx290':ctx290,'ctx298':ctx298,'mode':mode})
    return ok, out, groups

def block_for(blocks, gi):
    for b in blocks:
        if b['g_first'] is not None and b['g_last'] is not None and b['g_first']<=gi<=b['g_last']:
            return b
    return None

if __name__=='__main__':
    tests=[('extracted/packdata_raw/1197_type02.raw',905,'DIAL','R1197 Barkeep g905'),
           ('extracted/packdata_raw/1196_type02.raw',569,'NARR','R1196 narration g569'),
           ('extracted/packdata_raw/1196_type02.raw',575,'NARR','R1196 narration g575')]
    for path,gi,expect,label in tests:
        data=open(path,'rb').read(); ok,blocks,groups=sim(data)
        b=block_for(blocks,gi); got=b['mode'] if b else None
        v='PASS' if got==expect else 'FAIL'
        print(f"{v}  {label}: g[{b['g_first']}..{b['g_last']}] ctx290={b['ctx290']} ctx298={b['ctx298']} mode={got} expect={expect}")
