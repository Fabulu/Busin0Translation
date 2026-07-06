import sys, zipfile, struct
sys.stdout.reconfigure(encoding='utf-8')
def load(p):
    z=zipfile.ZipFile(p)
    for n in z.namelist():
        if 'eeMemory' in n: return z.read(n)
def u8(m,va): return m[va]
def u16(m,va): return struct.unpack('<H',m[va:va+2])[0]
def u32(m,va): return struct.unpack('<I',m[va:va+4])[0]
work=load(r'C:\programmieren\wizardrytranslation\ramdumps\tavern104.p2s')
froz=load(r'C:\programmieren\wizardrytranslation\ramdumps\fuckinghellman.p2s')
gp=0x504FF0
items=[
 ('input_lock 0x23c740 [gp-0x6d68]',-0x6d68,'u8'),
 ('[gp-0x6d64]',-0x6d64,'u8'),
 ('[gp-0x6d60]',-0x6d60,'u8'),
 ('rawpad 0x492cd0 [gp-0x6284]',-0x6284,'u32'),
 ('navrepeat ctr [gp-0x6980]',-0x6980,'u16'),
 ('action_mask [gp-0x694c]',-0x694c,'u32'),
 ('-0x6930 (set by bit2/4 fns)',-0x6930,'u8'),
]
for name,off,t in items:
    va=gp+off
    if t=='u8': w,f=u8(work,va),u8(froz,va)
    elif t=='u16': w,f=u16(work,va),u16(froz,va)
    else: w,f=u32(work,va),u32(froz,va)
    d='  <-- DIFF' if w!=f else ''
    print(f"{name:34s} 0x{va:08X} work=0x{w:X} froz=0x{f:X}{d}")
