import struct
data=open(r'C:/programmieren/wizardrytranslation/runs/CLAUDE-RUNS/RUN-20260623-1835-box-request-formatting/subagents/chest/eeMemory.bin','rb').read()
# find gp value: common idiom is lui gp / addiu gp near _start. Search for the gp init.
# Actually find 'lui gp, ; addiu gp,gp,' near 0x100000.. 
# gp typically points to small-data. Let me search for the gp init pattern: 3C1C... (lui gp)
import sys
for a in range(0x100000,0x120000,4):
    w=struct.unpack_from('<I',data,a)[0]
    if (w>>26)==0x0F and ((w>>16)&31)==28: # lui gp
        hi=w&0xFFFF
        w2=struct.unpack_from('<I',data,a+4)[0]
        if (w2>>26)==9 and ((w2>>16)&31)==28 and ((w2>>21)&31)==28: # addiu gp,gp
            lo=w2&0xFFFF; lo=lo-0x10000 if lo&0x8000 else lo
            gp=(hi<<16)+lo
            print('gp init @0x%X gp=0x%X'%(a,gp))
