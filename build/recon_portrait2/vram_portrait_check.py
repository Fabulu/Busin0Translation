import sys, struct
import numpy as np
sys.stdout.reconfigure(encoding='utf-8')
import zstandard as zstd

def vram_savestate(path):
    d=open(path,'rb').read(); return np.frombuffer(bytearray(d[-4*1024*1024:]),dtype=np.uint8).copy()
def vram_gsdump(path):
    d=open(path,'rb').read()
    if d[:4]==b'\x28\xb5\x2f\xfd': d=zstd.ZstdDecompressor().decompress(d,max_output_size=512*1024*1024)
    hts=struct.unpack_from('<I',d,4)[0]; ds=8+hts
    return np.frombuffer(bytearray(d[ds+425:ds+425+4*1024*1024]),dtype=np.uint8).copy()

def region_stats(vram, dbp):
    base=dbp*256
    # portrait region: dbp 0x3000..0x4000 region (the figure column). Look at 0x3000..0x3400 = 0x40000 bytes
    reg=vram[base:base+0x40000]
    nz=int(np.count_nonzero(reg))
    return nz, len(reg), nz/len(reg)

if __name__=='__main__':
    kind,path=sys.argv[1],sys.argv[2]
    vram = vram_gsdump(path) if kind=='gsdump' else vram_savestate(path)
    for dbp in (0x3000,0x3400,0x3800):
        nz,tot,frac=region_stats(vram,dbp)
        print(f'{path.split("/")[-1]} dbp={hex(dbp)} nonzero={nz}/{tot} frac={frac:.3f}')
