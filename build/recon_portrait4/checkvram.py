import sys, struct
import numpy as np
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,'C:/programmieren/wizardrytranslation/tools')
from psmt4_deswizzle import _psmct32_word_addr
RAW='C:/programmieren/wizardrytranslation/extracted/packdata_raw'
R1251=open(f'{RAW}/1251_type01.raw','rb').read()
PORT=np.frombuffer(R1251[0xA1:0xA1+128*256*4],dtype=np.uint8).reshape(256,128,4)
HDR=509
def vram(p): return np.frombuffer(open(p,'rb').read()[HDR:HDR+4*1024*1024],dtype=np.uint8).copy()
def recon(p,dbp=0x3000,W=128,H=256,bw=128):
    v=vram(p); words=v.view(np.uint32); wb=dbp*64
    img=np.zeros((H,W,4),dtype=np.uint8)
    for y in range(H):
        for x in range(W):
            wv=words[wb+_psmct32_word_addr(x,y,bw)]
            img[y,x,0]=wv&0xFF; img[y,x,1]=(wv>>8)&0xFF; img[y,x,2]=(wv>>16)&0xFF; img[y,x,3]=(wv>>24)&0xFF
    return img
E='C:/programmieren/wizardrytranslation/build/recon_portrait4/extract/'
for name,p in [('nshadyman',E+'nshadymanand4linesinsteadof3__gs.bin'),('nosister',E+'nosister__gs.bin'),('ladyknight',E+'ladyknightnoportrait__gs.bin')]:
    img=recon(p)
    # how much matches R1251 portrait?
    match=np.mean(img[:,:,:3]==PORT[:,:,:3])
    nz=np.count_nonzero(img[:,:,:3])
    print(f"{name:12}: dbp=0x3000 vs R1251 match={match*100:.1f}% nonzero_px_bytes={nz}")
