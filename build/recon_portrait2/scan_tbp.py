import sys, struct
import numpy as np
sys.path.insert(0, 'build/recon_v86/gs-vram-atlas')
sys.stdout.reconfigure(encoding='utf-8')
import zstandard as zstd
import gs_atlas as G
RAW = open('extracted/packdata_raw/1251_type01.raw','rb').read()
PX = np.frombuffer(RAW[0xA1:0xA1+0x20000], dtype=np.uint8)
SIG = PX != 0

def vram_raw(path):
    d=open(path,'rb').read()
    if d[:4]==b'\x28\xb5\x2f\xfd': d=zstd.ZstdDecompressor().decompress(d,max_output_size=512*1024*1024)
    hts=struct.unpack_from('<I',d,4)[0]; ds=8+hts
    return np.frombuffer(bytearray(d[ds+425:ds+425+4*1024*1024]),dtype=np.uint8).copy()

vram=vram_raw(sys.argv[1])
best=[]
for bw in (128,256,512):
    for tbp in range(0x0, 0x3800, 0x20):
        idx=G.sample_pixels(vram,tbp,bw,0x13,256,512)
        lin=idx.reshape(-1)[:len(PX)]
        sigeq=np.count_nonzero((lin==PX)&SIG)
        best.append((sigeq, tbp, bw))
best.sort(reverse=True)
for sigeq,tbp,bw in best[:12]:
    print(f'tbp={hex(tbp)} bw={bw} sigmatch={sigeq/np.count_nonzero(SIG):.4f} ({sigeq})')
