import struct
EXE=r"C:\programmieren\wizardrytranslation\extracted\SLPM_653.78"
VA_BASE=0xFFF80
exe=open(EXE,'rb').read()
# scan code region for immediate 0x139 in addiu/ori/li/slti/sltiu
# code is roughly VA 0x100000..0x4C0000
hits=[]
for fo in range(0,len(exe)-4,4):
    w=struct.unpack('<I',exe[fo:fo+4])[0]
    op=(w>>26)&0x3F
    imm=w&0xFFFF
    if imm==0x139 and op in (0x09,0x0d,0x0a,0x0b,0x0c):
        va=fo+VA_BASE
        hits.append((va,op,w))
names={0x09:'addiu',0x0d:'ori',0x0a:'slti',0x0b:'sltiu',0x0c:'andi'}
for va,op,w in hits:
    rt=(w>>16)&0x1f; rs=(w>>21)&0x1f
    print(f"{va:08X} {names[op]} rt={rt} rs={rs}")
print("total",len(hits))
