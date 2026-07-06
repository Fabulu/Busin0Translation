import struct,sys,os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,os.path.abspath('tools'))
import sec1_disasm as S
v99=open('build/patched_type2/1197_type02.raw','rb').read()
# compute word offset of group 652 start in sec2
o=struct.unpack_from("<I",v99,0x18)[0]; s2=v99[o:]
gi=0; start=0; off_of={}
for i in range(0,len(s2)-1,2):
    w=(s2[i]<<8)|s2[i+1]
    if gi not in off_of: off_of[gi]=start//2
    if w==0xFFFF:
        gi+=1; start=i+2
for g in [63,652,916]:
    print("group %d starts at sec2 word offset %d"%(g,off_of.get(g)))
# Now find 0x04 DISPLAY in sec1 whose off == these word offsets
ok,instrs=S.walk(v99[0x20:o])
s1=v99[0x20:o]
disp={}
for pc in instrs:
    if instrs[pc]==0x04:
        doff=struct.unpack_from(">I",s1,pc+2)[0]
        disp.setdefault(doff,[]).append(pc)
for g in [63,652,916]:
    wo=off_of.get(g)
    print("DISPLAY pcs referencing group %d (wordoff %d):"%(g,wo), [hex(x) for x in disp.get(wo,[])])
