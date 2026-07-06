import struct
data=open(r'C:/programmieren/wizardrytranslation/runs/CLAUDE-RUNS/RUN-20260623-1835-box-request-formatting/subagents/chest/eeMemory.bin','rb').read()
# Look for code loading immediate 88(0x58) or 89(0x59) AND 39(0x27) in nearby instructions (addiu rt,zero,imm)
# addiu rt,zero,imm = 0x2400xxxx with rs=0. encoding: op9 rs0 rt imm
def imms(val):
    hits=[]
    for a in range(0x100000,0x500000,4):
        w=struct.unpack_from('<I',data,a)[0]
        if (w>>26)==9 and ((w>>21)&31)==0 and (w&0xFFFF)==val:
            hits.append(a)
    return hits
h88=set(imms(88)); h89=set(imms(89)); h39=set(imms(39))
# find h88 near h39 within 0x40 bytes
near=[]
for a in h88:
    for b in h39:
        if abs(a-b)<=0x40: near.append((a,b))
print('88 count',len(h88),'89 count',len(h89),'39 count',len(h39))
print('88 near 39:', ['0x%X/0x%X'%(a,b) for a,b in near[:20]])
# also 88 near 89
near2=[(a,b) for a in h88 for b in h89 if abs(a-b)<=0x60]
print('88 near 89:', ['0x%X/0x%X'%(a,b) for a,b in near2[:20]])
