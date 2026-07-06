import sys,struct,zipfile
sys.stdout.reconfigure(encoding='utf-8')
def load(p):
    z=zipfile.ZipFile(p)
    for n in z.namelist():
        if 'eeMemory' in n or n.endswith('.bin'): return z.read(n)
    return z.read(z.namelist()[0])
work=load(r"RAMdumps/tavern104.p2s"); froz=load(r"RAMdumps/fuckinghellman.p2s")
def u16(m,a): return struct.unpack('<H',m[a:a+2])[0]
def u8(m,a): return m[a]
def u32(m,a): return struct.unpack('<I',m[a:a+4])[0]
ctx=0x1137a00; gp=0x504FF0
for name,m in [('WORK',work),('FROZ',froz)]:
    print(f"--- {name}")
    print(f"  ctx+0x290 (sel/col) = {u32(m,ctx+0x290):#x}")
    print(f"  ctx+0x2A2 (confirm phase u16) = {u16(m,ctx+0x2A2):#x}")
    print(f"  ctx+0x2A4 (cancel switch u16) = {u16(m,ctx+0x2A4):#x}")
    print(f"  ctx+0x29A (u16) = {u16(m,ctx+0x29A):#x}")
    print(f"  ctx+0x29C (repeat timer u16) = {u16(m,ctx+0x29C):#x}")
    print(f"  [gp-0x62D8]=0x4FED18 (party-check gate, ==8?) = {u8(m,gp-0x62D8):#x}")
    print(f"  [gp-0x6940]=0x4FE6B0 (sb zero in 2F2304) = {u8(m,gp-0x6940):#x}")
    print(f"  [gp-0x6930]=0x4FE6C0 (interp loop flag) = {u8(m,gp-0x6930):#x}")
