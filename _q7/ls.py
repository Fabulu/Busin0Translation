import struct
ee=open('_q7/chargen_ee.bin','rb').read()
print("LEFTSHIFT @0x4C7690 first 32 bytes:", ee[0x4C7690:0x4C7690+32].hex())
nz=sum(1 for b in ee[0x4C7690:0x4C7690+96] if b!=0)
print("nonzero entries in 0x4C7690..+96:", nz)
# Is it actually Patch14's LEFTSHIFT? check what's there
print("vals[0..16]:", list(ee[0x4C7690:0x4C7690+16]))
