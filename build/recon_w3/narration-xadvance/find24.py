import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
EXE="C:/programmieren/wizardrytranslation/extracted/SLPM_653.78"
D=open(EXE,'rb').read()
def v2f(va): return va-0x100000+0x80
def f2v(o): return o-0x80+0x100000
def fields(va):
    w=struct.unpack_from('<I',D,v2f(va))[0]
    return w, w>>26, (w>>21)&31,(w>>16)&31,(w>>11)&31,(w>>6)&31,w&0x3f
lo,hi=0x300000,0x310000
for va in range(lo,hi,4):
    # pattern: sll rd,rt,1 ; addu rx,rd,rt ; sll ry,rx,3  -> *24
    w0,op0,_,rt0,rd0,sa0,fn0=fields(va)
    w1,op1,rs1,rt1,rd1,_,fn1=fields(va+4)
    w2,op2,_,rt2,rd2,sa2,fn2=fields(va+8)
    if op0==0 and fn0==0 and sa0==1 and \
       op1==0 and fn1==0x21 and \
       op2==0 and fn2==0 and sa2==3:
        print(f"{va:08x}: *24 idiom (sll {rd0}<-{rt0}<<1; addu {rd1}; sll {rd2}<<3)")
