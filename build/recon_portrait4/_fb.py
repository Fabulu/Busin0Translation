import sys, numpy as np
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image
HDR=509
def vram(p): return np.frombuffer(open(p,'rb').read()[HDR:HDR+4*1024*1024],dtype=np.uint8).copy()
P=sys.argv[1] if len(sys.argv)>1 else 'build/recon_portrait4/extract/ladyknightnoportrait__gs.bin'
v=vram(P); w=v.view(np.uint32)
# Try linear PSMCT32 framebuffers at common fbp word-bases. PS2 fbp in 2048-word pages? fbp*2048 words.
# Common DISPLAY: fbw=10 (640), or 8(512). Scan candidate fbps and render 512x256 to find image.
best=None
for fbp in range(0, 0x100, 1):
    base=fbp*2048
    if base+512*256>len(w): break
    block=w[base:base+512*256].reshape(256,512)
    luma=((block&0xFF)+((block>>8)&0xFF)+((block>>16)&0xFF))//3
    score=(luma>30).sum()
    if best is None or score>best[1]:
        best=(fbp,score)
print("best fbp guess",best)
