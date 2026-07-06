import sys
import numpy as np
sys.stdout.reconfigure(encoding='utf-8')
HDR=509
E='C:/programmieren/wizardrytranslation/build/recon_portrait4/extract'
E2='C:/programmieren/wizardrytranslation/build/recon_portrait2/extract'
GS={
 'PRESENT':   f'{E2}/Firstdialogue__gs.bin',
 'nshadyman': f'{E}/nshadymanand4linesinsteadof3__gs.bin',
 'nosister':  f'{E}/nosister__gs.bin',
 'ladyknight':f'{E}/ladyknightnoportrait__gs.bin',
}
# Try to render the final framebuffer. Common FB base for this game ~ 0 or 0x1000 in PSMCT32 640x... 
# Just scan for a 640x448-ish bright region. Simpler: render dbp ranges as linear PSMCT32 512-wide and save thumbnails.
from PIL import Image
def vram(p): return np.frombuffer(open(p,'rb').read()[HDR:HDR+4*1024*1024],dtype=np.uint8).copy()
for k,p in GS.items():
    v=vram(p)
    w=v.view(np.uint32)
    # render first 640*512 words as linear RGBA at 640 wide (framebuffer guess at word 0)
    for fbword,tag in ((0,'fb0'),):
        block=w[fbword:fbword+640*512]
        img=np.zeros((512,640,3),np.uint8)
        rgba=block.view(np.uint32)
        img[...,0]=(rgba&0xFF).reshape(512,640)
        img[...,1]=((rgba>>8)&0xFF).reshape(512,640)
        img[...,2]=((rgba>>16)&0xFF).reshape(512,640)
        Image.fromarray(img,'RGB').save(f'C:/programmieren/wizardrytranslation/build/recon_portrait4/gate/{tag}_{k}.png')
    print(f"{k}: saved fb0")
