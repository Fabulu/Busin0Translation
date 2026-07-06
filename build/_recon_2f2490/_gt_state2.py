import sys, os, struct
sys.path.insert(0, r'C:\programmieren\wizardrytranslation\tools')
from sec1_disasm import walk, extract_records
from patch_section1_offsets import parse_sec2_group_offsets
RAW = r'C:\programmieren\wizardrytranslation\extracted\packdata_raw'

def load(res):
    raw = open(os.path.join(RAW, '%04d_type02.raw' % res), 'rb').read()
    sec2_off = struct.unpack_from('<I', raw, 0x18)[0]
    sec2_size = struct.unpack_from('<I', raw, 0x14)[0]
    sec1 = raw[0x20:sec2_off]
    sec2 = raw[sec2_off:sec2_off + sec2_size]
    groups, _ = parse_sec2_group_offsets(sec2)
    return sec1, sec2, groups

def beu16(b,o): return struct.unpack_from('>H',b,o)[0]
def beu32(b,o): return struct.unpack_from('>I',b,o)[0]

# Track last 0x47 and 0x48 operands seen in offset order before each 0x04.
# 0x47 handler 0x2F9490; 0x48 stores byte at gp-0x6930. Let's read their operand bytes.
# We don't know lengths certainly; dump raw bytes of each 0x47/0x48/0x60/0x62.
from sec1_disasm import LENB
for res, gt in [(1197, {3:'NARR',4:'DIAL',7:'NARR',9:'DIAL',10:'DIAL',13:'NARR',
                        904:'DIAL',922:'DIAL',925:'DIAL',926:'NARR',927:'DIAL',929:'DIAL'}),
                (1196, {569:'NARR',575:'NARR',616:'NARR',577:'DIAL',568:'NARR',570:'NARR',615:'NARR'})]:
    sec1, sec2, groups = load(res)
    ok, instrs = walk(sec1)
    order = sorted(instrs)
    # state machine over offset order
    last47 = None   # (pc, operand byte after)
    last48 = None
    # find display block per group
    recs = extract_records(sec1, instrs)
    def grp(off):
        for gi,(gs,ge) in enumerate(groups):
            if gs<=off<=ge: return gi
        return None
    # for each display, snapshot state
    state_at_disp = {}  # block_pc -> (last47, last48)
    cur47=cur48=None
    for pc in order:
        op=instrs[pc]
        if op==0x47:
            cur47=beu16(sec1,pc+2) if pc+4<=len(sec1) else None
        elif op==0x48:
            cur48=sec1[pc+2] if pc+2<len(sec1) else None
        elif op==0x04:
            off=beu32(sec1,pc+2); cnt=beu32(sec1,pc+6)
            if cnt==0: continue
            for gi in range(len(groups)):
                gs,ge=groups[gi]
                if not (ge<off or gs>=off+cnt):
                    state_at_disp.setdefault(gi,(cur47,cur48))
    print('=== R%d'%res)
    for g,lab in gt.items():
        s=state_at_disp.get(g)
        print('   g%-4d %s  last47=%s last48=%s'%(g,lab,s[0] if s else None, s[1] if s else None))
