import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
def rd(p): return open(p,'rb').read()
EXTRACT='C:/programmieren/wizardrytranslation/build/recon_portrait4/extract/'
REF='C:/programmieren/wizardrytranslation/build/recon_portrait2/extract/Firstdialogue__ee.bin'
dumps={'PRESENT':REF,'nshadyman':EXTRACT+'nshadymanand4linesinsteadof3__ee.bin','request':EXTRACT+'request__ee.bin'}
data={n:rd(p) for n,p in dumps.items()}
DBASE=0x55DD20; STRIDE=0x1E0
for idx in [0,1]:
    b=DBASE+idx*STRIDE
    print(f"\n=== descriptor[{idx}] @0x{b:08X} full 0x1E0 ===")
    for name,d in data.items():
        print(f"  {name}:")
        for r in range(0,0xE0,16):
            print(f"    +0x{r:03X}: {d[b+r:b+r+16].hex()}")
