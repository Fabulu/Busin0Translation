import sys, struct
import numpy as np
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,'C:/programmieren/wizardrytranslation/tools')
from psmt4_deswizzle import _psmct32_word_addr

RAW='C:/programmieren/wizardrytranslation/extracted/packdata_raw'
R1251=open(f'{RAW}/1251_type01.raw','rb').read()
PORTRAIT_SRC=np.frombuffer(R1251[0xA1:0xA1+128*256*4],dtype=np.uint8).reshape(256,128,4)  # linear rows

HDR=509
def vram(p):
    return np.frombuffer(open(p,'rb').read()[HDR:HDR+4*1024*1024],dtype=np.uint8).copy()

P='C:/programmieren/wizardrytranslation/build/recon_portrait3/extract/MissingPortraitAndFuckedDialogue__gs.bin'
v=vram(P)
words=v.view(np.uint32)  # 1M words

dbp=0x3000
# VRAM word index base: dbp is in 256-byte block units => byte base = dbp*256 => word base = dbp*64
wordbase = dbp*64
W,H=128,256
bw=128
img=np.zeros((H,W,4),dtype=np.uint8)
for y in range(H):
    for x in range(W):
        wa = _psmct32_word_addr(x,y,bw)
        wv = words[wordbase+wa]
        img[y,x,0]= wv & 0xFF
        img[y,x,1]= (wv>>8)&0xFF
        img[y,x,2]= (wv>>16)&0xFF
        img[y,x,3]= (wv>>24)&0xFF

# Correlate alpha/luma vs source
def luma(a): return a[...,:3].astype(np.float32).mean(axis=2)
ls=luma(PORTRAIT_SRC); lv=luma(img)
# Pearson on nonzero
mask=(ls>4)|(lv>4)
if mask.sum()>100:
    cs=ls[mask]-ls[mask].mean(); cv=lv[mask]-lv[mask].mean()
    denom=(np.sqrt((cs**2).sum())*np.sqrt((cv**2).sum()))
    corr=(cs*cv).sum()/denom if denom>0 else 0
else:
    corr=float('nan')
print(f"dbp=0x{dbp:04X} reconstructed 128x256 CT32:")
print(f"  src nonzero px={int((ls>4).sum())}  vram nonzero px={int((lv>4).sum())}  corr(luma)={corr:.3f}")

# Save PNGs for visual
try:
    from PIL import Image
    Image.fromarray(img[...,:3],'RGB').save('C:/programmieren/wizardrytranslation/build/recon_portrait3/gs/vram_3000.png')
    Image.fromarray(PORTRAIT_SRC[...,:3].copy(),'RGB').save('C:/programmieren/wizardrytranslation/build/recon_portrait3/gs/r1251_src.png')
    print("  saved vram_3000.png and r1251_src.png")
except Exception as e:
    print("  PIL err",e)

# Also reconstruct what's actually at 0x3000 if it's a 512x256 region (font?) - just report mean
print(f"  vram region mean luma={lv.mean():.1f}")
