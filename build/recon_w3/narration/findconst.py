import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
data=open("extracted/SLPM_653.78",'rb').read()
def va2off(va): return va-0x100000+0x80
# scan VA range for immediates of 24 (0x18) in addiu/ori/sll-by patterns, and float 24.0
lo,hi=0x302000,0x306000
off0=va2off(lo)
for va in range(lo,hi,4):
    o=va2off(va)
    w=struct.unpack('<I',data[o:o+4])[0]
    op=w>>26
    imm=w&0xffff
    # addiu(0x09)/ori(0x0d)/slti with imm==24 or 0x18
    if op in (0x09,0x0d,0x0a,0x0b) and imm==24:
        rt=(w>>16)&0x1f; rs=(w>>21)&0x1f
        names={0x09:'addiu',0x0d:'ori',0x0a:'slti',0x0b:'sltiu'}
        print(f"0x{va:08x}: {names[op]} rt={rt} rs={rs} imm=24")
    # sll by 3 then add (x24 = x*8*3 or x*16+x*8). sll imm field bits 6-10
    if op==0 and (w&0x3f)==0 and ((w>>6)&0x1f)==3:  # sll ,,3
        pass
# search for float constant 24.0 (0x41C00000) in range
needle=struct.pack('<f',24.0)
i=off0
end=va2off(hi)
while True:
    j=data.find(needle,i,end)
    if j<0: break
    va=j-0x80+0x100000
    print(f"FLOAT24.0 @ va 0x{va:08x}")
    i=j+1
