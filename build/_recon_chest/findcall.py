import struct
data=open(r'C:/programmieren/wizardrytranslation/runs/CLAUDE-RUNS/RUN-20260623-1835-box-request-formatting/subagents/chest/eeMemory.bin','rb').read()
import sys
target=int(sys.argv[1],16)
# jal target encoding: op=3, addr = (va&0xF0000000)|(idx<<2). For EXE region, top nibble 0.
idx=(target>>2)&0x3FFFFFF
jal=(3<<26)|idx
jalb=struct.pack('<I',jal)
i=0;hits=[]
while True:
    j=data.find(jalb,i)
    if j<0:break
    if j%4==0 and 0x100000<=j<0x600000:
        hits.append(j)
    i=j+1
for h in hits: print('jal 0x%X  from 0x%X'%(target,h))
print('count',len(hits))
