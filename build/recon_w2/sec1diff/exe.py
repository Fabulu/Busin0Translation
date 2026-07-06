import struct,sys
sys.stdout.reconfigure(encoding='utf-8')
ee=open('build/recon_tri/extract/requestbroken__ee.bin','rb').read()
base=0x11c3d20
lo,hi=base,base+0xb840
hits=[]
for i in range(0,len(ee)-7,4):
    v0=struct.unpack_from("<I",ee,i)[0]
    if v0==base:
        ctx=[struct.unpack_from("<I",ee,i+k*4)[0] for k in range(-4,8)]
        hits.append((i,ctx))
print("struct base==0x%x occurrences:"%base,len(hits))
for off,ctx in hits[:30]:
    print("@0x%x"%off, ["0x%x"%c for c in ctx])
