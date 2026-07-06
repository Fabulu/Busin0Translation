"""
Runtime-faithful DIALOGUE classifier (v2): models the name-SLOT machine.

Runtime (RE'd, SLPM_653.78):
  name struct[P] = ctx + P*12, fields +0xA0(name_off u32) +0xA4(name_cnt u32).
  - 0x14 NAMELBL handler @0x2F3F00: param P = slot; writes (off,cnt) into slot P.
  - 0x60 SET_NAME_IDX handler @0x2FA0C0: operand V (when V<10) -> ctx+0x298 = V
    (the ACTIVE name slot). V>=10 leaves it unchanged.
  - 0x04 DISPLAY handler @0x2F3700: if ctx+0x290 bit0 -> mode1; elif ctx+0x298==-1
    -> CENTERED NARRATION; else mode2 fetches slot[ctx+0x298] and prepends its name,
    then draws the body BOXED.
  -> A DISPLAY is BOXED DIALOGUE iff the active slot holds a non-empty name
     (cnt>0). If the active slot is empty (cnt==0) the prepended name is empty,
     i.e. text with no visible speaker = the centered narration look.

Encoder model: PC-order walk. slots = {} (param -> cnt). active = None.
  0x14 -> slots[param] = cnt
  0x60 (op<10) -> active = op
  0x04 -> DIALOGUE iff active is not None and slots.get(active,0) > 0
"""
import sys, os, struct
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath('tools'))
import sec1_disasm as S
import patch_section1_offsets as P

def beu16(b, o): return struct.unpack_from('>H', b, o)[0]

def classify(data):
    ok, instrs, sec1, s2 = S.walk_resource(data)
    groups, _ = P.parse_sec2_group_offsets(data[s2:])
    recs = S.extract_records(sec1, instrs)
    # slot writes from 0x14 (param -> cnt)
    slot_cnt = {}
    for r in recs['label']:
        slot_cnt[r['param']] = max(slot_cnt.get(r['param'], 0), r['cnt'])
    disp = {d['pc']: d for d in recs['display']}
    out = []
    active = None
    for pc in sorted(instrs):
        op = instrs[pc]
        if op == 0x60:
            v = beu16(sec1, pc + 2)
            if v < 10:
                active = v
        elif op == 0x14:
            pass  # slot already accounted via slot_cnt; (param,cnt static)
        elif op == 0x04 and pc in disp:
            d = disp[pc]
            if d['cnt'] == 0:
                continue
            gf = P._find_group(groups, d['off'])
            gl = P._find_group(groups, d['off'] + d['cnt'] - 1)
            has_name = active is not None and slot_cnt.get(active, 0) > 0
            out.append({'pc': pc, 'g_first': gf, 'g_last': gl,
                        'active': active, 'dialogue': has_name})
    return ok, out, groups

def block_for(blocks, gi):
    for b in blocks:
        if b['g_first'] is not None and b['g_last'] is not None and b['g_first'] <= gi <= b['g_last']:
            return b
    return None

if __name__ == '__main__':
    tests = [('extracted/packdata_raw/1197_type02.raw', 905, True,  'R1197 Barkeep g905'),
             ('extracted/packdata_raw/1196_type02.raw', 569, False, 'R1196 narration g569'),
             ('extracted/packdata_raw/1196_type02.raw', 575, False, 'R1196 narration g575')]
    for path, gi, expect, label in tests:
        data = open(path, 'rb').read()
        ok, blocks, groups = classify(data)
        b = block_for(blocks, gi)
        got = b['dialogue'] if b else None
        v = 'PASS' if got == expect else '*** FAIL ***'
        print(f"{v}  {label}: g[{b['g_first']}..{b['g_last']}] active_slot={b['active']} "
              f"dialogue={got} expect={expect}")
