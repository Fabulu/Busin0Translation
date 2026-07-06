import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
def rd(p): return open(p,'rb').read()
def u32(d,a): return struct.unpack_from('<I',d,a)[0]
E='C:/programmieren/wizardrytranslation/build/recon_portrait4/extract/'
REF='C:/programmieren/wizardrytranslation/build/recon_portrait2/extract/Firstdialogue__ee.bin'
GP=0x504FF0
for name,p in [('PRESENT',REF),('nshadyman',E+'nshadymanand4linesinsteadof3__ee.bin')]:
    d=rd(p)
    g6234=u32(d,GP-0x6234)  # 0x4FEDBC
    g6230=u32(d,GP-0x6230)  # 0x4FEDC0
    print(f"{name:10}: *(gp-0x6234)=0x{g6234:08X}  *(gp-0x6230)=0x{g6230:08X}")
# descriptor[1] addr
print(f"\ndescriptor[1] = 0x55DF00, +0x06 field at 0x55DF06")
