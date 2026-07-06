import sys, os, numpy as np
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,'build/recon_v86/gs-vram-atlas')
from gs_atlas import sample_pixels
from PIL import Image
os.makedirs('build/recon_w1/rows', exist_ok=True)

def load_vram(path):
    d=open(path,'rb').read()
    return np.frombuffer(bytearray(d[509:509+4*1024*1024]),dtype=np.uint8).copy()

for name in ['shady4','BarkeepOverflow']:
    vram=load_vram(f'build/recon_tri2/{name}__gs.bin')
    W=512; H=448
    px=sample_pixels(vram, 0, W, 0x00, W, H)  # full FB
    rgb=px[...,:3].astype(np.int32)
    # text is bright glyphs on dark box. Compute per-row brightness in the dialogue box region.
    # First save full upscaled bottom region.
    bottom=px[300:448,:,:]
    Image.fromarray(bottom,'RGBA').convert('RGB').resize((W*2,(448-300)*2),Image.NEAREST).save(f'build/recon_w1/rows/{name}_bottom2x.png')
    # per-row mean brightness across full image
    rowb=rgb.mean(axis=(1,2))
    # Print rows 300..448
    print(f'=== {name} per-row brightness (y: val) for y=300..447 ===')
    for y in range(300,448):
        bar='#'*int(rowb[y]/3)
        print(f'{y:3d} {rowb[y]:6.1f} {bar}')
