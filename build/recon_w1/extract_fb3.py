import sys, os, numpy as np
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image
os.makedirs('build/recon_w1/fb3', exist_ok=True)

def load_vram(path):
    d=open(path,'rb').read()
    return np.frombuffer(bytearray(d[509:509+4*1024*1024]),dtype=np.uint8).copy()

name='shady4'
vram=load_vram(f'build/recon_tri2/{name}__gs.bin')
# Treat as fully linear RGBA at offset 0, width 512 and 640
for W in [512,640]:
    H=448
    need=W*H*4
    arr=vram[:need].reshape(H,W,4)
    Image.fromarray(arr,'RGBA').convert('RGB').save(f'build/recon_w1/fb3/{name}_linear_W{W}.png')
    print('linear',W,'mean',arr[...,:3].mean())
