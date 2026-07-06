import struct, zipfile, sys
sys.stdout.reconfigure(encoding='utf-8')
def load(p):
    z=zipfile.ZipFile(p)
    for n in z.namelist():
        if 'eeMemory' in n: return z.read(n)
for lbl,p in [('WORKING','tavern104.p2s'),('FROZEN','fuckinghellman.p2s')]:
    m=load('C:/programmieren/wizardrytranslation/ramdumps/'+p)
    for nva in [0x578cec, 0x578cd8]:
        b=m[nva:nva+16]
        vals=struct.unpack('<4I',b)
        print(f'{lbl} node 0x{nva:08x}: next=0x{vals[0]:08x} f04=0x{vals[1]:08x} fn=0x{vals[2]:08x} ctx=0x{vals[3]:08x}')
    print('  head 0x578CC4 ->', hex(struct.unpack("<I",m[0x578CC4:0x578CC8])[0]))
