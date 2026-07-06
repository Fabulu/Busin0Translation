import struct,sys,os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,os.path.abspath('tools'))
import sec1_disasm as S
ee=open('build/recon_tri/extract/requestbroken__ee.bin','rb').read()
base=0x11c3d20
sec1=ee[base:base+47136]
# What is at 0x9e5b region and the bytes right before the gap. Disasm linearly from 0x9e4b..0x9e70
print("linear disasm 0x9e3b..0x9e70:")
p=0x9e3b
while p<0x9e72:
    op=(sec1[p]<<8)|sec1[p+1]
    ln=S.LENB.get(op, '?')
    if op>=193:
        print("  0x%04x INVALID op=0x%x"%(p,op)); p+=2; continue
    print("  0x%04x op=0x%02x len=%d %s"%(p,op,ln,sec1[p:p+ln].hex()))
    p+=ln
# So 0x9e5b op=0x11 jumps to 0x4836. After it (no fallthrough) bytes are padding.
# So runtime did NOT fall through 0x9e5b. The runtime reached padding via a different mechanism.
# Let's check: maybe the PC ptr was just left at a stale value and the REAL issue is the dispatcher
# return / a wait flag. Re-examine: is 0xb820 actually 'end of sec1' = the GOSUB return sentinel?
print("\nsec1 len=0x%x, PC off=0xb820, delta=%d"%(len(sec1), len(sec1)-0xb820))
# 0xb820 == len(sec1). So PC == sec1_base + sec1_len exactly = points at sec2_off-0x20... 
# Actually sec2_off=0xb840 file => sec1 ends at file 0xb840 => sec1[0xb820] is last? len=47136=0xb820. yes PC==len.
