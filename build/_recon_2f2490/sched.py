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
# scheduler list: walk objects. obj+8=handler, obj+0xC=ctx. Find link field by scanning common offsets.
# Dump a window of both sched-obj to compare structure
for name,m in [('WORK',work),('FROZ',froz)]:
    obj=u32(m,gp-0x6230)
    print(f"--- {name} sched-obj {obj:#x}")
    for off in range(0,0x30,4):
        print(f"   +{off:02X}={u32(m,obj+off):#010x}", end='')
    print()
# Look for chain: many engines store linked list. Check +0x00 (next?) 
# Also enumerate ALL objects whose +8 points into 0x2Fxxxx (menu handlers) by scanning heap region
print("\n=== Scan for active menu-handler objects (obj+8 in 0x130000-0x500000 code, near tavern handlers) ===")
for name,m in [('WORK',work),('FROZ',froz)]:
    print(f"--- {name}")
    cnt=0
    for a in range(0x500000,0x600000,4):
        v=u32(m,a)
        if v in (0x2F2490,):  # references to our handler stored as obj+8
            print(f"   handler ptr 0x2F2490 stored at {a:#x}; obj base {a-8:#x} ctx={u32(m,a+4):#x}")
            cnt+=1
        if cnt>10: break
