import sys, zipfile, struct
sys.stdout.reconfigure(encoding='utf-8')
def load(path):
    z=zipfile.ZipFile(path)
    for n in z.namelist():
        if 'eeMemory' in n.lower() or n.lower().endswith('.bin') and z.getinfo(n).file_size>=33554432:
            return z.read(n)
    # fallback: largest
    biggest=max(z.namelist(), key=lambda n:z.getinfo(n).file_size)
    return z.read(biggest)
def u32(m,a): return struct.unpack('<I',m[a:a+4])[0]
def u16(m,a): return struct.unpack('<H',m[a:a+2])[0]
def u8(m,a): return m[a]
if __name__=='__main__':
    m=load(sys.argv[1])
    print('len',len(m))
    for a in sys.argv[2:]:
        addr=int(a,16); print(f"0x{addr:08X}: u32=0x{u32(m,addr):08X} u16=0x{u16(m,addr):04X} u8=0x{u8(m,addr):02X}")
