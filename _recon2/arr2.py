import sys, zipfile, struct
sys.stdout.reconfigure(encoding='utf-8')
def load(p):
    z=zipfile.ZipFile(p)
    for n in z.namelist():
        if 'eeMemory' in n: return z.read(n)
def u32(m,va): return struct.unpack('<I',m[va:va+4])[0]
work=load(r'C:\programmieren\wizardrytranslation\ramdumps\tavern104.p2s')
froz=load(r'C:\programmieren\wizardrytranslation\ramdumps\fuckinghellman.p2s')

# Records have +8=handler,+C=ctx. Walk via 'next' field (+0)? In work rec0x578CB0 +0=0x578CD8.
def walk(p, tag):
    cur=u32(p,0x4FEDC0)
    print(f"=== {tag}: active=0x{cur:08X} ; walk via +0x00 (next) ===")
    seen=set()
    for i in range(12):
        if cur in seen or cur<0x100000 or cur>0x2000000: break
        seen.add(cur)
        nxt=u32(p,cur+0); hdl=u32(p,cur+8); ctx=u32(p,cur+0xC)
        f290=u32(p,ctx+0x290) if 0x100000<ctx<0x2000000 else -1
        print(f"  [{i}] obj=0x{cur:08X} hdl=0x{hdl:08X} ctx=0x{ctx:08X} ctx+0x290={f290:#x}")
        cur=nxt
walk(work,'work'); print(); walk(froz,'froz')
