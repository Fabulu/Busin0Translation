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
gp=0x504FF0
# scheduler menu object @ gp-0x6230
for name,m in [('WORK',work),('FROZ',froz)]:
    obj=u32(m,gp-0x6230)
    print(f"--- {name} sched-obj @gp-0x6230 = {obj:#x}")
    print(f"   +08 handler  = {u32(m,obj+8):#x}")
    print(f"   +0C ctx/arg  = {u32(m,obj+0xC):#x}")
    print(f"   +2A4 state   = {u16(m,obj+0x2A4):#x}")
print()
# Per prompt s1=a0=0x1379D0 (frozen). The handler arg a0 == sched-obj+0xC? check
# Try s1 = the +0x0C ctx of sched obj
for name,m in [('WORK',work),('FROZ',froz)]:
    obj=u32(m,gp-0x6230)
    s1=u32(m,obj+0xC)
    print(f"--- {name}: s1(=obj+0xC ctx) = {s1:#x}  (final-block reads s1+0x290/29A/29C/2A2/2A4)")
    for off in (0x290,0x29A,0x29C,0x2A2,0x2A4,0x00,0x04,0x08,0x0A):
        try: print(f"     +{off:03X} = {u32(m,s1+off):#010x}  (u16 {u16(m,s1+off):#06x})")
        except: pass
