import sys, os, struct
sys.path.insert(0, r'C:\programmieren\wizardrytranslation\tools')
from sec1_disasm import LENB, JUMP_OPS, GOSUB_OPS, COND_OPS
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

def beu16(b, o): return struct.unpack_from('>H', b, o)[0]
def beu32(b, o): return struct.unpack_from('>I', b, o)[0]

def exec_sim(res):
    """Control-flow simulation. State = name_channel_active (gp-0x6930 byte,
    set by 0x0C, cleared by 0x0D). At each 0x04 DISPLAY, snapshot state and
    record which groups it covers. BFS over CF; each pc visited once with the
    FIRST-reached state (scene scripts are near-linear so this is stable)."""
    sec1, groups = load(res)
    n = len(sec1)
    # state per display: gi -> 'DIAL'/'NARR'
    gclass = {}
    visited = {}  # pc -> channel_state (to avoid reprocessing)
    # work items: (pc, channel_active)
    work = [(0, 0)]
    while work:
        pc, ch = work.pop()
        while 0 <= pc and pc + 2 <= n:
            if pc in visited:
                break
            visited[pc] = ch
            op = beu16(sec1, pc)
            if op >= 193:
                break
            if op == 0x0C:
                ch = 1
            elif op == 0x0D:
                ch = 0
            elif op == 0x04:
                off = beu32(sec1, pc + 2); cnt = beu32(sec1, pc + 6)
                if cnt:
                    end = off + cnt
                    for gi, (gs, ge) in enumerate(groups):
                        if not (ge < off or gs >= end):
                            # DIALOGUE iff channel active at this display
                            cls = 'DIAL' if ch else 'NARR'
                            # if conflicting, prefer DIAL (channel-set wins)
                            if gi not in gclass or cls == 'DIAL':
                                gclass[gi] = cls
            ln = LENB[op]
            if op in JUMP_OPS:
                if pc + 6 > n: break
                pc = beu32(sec1, pc + 2); continue
            if op in GOSUB_OPS:
                if pc + 6 <= n:
                    t = beu32(sec1, pc + 2)
                    if t < n and t not in visited:
                        work.append((t, ch))
            if op in COND_OPS:
                if pc + 14 <= n:
                    t = beu32(sec1, pc + 10)
                    if t < n and t not in visited:
                        work.append((t, ch))
            pc += ln
    return gclass, groups

if __name__ == '__main__':
    GT = {
        1197: {'DIAL': [4, 9, 10, 904, 922, 925, 927, 929],
               'NARR': [3, 7, 13, 926]},
        1196: {'DIAL': [577], 'NARR': [569, 575, 616, 568, 570, 615]},
    }
    total_ok = total = 0
    for res in (1197, 1196):
        gclass, groups = exec_sim(res)
        print('=== R%d  classified=%d/%d groups' % (res, len(gclass), len(groups)))
        for want, gs in GT[res].items():
            for g in gs:
                got = gclass.get(g, 'NONE')
                ok = (got == want)
                total += 1; total_ok += ok
                print('   [%s] g%-4d want=%s got=%s' % ('OK' if ok else 'XX', g, want, got))
    print('SCORE: %d/%d correct' % (total_ok, total))
