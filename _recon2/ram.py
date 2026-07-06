import sys, zipfile, struct
sys.stdout.reconfigure(encoding='utf-8')

def load(p):
    z=zipfile.ZipFile(p)
    for n in z.namelist():
        if 'eeMemory' in n:
            return z.read(n)
    raise SystemExit('no eeMemory in '+p)

def u32(m,va): return struct.unpack('<I',m[va:va+4])[0]
def u16(m,va): return struct.unpack('<H',m[va:va+2])[0]
def u8(m,va): return m[va]

work=load(r'C:\programmieren\wizardrytranslation\ramdumps\tavern104.p2s')
froz=load(r'C:\programmieren\wizardrytranslation\ramdumps\fuckinghellman.p2s')
print('work len',len(work),'froz len',len(froz))

addrs=[
 ('input_mask 0x4FE6A4',0x4FE6A4,'u32'),
 ('gateA 0x4FE6AC',0x4FE6AC,'u8'),
 ('gateB 0x4FE68C',0x4FE68C,'u8'),
 ('flag 0x4FE6B4',0x4FE6B4,'u8'),
 ('0x4FE690',0x4FE690,'u8'),
 ('menuobj_ptr 0x4FEDC0',0x4FEDC0,'u32'),
 ('inpedge_ptr 0x4FEBB8',0x4FEBB8,'u32'),
 ('global 0x564EDC',0x564EDC,'u32'),
 ('0x564EE4',0x564EE4,'u16'),
 ('0x564ED8',0x564ED8,'u32'),
]
for name,va,t in addrs:
    if t=='u32': w,f=u32(work,va),u32(froz,va)
    elif t=='u16': w,f=u16(work,va),u16(froz,va)
    else: w,f=u8(work,va),u8(froz,va)
    flag='  <-- DIFF' if w!=f else ''
    print(f"{name:24s} work=0x{w:08X} froz=0x{f:08X}{flag}")
