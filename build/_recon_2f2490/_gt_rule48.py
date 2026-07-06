import sys, os, struct
sys.path.insert(0, r'C:\programmieren\wizardrytranslation\tools')
from sec1_disasm import LENB, JUMP_OPS, GOSUB_OPS, COND_OPS
from patch_section1_offsets import parse_sec2_group_offsets
RAW = r'C:\programmieren\wizardrytranslation\extracted\packdata_raw'
def load(res):
    raw = open(os.path.join(RAW, '%04d_type02.raw' % res), 'rb').read()
    sec2_off = struct.unpack_from('<I', raw, 0x18)[0]
    sec1 = raw[0x20:sec2_off]
    sec2_size = struct.unpack_from('<I', raw, 0x14)[0]
    sec2 = raw[sec2_off:sec2_off + sec2_size]
    groups, _ = parse_sec2_group_offsets(sec2)
    return sec1, groups
def beu16(b,o): return struct.unpack_from('>H',b,o)[0]
def beu32(b,o): return struct.unpack_from('>I',b,o)[0]

def sim(res):
    """CF sim tracking the persistent window mode set by opcode 0x48 operand b.
    b & 0x80 -> DIAL (nameplate window); else NARR. Each pc visited once with
    first-reached mode."""
    sec1, groups = load(res)
    n = len(sec1)
    gclass = {}
    visited = {}
    work = [(0, None)]   # (pc, current_mode: 'DIAL'/'NARR'/None)
    while work:
        pc, mode = work.pop()
        while 0 <= pc and pc + 2 <= n:
            if pc in visited:
                break
            visited[pc] = mode
            op = beu16(sec1, pc)
            if op >= 193: break
            if op == 0x48:
                b = beu16(sec1, pc + 4)
                mode = 'DIAL' if (b & 0x80) else 'NARR'
            elif op == 0x04:
                off = beu32(sec1, pc+2); cnt = beu32(sec1, pc+6)
                if cnt:
                    end = off + cnt
                    for gi,(gs,ge) in enumerate(groups):
                        if not (ge<off or gs>=end):
                            if gi not in gclass:
                                gclass[gi] = mode if mode else 'NARR'
            ln = LENB[op]
            if op in JUMP_OPS:
                if pc+6>n: break
                pc = beu32(sec1, pc+2); continue
            if op in GOSUB_OPS:
                if pc+6<=n:
                    t=beu32(sec1,pc+2)
                    if t<n and t not in visited: work.append((t,mode))
            if op in COND_OPS:
                if pc+14<=n:
                    t=beu32(sec1,pc+10)
                    if t<n and t not in visited: work.append((t,mode))
            pc += ln
    return gclass, groups

if __name__ == '__main__':
    GT = {
        1197: {'DIAL': [4,9,10,904,922,925,927,929], 'NARR': [3,7,13,926]},
        1196: {'DIAL': [577], 'NARR': [569,575,616,568,570,615]},
    }
    tot=ok=0
    for res in (1197,1196):
        gclass,groups=sim(res)
        print('=== R%d'%res)
        for want,gs in GT[res].items():
            for g in gs:
                got=gclass.get(g,'NONE')
                good=(got==want); tot+=1; ok+=good
                print('   [%s] g%-4d want=%s got=%s'%('OK' if good else 'XX',g,want,got))
    print('SCORE %d/%d'%(ok,tot))
