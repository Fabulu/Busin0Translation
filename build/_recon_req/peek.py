import sys,struct,zipfile,io
sys.stdout.reconfigure(encoding='utf-8')

def load_ee(path):
    z=zipfile.ZipFile(path)
    names=z.namelist()
    ee=None
    for n in names:
        if 'eeMemory' in n or n.endswith('.bin') and 'ee' in n.lower():
            ee=n;break
    if ee is None:
        # pick largest
        ee=max(names,key=lambda n:z.getinfo(n).file_size)
    return z.read(ee)

def u32(m,a): return struct.unpack('<I',m[a:a+4])[0]
def u16(m,a): return struct.unpack('<H',m[a:a+2])[0]
def u8(m,a): return m[a]

def dump(path):
    m=load_ee(path)
    print('==== ',path,' len',hex(len(m)))
    gp=0x504FF0
    glob=u32(m,0x4FEDBC)  # gp-0x6234
    print('global[0x4FEDBC] (hub menu ctx / active top) =',hex(glob))
    glob2=u32(m,gp-0x6438) # -0x6438 used by chooser/unlink
    print('global[gp-0x6438] (0x%X) =' % (gp-0x6438),hex(glob2))
    if glob2:
        print('  [glob2+0x1c] =', hex(u32(m,glob2+0x1c)))
    # parent ctx 0x01137880
    p=0x01137880
    print('parent 0x01137880 +0x1c =',hex(u32(m,p+0x1c)), '+0x7c =',hex(u16(m,p+0x7c)), '+0x70=',hex(u16(m,p+0x70)),'+0x8=',hex(u8(m,p+0x8)))
    # chooser host ctx 0x011EDEC0
    c=0x011EDEC0
    print('chooser host 0x011EDEC0 +0x8 =',hex(u8(m,c+0x8)),'+0x4(sub)=',hex(u32(m,c+0x4)),'+0x0=',hex(u32(m,c+0x0)))
    sub=u32(m,c+0x4)
    if sub:
        print('  sub-ctx',hex(sub),'+0x8(state)=',hex(u16(m,sub+0x8)),'+0xc=',hex(u8(m,sub+0xc)))
    # hub menu ctx 0x01137A00
    h=0x01137A00
    print('hub 0x01137A00 +0x0=',hex(u32(m,h+0x0)),'+0xA0=',hex(u8(m,h+0xA0)),'+0xAC=',hex(u8(m,h+0xAC)),'+0xB0=',hex(u8(m,h+0xB0)),'+0x290=',hex(u32(m,h+0x290)))

for p in sys.argv[1:]:
    try:
        dump(p)
    except Exception as e:
        print('ERR',p,e)
