import sys, hashlib
import numpy as np
sys.stdout.reconfigure(encoding='utf-8')
RAW='C:/programmieren/wizardrytranslation/extracted/packdata_raw'
R1251=open(f'{RAW}/1251_type01.raw','rb').read()
PORTRAIT_SRC=R1251[0xA1:0xA1+128*256*4]
CLUT_SRC=R1251[0x200D0:0x200D0+16*16*4]
HDR=509
E='C:/programmieren/wizardrytranslation/build/recon_portrait4/extract'
E2='C:/programmieren/wizardrytranslation/build/recon_portrait2/extract'
GS={
 'PRESENT':   f'{E2}/Firstdialogue__gs.bin',
 'nshadyman': f'{E}/nshadymanand4linesinsteadof3__gs.bin',
 'nosister':  f'{E}/nosister__gs.bin',
 'ladyknight':f'{E}/ladyknightnoportrait__gs.bin',
}
import os
def vram(p):
    if not os.path.exists(p): return None
    return np.frombuffer(open(p,'rb').read()[HDR:HDR+4*1024*1024],dtype=np.uint8).copy()
for k,p in GS.items():
    v=vram(p)
    if v is None: print(f"{k}: no gs"); continue
    print(f"==== {k} ====")
    for dbp in (0x3000,0x3200):
        base=dbp*256
        region=v[base:base+256*512]
        nz=int(np.count_nonzero(region))
        h=hashlib.md5(region[:0x8000].tobytes()).hexdigest()[:10]
        print(f"   dbp=0x{dbp:04X} nonzero={nz}/{len(region)} md5={h}")
    idx=v.tobytes().find(PORTRAIT_SRC[:4096])
    print(f"   R1251 portrait payload(4KB) in VRAM at byteoff: {idx} (dbp={idx//256 if idx>=0 else 'NA'})")
    cidx=v.tobytes().find(CLUT_SRC[:256])
    print(f"   R1251 CLUT(256B) in VRAM at byteoff: {cidx} (dbp={cidx//256 if cidx>=0 else 'NA'})")
