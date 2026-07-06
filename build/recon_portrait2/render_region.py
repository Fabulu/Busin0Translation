import sys, struct
import numpy as np
sys.path.insert(0,'build/recon_v86/gs-vram-atlas')
sys.stdout.reconfigure(encoding='utf-8')
import zstandard as zstd, gs_atlas as G
from PIL import Image

def vram_gsdump(path):
    d=open(path,'rb').read()
    if d[:4]==b'\x28\xb5\x2f\xfd': d=zstd.ZstdDecompressor().decompress(d,max_output_size=512*1024*1024)
    if d[:4]==b'\xff\xff\xff\xff' or struct.unpack_from('<I',d,8)[0]==9:
        pass
    hts=struct.unpack_from('<I',d,4)[0]; ds=8+hts
    return np.frombuffer(bytearray(d[ds+425:ds+425+4*1024*1024]),dtype=np.uint8).copy()
def vram_ss(path):
    d=open(path,'rb').read(); return np.frombuffer(bytearray(d[-4*1024*1024:]),dtype=np.uint8).copy()

kind,path,out=sys.argv[1],sys.argv[2],sys.argv[3]
vram = vram_gsdump(path) if kind=='gsdump' else vram_ss(path)
# render dbp=0x3000 as PSMCT32 128x256 (the portrait sprite dims)
img=G.sample_pixels(vram,0x3000,128,0x00,128,256)  # (256,128,4)
Image.fromarray(img[:,:,:3],'RGB').save(out)
print('saved',out)
