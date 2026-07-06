import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
import rabbitizer
exe=open("extracted/SLPM_653.78","rb").read()
def f(va): return va-0x100000+0x80
def dis(s,n,label=""):
    print(f"--- {label} ---")
    for i in range(n):
        va=s+i*4; raw=struct.unpack_from("<I",exe,f(va))[0]
        ins=rabbitizer.Instruction(raw); ins.vram=va
        print(f"0x{va:08X}: {ins.disassemble()}")
import sys as _s
dis(int(_s.argv[1],16), int(_s.argv[2]) if len(_s.argv)>2 else 40, _s.argv[3] if len(_s.argv)>3 else "")
