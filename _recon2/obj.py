import sys, zipfile, struct
sys.stdout.reconfigure(encoding='utf-8')
def load(p):
    z=zipfile.ZipFile(p)
    for n in z.namelist():
        if 'eeMemory' in n: return z.read(n)
def u32(m,va): return struct.unpack('<I',m[va:va+4])[0]
def u16(m,va): return struct.unpack('<H',m[va:va+2])[0]
def s16(m,va): return struct.unpack('<h',m[va:va+2])[0]
work=load(r'C:\programmieren\wizardrytranslation\ramdumps\tavern104.p2s')
froz=load(r'C:\programmieren\wizardrytranslation\ramdumps\fuckinghellman.p2s')

# handler arg object: frozen a0=0x1379D0. Dump key sub-state offsets used in handler:
# +0x290 (u32 flags), +0x294, +0x298, +0x29a (s16), +0x29c (u16 wait), +0x2A4 (state)
obj=0x001379D0
print("=== object @0x1379D0 sub-state (handler s1) ===")
for o in [0x00,0x04,0x08,0x0a,0x288,0x28c,0x290,0x294,0x298,0x29a,0x29c,0x2a0,0x2a4]:
    w=u32(work,obj+o); f=u32(froz,obj+o)
    d='  <-- DIFF' if w!=f else ''
    print(f"  +0x{o:03X}: work=0x{w:08X} froz=0x{f:08X}{d}")

print()
print("=== menu objects ===")
for tag,p in [('work',work),('froz',froz)]:
    mp=u32(p,0x4FEDC0)
    print(f"{tag} menuobj_ptr=0x{mp:08X}")
    for o in [0x00,0x04,0x08,0x0c,0x2a4]:
        print(f"   +0x{o:03X}=0x{u32(p,mp+o):08X}")
