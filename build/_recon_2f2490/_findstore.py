import struct,sys
sys.stdout.reconfigure(encoding='utf-8')
VA_BASE=0xFFF80
exe=open(r'C:\programmieren\wizardrytranslation\extracted\SLPM_653.78','rb').read()
# find sw $rt, -0x6804($gp)  => op=0x2B rs=gp(28) imm=0x97FC
# also lw -0x6804($gp) op=0x23
target_imm=0x97FC
for op,name in ((0x2B,'sw'),(0x23,'lw'),(0x09,'addiu')):
    print(f"=== {name} ...,{hex(target_imm)}($gp) ===")
    n=0
    for off in range(0,len(exe)-4,4):
        w=struct.unpack('<I',exe[off:off+4])[0]
        o=(w>>26)&0x3F; rs=(w>>21)&0x1F; rt=(w>>16)&0x1F; imm=w&0xFFFF
        if o==op and rs==28 and imm==target_imm:
            va=off+VA_BASE
            print(f"  {va:08X}  rt={rt}  w={w:08X}")
            n+=1
            if n>40: break
