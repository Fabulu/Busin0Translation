import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
def rd(p): return open(p,'rb').read()
EXTRACT='C:/programmieren/wizardrytranslation/build/recon_portrait4/extract/'
REF='C:/programmieren/wizardrytranslation/build/recon_portrait2/extract/Firstdialogue__ee.bin'
dumps={'PRESENT':REF,'nshadyman':EXTRACT+'nshadymanand4linesinsteadof3__ee.bin','nosister':EXTRACT+'nosister__ee.bin','ladyknight':EXTRACT+'ladyknightnoportrait__ee.bin'}
data={n:rd(p) for n,p in dumps.items()}
def u32(d,a): return struct.unpack_from('<I',d,a)[0]
# CG resource slot table ~0x509E00 stride 0x24, 0x509F80 is one entry
print("CG slot region 0x509E00..0x50A000 (stride 0x24 entries), u32[0] each:")
for name,d in data.items():
    print(f"\n  {name}:")
    for base in range(0x509E00,0x50A040,0x24):
        v=u32(d,base)
        if v: print(f"    0x{base:08X}: ptr=0x{v:08X}  +4=0x{u32(d,base+4):08X} +8=0x{u32(d,base+8):08X}")
# specifically 0x509F80
print("\n  0x509F80 (CG ptr) per dump:")
for name,d in data.items():
    print(f"    {name:10}: 0x{u32(d,0x509F80):08X}  prev24=0x{u32(d,0x509F80-0x24):08X}")
