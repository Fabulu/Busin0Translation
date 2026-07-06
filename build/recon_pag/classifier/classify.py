"""
Encoder-time DIALOGUE/NARRATION classifier replicating the runtime name-state.

Runtime ground truth (RE'd from SLPM_653.78):
  - 0x04 DISPLAY_TEXT handler @ VA 0x2F3700 picks render mode from ctx fields:
      * ctx+0x290 bit0 set        -> mode 1 (special override layout)
      * else ctx+0x298 (name idx) == -1 -> mode 0  CENTERED NARRATION  (0x305B1C/0x305CC4)
      * else                       -> mode 2 (name prepend) + mode 0 body, BOXED dialogue
  - ctx+0x298 (s16 active-name index) is set ONLY by the 0x14 NAMELBL handler
    @ VA 0x2F3F00 (writes name struct +0xA0/+0xA4 and the pending flag);
    it is INITIALIZED (to -1) only at scene init @ VA 0x2F2AA8.
  - 0x0C/0x0D (SET/CLR_NAME) @ 0x302020/0x302180 touch a CHANNEL-BIT array, NOT 0x298.
  - The 0x04 handler does NOT clear 0x298 after use: a name, once set by a 0x14,
    sticks across all following 0x04 blocks until the next 0x14.

Encoder model: walk Section-1 instructions in PC order. Maintain name_active.
A 0x14 NAMELBL sets name_active=True (records the name group). For each 0x04
DISPLAY block, it is DIALOGUE (boxed, safe to paginate) iff name_active is True
at that PC. Otherwise NARRATION (centered, NEVER paginate).
"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath('tools'))
import sec1_disasm as S
import patch_section1_offsets as P

def classify_resource(data):
    ok, instrs, sec1, sec2_off = S.walk_resource(data)
    recs = S.extract_records(sec1, instrs)
    groups, trailing = P.parse_sec2_group_offsets(data[sec2_off:])
    # Build a PC-ordered event stream of just 0x14 (sets name) and 0x04 (display).
    ev = []
    for r in recs['label']:
        ev.append((r['pc'], 'NAME', r))
    for d in recs['display']:
        ev.append((d['pc'], 'DISP', d))
    ev.sort(key=lambda x: x[0])
    name_active = False  # mirrors ctx+0x298 != -1 ; init -1 at scene start
    out = []  # list of dicts per 0x04 block
    for pc, kind, r in ev:
        if kind == 'NAME':
            name_active = True
        else:
            off, cnt = r['off'], r['cnt']
            if cnt == 0:
                continue
            gf = P._find_group(groups, off)
            gl = P._find_group(groups, off + cnt - 1)
            out.append({'pc': pc, 'off': off, 'cnt': cnt,
                        'g_first': gf, 'g_last': gl,
                        'dialogue': name_active})
    return ok, out, groups

def block_for_group(blocks, gi):
    for b in blocks:
        if b['g_first'] is not None and b['g_last'] is not None and b['g_first'] <= gi <= b['g_last']:
            return b
    return None

if __name__ == '__main__':
    tests = [('extracted/packdata_raw/1197_type02.raw', 905, True,  'R1197 Barkeep dialogue'),
             ('extracted/packdata_raw/1196_type02.raw', 569, False, 'R1196 narration g569'),
             ('extracted/packdata_raw/1196_type02.raw', 575, False, 'R1196 narration g575')]
    for path, gi, expect, label in tests:
        data = open(path, 'rb').read()
        ok, blocks, groups = classify_resource(data)
        b = block_for_group(blocks, gi)
        got = b['dialogue'] if b else None
        verdict = 'PASS' if got == expect else '*** FAIL ***'
        print(f"{verdict}  {label}: g{gi} block g[{b['g_first']}..{b['g_last']}] "
              f"classified dialogue={got}, expected {expect}")
