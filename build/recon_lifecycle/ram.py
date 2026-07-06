import sys, struct, zipfile
sys.stdout.reconfigure(encoding='utf-8')
def load(p):
    z=zipfile.ZipFile(p)
    for n in z.namelist():
        if 'eeMemory' in n:
            return z.read(n)
    raise SystemExit('no eeMemory')
working=load('C:/programmieren/wizardrytranslation/ramdumps/tavern104.p2s')
frozen =load('C:/programmieren/wizardrytranslation/ramdumps/fuckinghellman.p2s')
print('working len',len(working),'frozen len',len(frozen))
def b(mem,va): return mem[va]
def w32(mem,va): return struct.unpack('<I',mem[va:va+4])[0]
for va,nm in [(0x4FE690,'FLAG690'),(0x4FE6B8,'FLAG6B8'),(0x4FE724,'FLAG724'),(0x4FE6C0,'YIELD6C0')]:
    print(f'{nm} 0x{va:x}: working={b(working,va)} frozen={b(frozen,va)}')
