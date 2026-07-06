import struct
exe=open("C:/programmieren/wizardrytranslation/extracted/SLPM_653.78","rb").read()
def fo(va): return va-0x100000+0x80
# scan func 0x307DA0..0x309800 for sw/sh to sp+0x110 (offset 272) and sp+0x178(376) and sp+0x1ce(462)
# store-to-sp: op sw=0x2b, sh=0x29, base rs=29(sp)
def scan(target_off, label):
    print(f"--- stores to sp+0x{target_off:X} ({target_off}) in 0x307000..0x309900 ---")
    for va in range(0x307000,0x309900,4):
        w=struct.unpack_from("<I",exe,fo(va))[0]
        op=w>>26; rs=(w>>21)&31; rt=(w>>16)&31; imm=w&0xffff
        simm=imm-0x10000 if imm&0x8000 else imm
        if rs==29 and simm==target_off and op in (0x29,0x2b,0x28):
            # also dump the few preceding insns to see what rt holds
            print(f"  0x{va:06X}: op=0x{op:02X} store rt={rt} -> sp+0x{target_off:X}")
scan(0x110,"metric flag")
scan(0x178,"size param[sp+0x178]")
