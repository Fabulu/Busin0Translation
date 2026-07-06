import struct,sys,os
sys.stdout.reconfigure(encoding='utf-8')
v99=open('build/patched_type2/1197_type02.raw','rb').read()
pri=open('extracted/packdata_raw/1197_type02.raw','rb').read()
ee=open('build/recon_tri/extract/requestbroken__ee.bin','rb').read()
base=0x11c3d20
def parts(d):
    o=struct.unpack_from("<I",d,0x18)[0]; return d[0x20:o],o
v1,vo=parts(v99); p1,po=parts(pri)
print("sec2_off v99=0x%x pri=0x%x"%(vo,po))
print("v99 sec1[0xb800:0xb820] (last bytes):",v1[0xb800:0xb820].hex())
print("pri sec1[0xb800:0xb820]:",p1[0xb800:0xb820].hex())
print("ram sec1[0xb800:0xb820]:",ee[base+0xb800:base+0xb820].hex())
# Is v99 sec1 tail all zero?
print("v99 sec1[0x9e62:] all zero:", all(x==0 for x in v1[0x9e62:]))
print("pri sec1[0x9e62:] all zero:", all(x==0 for x in p1[0x9e62:]))
print("ram sec1[0x9e62:0xb820] all zero:", all(x==0 for x in ee[base+0x9e62:base+0xb820]))
# Where does ram sec1 stop being zero near the end?
seg=ee[base:base+0xb840]
# find last nonzero before 0xb820
i=0xb820
while i>0 and seg[i-1]==0: i-=1
print("ram: last nonzero byte before 0xb820 at sec1 off 0x%x"%(i-1))
print("ram sec1[0xb7f0:0xb820]:",seg[0xb7f0:0xb820].hex())
