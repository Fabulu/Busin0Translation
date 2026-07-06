import sys, struct, rabbitizer
sys.stdout.reconfigure(encoding='utf-8')
exe=open('extracted/SLPM_653.78','rb').read()
BASE=0xFFF80  # file offset = vaddr - 0xFFF80
def f(va): return va-BASE
def dis(va_start, n, label=''):
    print(f"\n===== {label} 0x{va_start:08X} ({n} instrs) =====")
    off=f(va_start)
    for i in range(n):
        va=va_start+i*4
        raw=struct.unpack_from('<I',exe,off+i*4)[0]
        ins=rabbitizer.Instruction(raw); ins.vram=va
        print(f"  {va:08X}: {raw:08X}  {ins.disassemble()}")
import sys as _s
va=int(_s.argv[1],16); n=int(_s.argv[2]) if len(_s.argv)>2 else 60
dis(va,n)
