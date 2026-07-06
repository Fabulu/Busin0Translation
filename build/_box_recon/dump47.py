import sys, os, struct
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'tools'))
from sec1_disasm import walk_resource, LENB

def beu16(b,o): return struct.unpack_from('>H',b,o)[0]
def beu32(b,o): return struct.unpack_from('>I',b,o)[0]
JUMP_OPS={0x08,0x0B,0x11}; GOSUB_OPS={0x12}; COND_OPS={0x06,0x07}

for path in sys.argv[1:]:
    data=open(path,'rb').read()
    ok,instrs,sec1,sec2=walk_resource(data)
    n=len(sec1)
    print(f'=== {os.path.basename(path)} ok={ok} ===')
    from collections import Counter
    cnt=Counter(instrs.values())
    # show interesting opcode counts
    for op in (0x04,0x14,0x47,0x48,0x60,0x0C,0x0D):
        print(f'  op {op:#04x}: {cnt.get(op,0)}')
    # list 0x47/0x48 operands
    for pc in sorted(instrs):
        op=instrs[pc]
        if op==0x47:
            print(f'   {pc:5d} 0x47 a={beu16(sec1,pc+2)} b={beu16(sec1,pc+4)}')
        elif op==0x48:
            print(f'   {pc:5d} 0x48 a={beu16(sec1,pc+2)} b(width)={beu16(sec1,pc+4)} c={beu16(sec1,pc+6)}')
