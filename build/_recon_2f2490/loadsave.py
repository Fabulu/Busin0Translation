import zipfile,struct,sys,os
def load_ee(path):
    z=zipfile.ZipFile(path)
    for n in z.namelist():
        if n.endswith('eeMemory.bin') or 'eeMemory' in n:
            return z.read(n)
    # fallback: largest member
    biggest=max(z.namelist(),key=lambda n:z.getinfo(n).file_size)
    return z.read(biggest)
if __name__=='__main__':
    path=sys.argv[1]
    ee=load_ee(path)
    print("size",len(ee))
    # dump hub ctx
    def u32(va): return struct.unpack('<I',ee[va:va+4])[0]
    def u16(va): return struct.unpack('<H',ee[va:va+2])[0]
    glob=u32(0x4FEDBC)
    print(f"global[0x4FEDBC] = 0x{glob:08X}")
    if glob and glob<len(ee):
        ctx=glob
        print(f"hub ctx +0x00 (cursor) = 0x{u32(ctx+0x00):08X}")
        print(f"hub ctx +0xA0 = 0x{u32(ctx+0xA0):08X}")
        print(f"hub ctx +0xAC = 0x{u32(ctx+0xAC):08X}")
        print(f"hub ctx +0xB0 = 0x{u32(ctx+0xB0):08X}")
        print(f"hub ctx +0x290 = 0x{u32(ctx+0x290):08X}")
        print(f"hub ctx +0x294 (script sp) = 0x{u16(ctx+0x294):04X}")
        print(f"hub ctx +0x04 = 0x{u32(ctx+0x04):08X}")
    # parent submenu host
    p=0x01137880
    print(f"parent+0x1c = 0x{u32(p+0x1c):08X}")
    print(f"parent+0x7c = 0x{u32(p+0x7c):08X}")
    # chooser child
    c=0x011EDEC0
    print(f"child+0x08 = 0x{u32(c+0x08):08X}")
    # global flag gp-0x694c => gp=0x504FF0 -> 0x4FE6A4
    print(f"flag[gp-0x694c=0x4FE6A4] = 0x{u32(0x504FF0-0x694c):08X}")
