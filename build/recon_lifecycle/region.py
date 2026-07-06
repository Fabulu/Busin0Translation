import struct, zipfile, sys
sys.stdout.reconfigure(encoding='utf-8')
def load(p):
    z=zipfile.ZipFile(p)
    for n in z.namelist():
        if 'eeMemory' in n: return z.read(n)
def w32(m,va): return struct.unpack('<I',m[va:va+4])[0]
for lbl,p in [('WORKING','tavern104.p2s'),('FROZEN','fuckinghellman.p2s')]:
    m=load('C:/programmieren/wizardrytranslation/ramdumps/'+p)
    print(f'\n===== {lbl} =====  head[0x578CC4]=0x{w32(m,0x578CC4):08x}  curScreen[0x4FE9C0]=0x{w32(m,0x504FF0-25136):08x}  taskcount[0x4FE9C8 lh -25148]')
    print('  node-dump 0x578c80..0x578e10 (each 16B: next,+4,fn,ctx):')
    for va in range(0x578c80,0x578e10,16):
        n,f4,fn,cx=struct.unpack('<4I',m[va:va+16])
        mark=' <== fn=2F2490 HUB' if fn==0x2F2490 else (' <-- 3A2440' if fn==0x3A2440 else '')
        print(f'   0x{va:08x}: next=0x{n:08x} +4=0x{f4:08x} fn=0x{fn:08x} ctx=0x{cx:08x}{mark}')
