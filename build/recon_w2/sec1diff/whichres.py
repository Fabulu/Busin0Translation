import struct,sys,os
sys.stdout.reconfigure(encoding='utf-8')
ee=open('build/recon_tri/extract/requestbroken__ee.bin','rb').read()
base=0x11c3d20
# The loaded blob = file[0x20:] of R1197. Verify by matching sec1 first 0x40 bytes.
v99=open('build/patched_type2/1197_type02.raw','rb').read()
print("RAM[0:0x40]:",ee[base:base+0x40].hex())
print("v99 file[0x20:0x60]:",v99[0x20:0x60].hex())
print("match:", ee[base:base+0x200]==v99[0x20:0x220])
# How well does RAM match v99 across whole sec1?
v99_s1=v99[0x20:struct.unpack_from("<I",v99,0x18)[0]]
ram_s1=ee[base:base+len(v99_s1)]
d=sum(1 for i in range(len(v99_s1)) if v99_s1[i]!=ram_s1[i])
print("RAM-sec1 vs v99-sec1 byte diffs:",d," / ",len(v99_s1))
# RAM is v96. Check sec2 too: does RAM contain v96 English (different remap)?
ram_full=ee[base:base+len(v99)-0x20]
# match RAM sec2 start
print("RAM sec2 head:",ee[base+0xb820:base+0xb840].hex())
print("v99 sec2 head:",v99[0xb840:0xb860].hex())
