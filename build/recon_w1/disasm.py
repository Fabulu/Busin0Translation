import sys
from capstone import *
from capstone.mips import *
sys.stdout.reconfigure(encoding='utf-8')

d=open('build/recon_tri2/shady4__ee.bin','rb').read()
md=Cs(CS_ARCH_MIPS, CS_MODE_MIPS64|CS_MODE_LITTLE_ENDIAN)
md.detail=True

def dis(va, n, mark=None):
    code=d[va:va+n*4]
    print(f'--- disasm @ 0x{va:X} ({n} insns) ---')
    for ins in md.disasm(code, va):
        m=''
        # flag immediates 0x18,0x12,0x14,0x0C
        if ins.operands:
            for op in ins.operands:
                if op.type==MIPS_OP_IMM and op.imm in (0x18,0x12,0x14,0x0C,0xC,18,24,20,12):
                    m=' <== imm '+hex(op.imm)
        print(f'0x{ins.address:06X}: {ins.mnemonic:8s} {ins.op_str}{m}')

import sys
va=int(sys.argv[1],16) if len(sys.argv)>1 else 0x302DB0
n=int(sys.argv[2]) if len(sys.argv)>2 else 80
dis(va,n)
