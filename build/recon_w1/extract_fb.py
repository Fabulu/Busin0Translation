import struct, sys, os, numpy as np
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,'build/recon_v86/gs-vram-atlas')
from gs_atlas import sample_pixels
from PIL import Image

os.makedirs('build/recon_w1/fb', exist_ok=True)

def load_vram(path):
    d=open(path,'rb').read()
    vram=np.frombuffer(bytearray(d[509:509+4*1024*1024]),dtype=np.uint8).copy()
    return vram

W,H=640,448
for name in ['shady4','BarkeepOverflow']:
    vram=load_vram(f'build/recon_tri2/{name}__gs.bin')
    for fbp_page in [0,0x0A,0x14,0x1E,0x28,0x32,0x3C]:
        tbp_blocks=fbp_page*8
        px=sample_pixels(vram, tbp_blocks, W, 0x00, W, H)
        mean=px[...,:3].mean()
        Image.fromarray(px,'RGBA').convert('RGB').save(f'build/recon_w1/fb/{name}_fbp{fbp_page}.png')
        print(f'{name} fbp_page={fbp_page} tbp_blocks={tbp_blocks} mean={mean:.1f}')
