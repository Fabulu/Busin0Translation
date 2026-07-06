import sys,struct,zipfile
sys.stdout.reconfigure(encoding='utf-8')
def load(p):
    z=zipfile.ZipFile(p)
    for n in z.namelist():
        if 'eeMemory' in n or n.endswith('.bin'): return z.read(n)
    return z.read(z.namelist()[0])
work=load(r"RAMdumps/tavern104.p2s"); froz=load(r"RAMdumps/fuckinghellman.p2s")
def u32(m,a): return struct.unpack('<I',m[a:a+4])[0]
gp=0x504FF0
for name,m in [('WORK',work),('FROZ',froz)]:
    print(f"--- {name}")
    print(f"  edge word [gp-0x694C]=0x4FE6A4 = {u32(m,0x4FE6A4):#010x}")
    # 0x56D520 struct
    base=0x56D520
    for off in (0x00,0x04,0x08,0x0C,0x10,0x14,0x18,0x1C,0x20,0x24,0x28):
        print(f"  0x56D520+{off:02X} = {u32(m,base+off):#010x}")
    # input edge struct [gp-0x6438]=0x4FEBB8 -> ptr
    p=u32(m,gp-0x6438)
    print(f"  [gp-0x6438]=0x4FEBB8 ptr = {p:#x}; +1C = {u32(m,p+0x1C) if p and p<0x2000000 else 'n/a'}")
