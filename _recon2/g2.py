import sys, zipfile, struct
sys.stdout.reconfigure(encoding='utf-8')
def load(p):
    z=zipfile.ZipFile(p)
    for n in z.namelist():
        if 'eeMemory' in n: return z.read(n)
def u8(m,va): return m[va]
def u32(m,va): return struct.unpack('<I',m[va:va+4])[0]
work=load(r'C:\programmieren\wizardrytranslation\ramdumps\tavern104.p2s')
froz=load(r'C:\programmieren\wizardrytranslation\ramdumps\fuckinghellman.p2s')
gp=0x504FF0
# 0x131d20 busy gate = [gp-0x7334]
for name,off,t in [('busy 0x131d20 [gp-0x7334]',-0x7334,'u8'),
                   ('[gp-0x7328]',-0x7328,'u8'),
                   ('[gp-0x732c]',-0x732c,'u8'),
                   ('[gp-0x7330]',-0x7330,'u8'),
                   ('[gp-0x731c]',-0x731c,'u8')]:
    va=gp+off
    w=u8(work,va); f=u8(froz,va)
    d='  <-- DIFF' if w!=f else ''
    print(f"{name:28s} 0x{va:08X} work=0x{w:02X} froz=0x{f:02X}{d}")
