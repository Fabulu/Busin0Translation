import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
def rd(p): return open(p,'rb').read()
EXTRACT='C:/programmieren/wizardrytranslation/build/recon_portrait4/extract/'
REF='C:/programmieren/wizardrytranslation/build/recon_portrait2/extract/Firstdialogue__ee.bin'
dumps={'PRESENT':REF,'nshadyman':EXTRACT+'nshadymanand4linesinsteadof3__ee.bin'}
data={n:rd(p) for n,p in dumps.items()}
DBASE=0x55DD20; STRIDE=0x1E0
# how many descriptors? scan 0x542748 slot table holds idx; max idx 14 from init. Let's dump 30 descriptors' first 8 bytes
print("descriptor[i] first 16 bytes (PRESENT | nshadyman):")
for i in range(20):
    b=DBASE+i*STRIDE
    p=data['PRESENT'][b:b+16].hex()
    a=data['nshadyman'][b:b+16].hex()
    mark='  <-- DIFFERS' if p!=a else ''
    nz='' if any(data['PRESENT'][b:b+STRIDE]) else ' (PRESENT empty)'
    print(f"  [{i:2}] P {p}\n       N {a}{mark}{nz}")
