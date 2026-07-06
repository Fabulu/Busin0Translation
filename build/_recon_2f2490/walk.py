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
def walk(m,name):
    print(f"--- {name} scheduler list (next=+0x00, handler=+0x08, ctx=+0x0C)")
    obj=u32(m,gp-0x6230)
    seen=set(); a=obj; i=0
    # find list head: maybe gp-0x6230 is current, list root elsewhere. Just walk next from here.
    while a and a not in seen and 0x500000<=a<0x600000 and i<40:
        seen.add(a)
        h=u32(m,a+8); ctx=u32(m,a+0xC)
        print(f"   [{i}] obj={a:#x} handler={h:#010x} ctx={ctx:#010x} next={u32(m,a):#x}")
        a=u32(m,a); i+=1
walk(work,'WORK'); print(); walk(froz,'FROZ')
