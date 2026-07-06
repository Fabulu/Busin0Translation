import struct
data=open("extracted/SLPM_653.78","rb").read()
# look for: lui $X,hi ; addiu gp,$X,lo  OR  ori. Also daddiu. Scan whole exe for any write to gp(28)
# Most common: 0x3C1Chhhh (lui gp,hh) then 0x279Cllll (addiu gp,gp,ll)
for off in range(0x80, len(data)-4, 4):
    w=struct.unpack_from("<I",data,off)[0]
    # addiu/daddiu gp,gp/at -> gp ; rt=28
    rt=(w>>16)&31; op=w>>26; rs=(w>>21)&31
    if rt==28 and op in (0x0F,):  # lui gp
        hi=w&0xFFFF
        w2=struct.unpack_from("<I",data,off+4)[0]
        op2=w2>>26; rt2=(w2>>16)&31; rs2=(w2>>21)&31
        if rt2==28 and rs2==28 and op2 in (0x09,0x0D,0x19):
            lo=w2&0xFFFF
            if op2==0x09: lo = lo-0x10000 if lo&0x8000 else lo
            print(f"@0x{off:X}: lui gp,0x{hi:X}; op{op2:#x} -> gp=0x{(hi<<16)+lo & 0xFFFFFFFF:08X}")
