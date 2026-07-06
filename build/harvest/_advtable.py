import struct
ee=open("C:/programmieren/wizardrytranslation/build/harvest/_requestperfect/eeMemory.bin","rb").read()
base=0x4C7564
print("=== ADV table @0x4C7564 (live) first 0x60 bytes ===")
row=ee[base:base+0x60]
print(" ".join("%02x"%b for b in row))
# gid for space ' '=0x20 -> char-0x20=0 ; 'M'=0x4D-0x20=0x2D ; 'i'=0x69-0x20=0x49
for ch in [' ','M','i','D','u']:
    gid=ord(ch)-0x20
    print(f"  ADV['{ch}'] gid={gid} -> {ee[base+gid]}")
# Patch 14 marker check: 0x3097A0 should be j 0x4C7540
print("0x3097A0 =", "0x%08X"%struct.unpack_from("<I",ee,0x3097A0)[0])
print("0x4C7540 first words (Patch14 cave):")
for i in range(8):
    print("  0x%06X: %08X"%(0x4C7540+i*4, struct.unpack_from("<I",ee,0x4C7540+i*4)[0]))
