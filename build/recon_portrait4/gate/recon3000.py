import sys, struct
import numpy as np
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,'C:/programmieren/wizardrytranslation/tools')
from psmt4_deswizzle import _psmct32_word_addr
RAW='C:/programmieren/wizardrytranslation/extracted/packdata_raw'
R1251=open(f'{RAW}/1251_type01.raw','rb').read()
PORTRAIT_SRC=np.frombuffer(R1251[0xA1:0xA1+128*256*4],dtype=np.uint8).reshape(256,128,4)
HDR=509
E='C:/programmieren/wizardrytranslation/build/recon_portrait4/extract'
E2='C:/programmieren/wizardrytranslation/build/recon_portrait2/extract'
GS={
 'PRESENT':   f'{E2}/Firstdialogue__gs.bin',
 'nshadyman': f'{E}/nshadymanand4linesinsteadof3__gs.bin',
 'nosister':  f'{E}/nosister__gs.bin',
 'ladyknight':f'{E}/ladyknightnoportrait__gs.bin',
}
def vram(p): return np.frombuffer(open(p,'rb').read()[HDR:HDR+4*1024*1024],dtype=np.uint8).copy()
def recon(words,dbp,W=128,H=256,bw=128):
    wb=dbp*64; img=np.zeros((H,W,4),np.uint8)
    for y in range(H):
        for x in range(W):
            wv=words[wb+_psmct32_word_addr(x,y,bw)]
            img[y,x,0]=wv&0xFF; img[y,x,1]=(wv>>8)&0xFF; img[y,x,2]=(wv>>16)&0xFF; img[y,x,3]=(wv>>24)&0xFF
    return img
def luma(a): return a[...,:3].astype(np.float32).mean(2)
ls=luma(PORTRAIT_SRC)
for k,p in GS.items():
    v=vram(p); words=v.view(np.uint32)
    img=recon(words,0x3000); lv=luma(img)
    mask=(ls>4)|(lv>4)
    cs=ls[mask]-ls[mask].mean(); cv=lv[mask]-lv[mask].mean()
    den=np.sqrt((cs**2).sum())*np.sqrt((cv**2).sum())
    corr=(cs*cv).sum()/den if den>0 else 0
    print(f"{k:11s}: dbp0x3000 src_nz={int((ls>4).sum())} vram_nz={int((lv>4).sum())} corr={corr:.3f} mean_luma={lv.mean():.1f}")
    try:
        from PIL import Image
        Image.fromarray(img[...,:3],'RGB').save(f'C:/programmieren/wizardrytranslation/build/recon_portrait4/gate/vram3000_{k}.png')
    except Exception as e: print("  PIL",e)
