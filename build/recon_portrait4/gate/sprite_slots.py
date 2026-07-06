import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
E='C:/programmieren/wizardrytranslation/build/recon_portrait4/extract'
E2='C:/programmieren/wizardrytranslation/build/recon_portrait2/extract'
DUMPS={
 'PRESENT':   f'{E2}/Firstdialogue__ee.bin',
 'nshadyman': f'{E}/nshadymanand4linesinsteadof3__ee.bin',
 'nosister':  f'{E}/nosister__ee.bin',
 'ladyknight':f'{E}/ladyknightnoportrait__ee.bin',
}
def load(p): return open(p,'rb').read()
bufs={k:load(v) for k,v in DUMPS.items()}

SLOTTBL=0x542748   # 6-entry slot alloc table
DESC=0x55E5A0      # descriptor array, stride 480
print("=== Sprite slot table 0x542748 (6 entries x ? ) - dump 6*8 u32 ===")
for k,buf in bufs.items():
    vals=[f"{struct.unpack_from('<I',buf,SLOTTBL+i*4)[0]:08X}" for i in range(12)]
    print(f"  {k:11s}: {' '.join(vals)}")
print()
print("=== Descriptor array 0x55E5A0 (stride 480=0x1E0), first 6 descriptors, first 0x20 each ===")
for k,buf in bufs.items():
    print(f"  --- {k} ---")
    for d in range(6):
        base=DESC+d*480
        head=struct.unpack_from('<8I',buf,base)
        print(f"    desc[{d}]@0x{base:08X}: "+' '.join(f"{x:08X}" for x in head))
