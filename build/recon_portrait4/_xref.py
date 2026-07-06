import sys,struct
sys.stdout.reconfigure(encoding='utf-8')
EXE=open('extracted/SLPM_653.78','rb').read()
def v2f(va): return va-0x100000+0x80
def f2v(fo): return fo-0x80+0x100000
seg_start=0x80; seg_end=0x80+0x3FDC80
def find_jal(target_va):
    # jal encoding: op=3, target = (va&0x0FFFFFFC)>>2 ; word = (3<<26)|((target_va>>2)&0x03FFFFFF)
    tgt=(target_va>>2)&0x03FFFFFF
    word=(3<<26)|tgt
    res=[]
    for fo in range(seg_start,seg_end,4):
        w=struct.unpack_from('<I',EXE,fo)[0]
        if w==word:
            res.append(f2v(fo))
    return res
import sys
for t in sys.argv[1:]:
    tv=int(t,16)
    callers=find_jal(tv)
    print(f"callers of 0x{tv:08X}: {[hex(c) for c in callers]}")
