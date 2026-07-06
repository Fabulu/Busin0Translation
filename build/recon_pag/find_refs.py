import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
D=open('extracted/SLPM_653.78','rb').read()
def v2f(va): return va-0x100000+0x80
def f2v(off): return off-0x80+0x100000
# scan for JAL to target. JAL opcode=000011 (3). instr = (3<<26)|(target>>2)
TEXT_START=0x100000
TEXT_END=0x100000+0x3fdc80
targets=[int(x,16) for x in sys.argv[1:]]
for tgt in targets:
    jt=(0x0c000000)|((tgt>>2)&0x03ffffff)
    jtb=struct.pack('<I',jt)
    print('=== refs to %08x (jal word %08x) ==='%(tgt,jt))
    idx=0
    found=[]
    while True:
        i=D.find(jtb, v2f(TEXT_START)+idx)
        if i<0 or i> v2f(TEXT_END): break
        found.append(f2v(i))
        idx=i-v2f(TEXT_START)+4
    for f in found:
        print('  jal at %08x'%f)
    print('  total %d'%len(found))
