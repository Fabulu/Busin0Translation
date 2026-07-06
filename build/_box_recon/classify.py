import sys, os, struct
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'tools'))
from sec1_disasm import walk_resource, LENB

# Opcode 0x60 sets ctx+0x298 = u16 operand (if <10).  Opcode 0x04 = DISPLAY_TEXT.
# DISPLAY_TEXT renders BOXED DIALOGUE (nameplate) iff ctx+0x298 != -1.
# ctx+0x298 starts at -1 (ctx init). Only 0x60 writes a valid speaker slot.
# We do a path-sensitive linear walk: for every reachable DISPLAY_TEXT, determine
# whether a 0x60 dominates it on the executed path. We approximate with a
# forward dataflow over the BFS instr set following fallthrough+jumps, tracking
# speaker-state as a 3-valued lattice per pc: UNK(-1 cleared), SET, TOP(both).

def beu16(b,o): return struct.unpack_from('>H',b,o)[0]
def beu32(b,o): return struct.unpack_from('>I',b,o)[0]

JUMP_OPS={0x08,0x0B,0x11}; GOSUB_OPS={0x12}; COND_OPS={0x06,0x07}

def classify(path):
    data=open(path,'rb').read()
    ok,instrs,sec1,sec2=walk_resource(data)
    n=len(sec1)
    # successors
    def succ(pc):
        op=instrs[pc]; ln=LENB[op]; res=[]
        if op in JUMP_OPS:
            return [beu32(sec1,pc+2)]
        if op in GOSUB_OPS:
            t=beu32(sec1,pc+2); res.append(t); res.append(pc+ln); return res
        if op in COND_OPS:
            t=beu32(sec1,pc+10); res.append(t); res.append(pc+ln); return res
        if pc+ln in instrs: res.append(pc+ln)
        elif pc+ln<n: res.append(pc+ln)
        return res
    # state IN per pc: speaker present? -1 no(False), set True. lattice: None=unvisited, set of {F,T}
    IN={pc:set() for pc in instrs}
    IN[0]={False}
    from collections import deque
    wl=deque([0])
    while wl:
        pc=wl.popleft()
        if pc not in instrs: continue
        st=IN[pc]
        op=instrs[pc]
        out=set(st)
        if op==0x60:
            # operand <10 => set True; but op always sets if slot<10. assume sets True.
            out={True}
        for s in succ(pc):
            if s in IN:
                if not IN[s].issuperset(out):
                    IN[s]=IN[s]|out
                    wl.append(s)
    # display groups: each 0x04. classify by IN-state at that pc
    res=[]
    for pc in sorted(instrs):
        if instrs[pc]==0x04:
            st=IN[pc]
            if st=={True}: c='DIALOGUE'
            elif st=={False}: c='NARRATION'
            elif st==set(): c='UNREACHED'
            else: c='MIXED'
            res.append((pc,c))
    return res,instrs

if __name__=='__main__':
    for p in sys.argv[1:]:
        r,instrs=classify(p)
        n60=sum(1 for pc in instrs if instrs[pc]==0x60)
        n14=sum(1 for pc in instrs if instrs[pc]==0x14)
        print(f'{os.path.basename(p)}: {len(r)} DISPLAY, {n60} x0x60(speaker), {n14} x0x14')
        from collections import Counter
        print('  ',Counter(c for _,c in r))
