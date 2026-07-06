import struct,sys,os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,os.path.abspath('tools'))
import sec1_disasm as S
pri=open('extracted/packdata_raw/1197_type02.raw','rb').read()
pso=struct.unpack_from("<I",pri,0x18)[0]
psec1=pri[0x20:pso]
v99=open('build/patched_type2/1197_type02.raw','rb').read()
vso=struct.unpack_from("<I",v99,0x18)[0]
vsec1=v99[0x20:vso]
ee=open('build/recon_tri/extract/requestbroken__ee.bin','rb').read()
ram=ee[0x11c3d20:0x11c3d20+47136]

# The runaway block 0x9ce9..0x9e61. Compare opcode structure (ignore 0x04 off/cnt & 0x14 off/cnt).
def opbytes(sec1,p,ln,op):
    if op==0x04: return sec1[p:p+2]+sec1[p+10:p+ln]
    if op==0x14: return sec1[p:p+6]+sec1[p+14:p+ln]
    return sec1[p:p+ln]
ok,instrs=S.walk(vsec1)
diffs=0; checked=0
for p in sorted(instrs):
    op=instrs[p]; ln=S.LENB[op]
    a=opbytes(vsec1,p,ln,op); b=opbytes(psec1,p,ln,op)
    checked+=1
    if a!=b:
        diffs+=1
        if diffs<=20: print("STRUCT DIFF pc=0x%x op=0x%02x v99=%s pri=%s"%(p,op,a.hex(),b.hex()))
print("v99 vs pristine: %d instrs checked, %d structural (non-remap) diffs"%(checked,diffs))

# Confirm 0x9e5b op11 jump exists identically in pristine and ram
for nm,s in [("v99",vsec1),("pri",psec1),("ram",ram)]:
    print("%s @0x9e5b: %s  @0x9e61(1A): %s"%(nm,s[0x9e5b:0x9e61].hex(),s[0x9e61:0x9e63].hex()))
# And tail padding identical?
print("v99 tail 0x9e62..end all-zero:", all(x==0 for x in vsec1[0x9e62:]))
print("pri tail 0x9e62..end all-zero:", all(x==0 for x in psec1[0x9e62:]))
print("ram tail 0x9e62..end all-zero:", all(x==0 for x in ram[0x9e62:]))
