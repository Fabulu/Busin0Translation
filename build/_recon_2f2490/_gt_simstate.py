import sys, os, struct
sys.path.insert(0, r'C:\programmieren\wizardrytranslation\tools')
from sec1_disasm import walk, LENB, JUMP_OPS, GOSUB_OPS, COND_OPS
from patch_section1_offsets import parse_sec2_group_offsets

RAW = r'C:\programmieren\wizardrytranslation\extracted\packdata_raw'

def load(res):
    raw = open(os.path.join(RAW, '%04d_type02.raw' % res), 'rb').read()
    sec2_off = struct.unpack_from('<I', raw, 0x18)[0]
    sec2_size = struct.unpack_from('<I', raw, 0x14)[0]
    sec1 = raw[0x20:sec2_off]
    sec2 = raw[sec2_off:sec2_off + sec2_size]
    groups, _ = parse_sec2_group_offsets(sec2)
    return sec1, groups

def beu16(b, o):
    return struct.unpack_from('>H', b, o)[0]
def beu32(b, o):
    return struct.unpack_from('>I', b, o)[0]

def group_of(off, groups):
    for gi, (gs, ge) in enumerate(groups):
        if gs <= off <= ge:
            return gi
    return None

def sim(res):
    """Linear walk in PROGRAM ORDER (offset order) tracking name-channel state.
    For each 0x04 DISPLAY at offset, record whether a name channel is active."""
    sec1, groups = load(res)
    ok, instrs = walk(sec1)
    # Walk in offset order; track last 0x0C (set) / 0x0D (clear) before each 0x04.
    name_active = False   # set by 0x0C, cleared by 0x0D
    last_label_pc = None  # last 0x14
    results = []  # (display_off, display_grp, name_active, had_label)
    for pc in sorted(instrs):
        op = instrs[pc]
        if op == 0x0C:
            name_active = True
        elif op == 0x0D:
            name_active = False
        elif op == 0x14:
            last_label_pc = pc
        elif op == 0x04:
            off = beu32(sec1, pc + 2)
            cnt = beu32(sec1, pc + 6)
            if cnt == 0:
                continue
            gi = group_of(off, groups)
            results.append((pc, off, gi, name_active))
    return results, groups

if __name__ == '__main__':
    gt = {
        1197: {'dial': [4, 9, 10, 904, 922, 925, 927, 929],
               'narr': [3, 7, 13, 926]},
        1196: {'dial': [577], 'narr': [569, 575, 616, 568, 570, 615]},
    }
    for res in (1197, 1196):
        results, groups = sim(res)
        # map group -> name_active at its display
        gmap = {}
        for pc, off, gi, na in results:
            gmap[gi] = na
        print('=== R%d (groups=%d, display=%d)' % (res, len(groups), len(results)))
        for cls in ('dial', 'narr'):
            for g in gt[res][cls]:
                na = gmap.get(g, 'NO-DISPLAY')
                expect = 'dialogue' if cls == 'dial' else 'narration'
                pred = 'dialogue' if na is True else ('narration' if na is False else '?')
                mark = 'OK' if (pred == expect) else 'XX'
                print('   [%s] g%-4d expect=%-9s name_active=%s pred=%s' % (mark, g, expect, na, pred))
