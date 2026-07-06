import sys
import numpy as np
sys.stdout.reconfigure(encoding='utf-8')

RAW='C:/programmieren/wizardrytranslation/extracted/packdata_raw'
R1251=open(f'{RAW}/1251_type01.raw','rb').read()
PORTRAIT_SRC=R1251[0xA1:0xA1+128*256*4]

HDR=509
def load(p):
    return np.frombuffer(open(p,'rb').read()[HDR:HDR+4*1024*1024],dtype=np.uint8).copy()

p='C:/programmieren/wizardrytranslation/build/recon_portrait3/extract/MissingPortraitAndFuckedDialogue__gs.bin'
vram=load(p)
vb=vram.tobytes()

# The byteoff=0 "match" — verify it's real or coincidence
print("VRAM[0:16]:", vb[:16].hex())
print("PORTRAIT_SRC[0:16]:", PORTRAIT_SRC[:16].hex())
print("equal first 4KB?", vb[:4096]==PORTRAIT_SRC[:4096])
# both probably all-zero at start
print("VRAM first 4KB nonzero:", np.count_nonzero(vram[:4096]))
print("PORTRAIT first 4KB nonzero:", sum(1 for x in PORTRAIT_SRC[:4096] if x))

# Search for a NONZERO distinctive chunk of the portrait payload
# find first 256-byte run in payload with high entropy
off=None
for o in range(0,len(PORTRAIT_SRC)-256,256):
    chunk=PORTRAIT_SRC[o:o+256]
    if sum(1 for x in chunk if x)>200:
        off=o; break
print("distinctive payload chunk at payload-off",off)
if off is not None:
    needle=PORTRAIT_SRC[off:off+256]
    idx=vb.find(needle)
    print("distinctive chunk found in VRAM byteoff:",idx, "dbp(/256):", idx//256 if idx>=0 else "NA")
    # search a few more
    cnt=0; pos=0
    while True:
        i=vb.find(needle,pos)
        if i<0: break
        cnt+=1; pos=i+1
        if cnt<10: print("   occurrence byteoff",i,"dbp",i//256)
    print("total occurrences:",cnt)

# Also: dump the 0x3000 region as a thumbnail-ish stat per row to see if it looks like image
base=0x3000*256
reg=vram[base:base+128*256*4]  # if it were CT32 128x256 linear
print("0x3000 region (as if 128x256 CT32): nonzero", np.count_nonzero(reg),"/",len(reg))
