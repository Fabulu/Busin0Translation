import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
data=open("extracted/SLPM_653.78","rb").read()
for off in range(0x80, 0x6000, 4):
    w=struct.unpack_from("<I",data,off)[0]
    if (w>>26)==0x0F and ((w>>16)&31)==28:
        hi=w&0xFFFF
        w2=struct.unpack_from("<I",data,off+4)[0]
        if (w2>>26)==0x09 and ((w2>>16)&31)==28 and ((w2>>21)&31)==28:
            lo=w2&0xFFFF; simm=lo-0x10000 if lo&0x8000 else lo
            print(f"gp @ file 0x{off:X}: 0x{(hi<<16)+simm:08X}")
        if (w2>>26)==0x0D and ((w2>>16)&31)==28 and ((w2>>21)&31)==28:
            print(f"gp @ file 0x{off:X}: 0x{(hi<<16)+(w2&0xFFFF):08X}")
