import sys, struct, json
sys.stdout.reconfigure(encoding='utf-8')
EE='build/recon_portrait4/extract/request__ee.bin'
ee=open(EE,'rb').read()
def rd32(a): return struct.unpack_from('<I',ee,a)[0]
def rd16(a): return struct.unpack_from('<H',ee,a)[0]
RESBASE=0x11C3D20
# Find the ctx struct. ctx +0x00 = pc (byte ptr into sec1). The global 0x564ED0 holds sec1 base.
# The interpreter PC global 0x509F5C -> 0x11C9040 = sec1+0x5320.
# ctx struct: +0x00 pc, +0x08 call stack[16], +0x294 depth. Find ctx base: search for a struct whose
# +0 = a pointer into sec1.
# global 0x509F5C is likely ctx+0x00? Let's dump around 0x509F40..0x50A2E0
print("Dump 0x509F40..0x509FA0:")
for a in range(0x509F40,0x509FA0,4):
    print(f"  0x{a:X} = 0x{rd32(a):08X}")
# stack depth would be at ctx+0x294. If ctx=0x509F5C, depth@0x50A1F0
print("\nIf ctx base=0x509F5C: depth@0x509F5C+0x294=0x%X ="%(0x509F5C+0x294), hex(rd32(0x509F5C+0x294)))
# call stack at ctx+0x08 = 0x509F64
print("call stack[0..7] from 0x509F64:")
for i in range(8):
    print(f"  [{i}] 0x{rd32(0x509F64+i*4):08X}")
