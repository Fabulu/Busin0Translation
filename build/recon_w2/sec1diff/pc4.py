import struct,sys,os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,os.path.abspath('tools'))
import sec1_disasm as S
ee=open('build/recon_tri/extract/requestbroken__ee.bin','rb').read()
base=0x11c3d20
sec1=ee[base:base+47136]
ok,instrs=S.walk(sec1)
# instructions near 0xb820
near=sorted(p for p in instrs if 0xb700<=p<=0xb820)
print("instrs in [0xb700,0xb820]:")
for p in near:
    op=instrs[p]; ln=S.LENB[op]
    print("  0x%04x op=0x%02x len=%d  %s"%(p,op,ln,sec1[p:p+ln].hex()))
print("max instr pc:",hex(max(instrs)))
# raw bytes b7d0..b840
print("\nraw b7c0..b840:",sec1[0xb7c0:0xb820].hex())
# The state +0x008 = 0x1137980 - what is it (a return/stack?)
# And the flags +0x010=0x4000c, +0x014=4. Likely a WAIT state.
# Let's also check: is there a SECOND active script context? find all structs with base in packdata-loaded range
