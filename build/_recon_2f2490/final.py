import sys,struct,zipfile
sys.stdout.reconfigure(encoding='utf-8')
def load(p):
    z=zipfile.ZipFile(p)
    for n in z.namelist():
        if 'eeMemory' in n or n.endswith('.bin'): return z.read(n)
    return z.read(z.namelist()[0])
work=load(r"RAMdumps/tavern104.p2s"); froz=load(r"RAMdumps/fuckinghellman.p2s")
def u16(m,a): return struct.unpack('<H',m[a:a+2])[0]
def u32(m,a): return struct.unpack('<I',m[a:a+4])[0]
ctx=0x1137a00
for name,m in [('WORK',work),('FROZ',froz)]:
    print(f"--- {name}")
    print(f"  ctx+0x00 script IP = {u32(m,ctx):#x}")
    print(f"  ctx+0x04           = {u32(m,ctx+4):#x}")
    for off in (0x54,0x5C,0x60,0xA0,0xAC,0xB0,0x290):
        print(f"  ctx+0x{off:03X} = {u32(m,ctx+off):#010x}")
# Is script IP inside a known PACKDATA-loaded region? print bytes around IP
for name,m in [('WORK',work),('FROZ',froz)]:
    ip=u32(m,ctx)
    print(f"  {name} bytes @IP {ip:#x}: {m[ip-8:ip+8].hex()}")
