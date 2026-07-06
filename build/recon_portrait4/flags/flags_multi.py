import sys, struct
sys.stdout.reconfigure(encoding='utf-8')

E='C:/programmieren/wizardrytranslation/build/recon_portrait4/extract'
E3='C:/programmieren/wizardrytranslation/build/recon_portrait3/extract'
E2='C:/programmieren/wizardrytranslation/build/recon_portrait2/extract'
DUMPS={
 'PRESENT(Firstdialogue)': f'{E2}/Firstdialogue__ee.bin',
 'nshadyman':              f'{E}/nshadymanand4linesinsteadof3__ee.bin',
 'nosister':               f'{E}/nosister__ee.bin',
 'ladyknight':             f'{E}/ladyknightnoportrait__ee.bin',
}
TABLES={'0x565090(param2)':0x565090,'0x5650D0(param1)':0x5650D0,'0x565110(param0)':0x565110}
CGSLOT=0x509F80
def load(p): return open(p,'rb').read()
bufs={k:load(v) for k,v in DUMPS.items()}

def bits(buf,base,words=14):
    out=[]
    for w in range(words):
        v=struct.unpack_from('<I',buf,base+w*4)[0]
        for b in range(32):
            if v&(1<<b): out.append(w*32+b)
    return out

for name,base in TABLES.items():
    print(f"=== {name} set-bit indices ===")
    for k,buf in bufs.items():
        print(f"  {k:24s}: {bits(buf,base)}")
    print()

print("=== CG slot ptr 0x509F80 ===")
for k,buf in bufs.items():
    print(f"  {k:24s}: 0x{struct.unpack_from('<I',buf,CGSLOT)[0]:08X}")
print()
print("=== CG slot region 0x509F80..+0x40 ===")
for k,buf in bufs.items():
    vals=[f"{struct.unpack_from('<I',buf,CGSLOT+i*4)[0]:08X}" for i in range(16)]
    print(f"  {k:24s}: {' '.join(vals)}")
