import sys, numpy as np
sys.stdout.reconfigure(encoding='utf-8')
HDR=509
def vram(p):
    return np.frombuffer(open(p,'rb').read()[HDR:HDR+4*1024*1024],dtype=np.uint8).copy()

# Try to locate framebuffer. PS2 typical: 512x448 PSMCT32 at some dbp.
# Just dump candidate framebuffers at common base 0 and scan for high-luma horizontal text band.
P='build/recon_portrait4/extract/nshadymanand4linesinsteadof3__gs.bin'
v=vram(P)
words=v.view(np.uint32)
print("total words", len(words))
# A 512-wide CT32 linear framebuffer: try fbp candidates. Common: 0 (0x000000), or context. 
# Let's just interpret first 512*512 words as linear and look at it.
for fbp in [0x0, 0x000, 0x00000]:
    pass
# Instead: render whole VRAM as 1024-wide grayscale tiles to find the framebuffer visually
