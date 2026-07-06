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
# Byte at 0x55D8B0 (P=2b N=32) - dump region
print("=== 0x55D8A0..0x55D8C0 ===")
for k,buf in bufs.items():
    print(f"  {k:11s}: {buf[0x55D8A0:0x55D8C0].hex()}")
# The descriptor array 0x55E5A0: dump desc[0] FULL (480 bytes -> first 64 words) for present vs nshady,
# to find any draw-active field difference
print("\n=== desc[0] @0x55E5A0 first 32 words PRESENT vs nshadyman ===")
for off in range(0,128,4):
    a=0x55E5A0+off
    pv=struct.unpack_from('<I',bufs['PRESENT'],a)[0]
    nv=struct.unpack_from('<I',bufs['nshadyman'],a)[0]
    flag='  <-- DIFF' if pv!=nv else ''
    print(f"   +0x{off:03X}(0x{a:08X}): P={pv:08X} N={nv:08X}{flag}")
