import sys, os, numpy as np
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,'build/recon_v86/gs-vram-atlas')
from gs_atlas import sample_pixels
from PIL import Image
os.makedirs('build/recon_w1/fb2', exist_ok=True)

def load_vram(path):
    d=open(path,'rb').read()
    return np.frombuffer(bytearray(d[509:509+4*1024*1024]),dtype=np.uint8).copy()

name='shady4'
vram=load_vram(f'build/recon_tri2/{name}__gs.bin')
H=448
for W in [512,640]:
    for fbp_page in [0]:
        tbp_blocks=fbp_page*8
        # render with bw_px=W
        px=sample_pixels(vram, tbp_blocks, W, 0x00, W, H)
        Image.fromarray(px,'RGBA').convert('RGB').save(f'build/recon_w1/fb2/{name}_W{W}.png')
        print(f'W={W} done mean={px[...,:3].mean():.1f}')
