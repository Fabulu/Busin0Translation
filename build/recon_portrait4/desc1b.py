import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
def rd(p): return open(p,'rb').read()
EXTRACT='C:/programmieren/wizardrytranslation/build/recon_portrait4/extract/'
REF='C:/programmieren/wizardrytranslation/build/recon_portrait2/extract/Firstdialogue__ee.bin'
dumps={'PRESENT':REF,'nshadyman':EXTRACT+'nshadymanand4linesinsteadof3__ee.bin','nosister':EXTRACT+'nosister__ee.bin','ladyknight':EXTRACT+'ladyknightnoportrait__ee.bin','guy':EXTRACT+'Ithinkguyshouldshowuphere__ee.bin','request':EXTRACT+'request__ee.bin'}
data={n:rd(p) for n,p in dumps.items()}
DBASE=0x55DD20; STRIDE=0x1E0
def u16(d,a): return struct.unpack_from('<H',d,a)[0]
print("descriptor[1] @0x55DF00 first 0x60 bytes + key fields:")
for name,d in data.items():
    b=DBASE+STRIDE
    nonzero=any(d[b:b+STRIDE])
    print(f"\n  {name:10} active={nonzero}")
    print(f"     +0x00: {d[b:b+0x20].hex()}")
    print(f"     +0x06(u16)=0x{u16(d,b+6):04X}  +0x10(u16)=0x{u16(d,b+0x10):04X} +0x12=0x{u16(d,b+0x12):04X} +0x14=0x{u16(d,b+0x14):04X}")
# also count how many descriptors are non-zero in each
print("\n  count of non-empty descriptors (0..30):")
for name,d in data.items():
    cnt=[i for i in range(30) if any(d[DBASE+i*STRIDE:DBASE+i*STRIDE+STRIDE])]
    print(f"    {name:10}: {cnt}")
