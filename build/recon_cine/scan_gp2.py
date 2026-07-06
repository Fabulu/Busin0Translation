import struct
data=open("extracted/SLPM_653.78","rb").read()
# lui $r,hi ; addiu/ori gp,$r,lo  (any source reg)
for off in range(0x80, 0x8000, 4):
    w=struct.unpack_from("<I",data,off)[0]
    if (w>>26)==0x0F:  # lui rt,hi
        rt=(w>>16)&31; hi=w&0xFFFF
        w2=struct.unpack_from("<I",data,off+4)[0]
        op2=w2>>26; rt2=(w2>>16)&31; rs2=(w2>>21)&31
        if rt2==28 and rs2==rt and op2 in (0x09,0x0D):
            lo=w2&0xFFFF
            if op2==0x09: lo = lo-0x10000 if lo&0x8000 else lo
            print(f"@0x{off:X}: lui r{rt},0x{hi:X}; gp=0x{(hi<<16)+lo & 0xFFFFFFFF:08X}")
