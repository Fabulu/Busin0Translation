import sys, zipfile, struct
sys.stdout.reconfigure(encoding='utf-8')
def load(p):
    z=zipfile.ZipFile(p)
    for n in z.namelist():
        if 'eeMemory' in n: return z.read(n)
def u32(m,va): return struct.unpack('<I',m[va:va+4])[0]
def u16(m,va): return struct.unpack('<H',m[va:va+2])[0]
work=load(r'C:\programmieren\wizardrytranslation\ramdumps\tavern104.p2s')
froz=load(r'C:\programmieren\wizardrytranslation\ramdumps\fuckinghellman.p2s')

for tag,p in [('work',work),('froz',froz)]:
    mp=u32(p,0x4FEDC0)
    ctx=u32(p,mp+0x0C)
    print(f"=== {tag}: menuobj=0x{mp:08X} ctx(s1)=0x{ctx:08X} ===")

wmp=u32(work,0x4FEDC0); wctx=u32(work,wmp+0x0C)
fmp=u32(froz,0x4FEDC0); fctx=u32(froz,fmp+0x0C)
print(f"\nwork ctx=0x{wctx:08X}  froz ctx=0x{fctx:08X}")
print("\n=== ctx sub-state (offsets read by handler) ===")
offs=[0x00,0x04,0x08,0x0a,0x0c,0x10,0x288,0x28c,0x290,0x294,0x298,0x29a,0x29c,0x2a0,0x2a4]
for o in offs:
    w=u32(work,wctx+o); f=u32(froz,fctx+o)
    d='  <-- DIFF' if w!=f else ''
    print(f"  +0x{o:03X}: work=0x{w:08X} froz=0x{f:08X}{d}")
