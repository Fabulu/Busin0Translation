import struct,sys
ee=open(sys.argv[1],'rb').read()
print("size",len(ee))
def u32(va): return struct.unpack('<I',ee[va:va+4])[0]
def u16(va): return struct.unpack('<H',ee[va:va+2])[0]
glob=u32(0x4FEDBC)
print(f"global[0x4FEDBC] = 0x{glob:08X}")
if glob and glob+0x300<len(ee):
    ctx=glob
    print(f"hub +0x00 cursor = 0x{u32(ctx+0x00):08X}")
    print(f"hub +0x04        = 0x{u32(ctx+0x04):08X}")
    print(f"hub +0xA0        = 0x{u32(ctx+0xA0):08X}")
    print(f"hub +0xAC        = 0x{u32(ctx+0xAC):08X}")
    print(f"hub +0xB0        = 0x{u32(ctx+0xB0):08X}")
    print(f"hub +0x290       = 0x{u32(ctx+0x290):08X}")
    print(f"hub +0x294 sp    = 0x{u16(ctx+0x294):04X}")
p=0x01137880
print(f"parent+0x1c = 0x{u32(p+0x1c):08X}")
print(f"parent+0x7c = 0x{u32(p+0x7c):08X}")
c=0x011EDEC0
print(f"child(0x011EDEC0)+0x08 = 0x{u32(c+0x08):08X}")
print(f"flag[0x4FE6A4] = 0x{u32(0x4FE6A4):08X}")
print(f"flag[gp-0x6930=0x4FE6C0] = 0x{u32(0x504FF0-0x6930):08X}")
print(f"flag[gp-0x692c=0x4FE6C4] = 0x{u32(0x504FF0-0x692c):08X}")
