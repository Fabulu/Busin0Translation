import struct,sys,os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,os.path.abspath('tools'))
import sec1_disasm as S
ee=open('build/recon_tri/extract/requestbroken__ee.bin','rb').read()
base=0x11c3d20; sec1=ee[base:base+47136]
ok,instrs=S.walk(sec1)
# The block ending at 0x9e5b (op11 jump to 0x4836). Let's find the basic block start:
# walk back: find nearest jump-target or block boundary <= 0x9e5b
# Print the basic block containing the runaway tail: from a preceding jump landing
targets=set()
for p in instrs:
    op=instrs[p]
    if op in (0x08,0x0b,0x11,0x12): targets.add(struct.unpack_from(">I",sec1,p+2)[0])
    elif op in (0x06,0x07): targets.add(struct.unpack_from(">I",sec1,p+10)[0])
# find block start <= 0x9da9 that is a jump target
bs=[t for t in targets if t<=0x9e5b]
bstart=max(bs)
print("block start (nearest jump target <=0x9e5b):0x%x"%bstart)
p=bstart
while p<=0x9e61 and p in instrs:
    op=instrs[p];ln=S.LENB[op]
    extra=""
    if op==0x04:
        off=struct.unpack_from(">I",sec1,p+2)[0];cnt=struct.unpack_from(">I",sec1,p+6)[0]
        extra="DISPLAY off=%d cnt=%d"%(off,cnt)
    if op in (0x08,0xb,0x11,0x12): extra="JMP->0x%x"%struct.unpack_from(">I",sec1,p+2)[0]
    if op in (0x06,0x07): extra="COND->0x%x"%struct.unpack_from(">I",sec1,p+10)[0]
    print("  0x%04x op=0x%02x %s %s"%(p,op,sec1[p:p+ln].hex(),extra))
    p+=ln
