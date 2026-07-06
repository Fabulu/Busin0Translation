import struct,sys
sys.stdout.reconfigure(encoding='utf-8')
ee=open('build/recon_tri/extract/requestbroken__ee.bin','rb').read()
sv=0x564ed0
depth=struct.unpack_from("<h",ee,sv+0x294)[0]
print("call-stack depth (struct+0x294):",depth)
# the stack: struct+8 + idx*4
print("stack entries (struct+8.. ):")
for k in range(0,12):
    v=struct.unpack_from("<I",ee,sv+8+k*4)[0]
    base=0x11c3d20
    rel = v-base if base<=v<base+0xb840 else None
    print("  [%d] +0x%x = 0x%08x  sec1rel=%s"%(k,8+k*4,v, hex(rel) if rel is not None else '-'))
