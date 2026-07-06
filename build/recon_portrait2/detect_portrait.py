import sys, struct, os
import numpy as np
sys.path.insert(0, 'build/recon_v86/gs-vram-atlas')
sys.stdout.reconfigure(encoding='utf-8')
import zstandard as zstd
import gs_atlas as G

RAW = open('extracted/packdata_raw/1251_type01.raw','rb').read()
PX = np.frombuffer(RAW[0xA1:0xA1+0x20000], dtype=np.uint8)  # linear PSMT8 256x512

def vram_from_savestate_gs(path):
    d = open(path,'rb').read()
    # last 4MB is VRAM
    return np.frombuffer(bytearray(d[-4*1024*1024:]), dtype=np.uint8).copy()

def vram_from_raw_gsdump(path):
    d = open(path,'rb').read()
    if d[:4]==b'\x28\xb5\x2f\xfd':
        d = zstd.ZstdDecompressor().decompress(d, max_output_size=512*1024*1024)
    hts = struct.unpack_from('<I', d, 4)[0]
    ds = 8 + hts
    return np.frombuffer(bytearray(d[ds+425:ds+425+4*1024*1024]), dtype=np.uint8).copy()

def score_at(vram, tbp, bw_px=256, w=256, h=512):
    # deswizzle PSMT8 region, linearize row-major, compare to PX
    idx = G.sample_pixels(vram, tbp, bw_px, 0x13, w, h)  # (h,w) uint8
    lin = idx.reshape(-1).astype(np.uint8)
    n = min(len(lin), len(PX))
    a = lin[:n]; b = PX[:n]
    eq = np.count_nonzero(a==b)
    # also ignore-zeros score (signal pixels)
    sig = b != 0
    sigeq = np.count_nonzero((a==b) & sig)
    sign = np.count_nonzero(sig)
    return eq/n, (sigeq/sign if sign else 0.0), int(np.count_nonzero(idx))

if __name__=='__main__':
    kind, path = sys.argv[1], sys.argv[2]
    tbp = int(sys.argv[3],0) if len(sys.argv)>3 else 0x3000
    vram = vram_from_raw_gsdump(path) if kind=='gsdump' else vram_from_savestate_gs(path)
    full, sigm, nz = score_at(vram, tbp)
    print(f'{os.path.basename(path)} tbp={hex(tbp)} fullmatch={full:.3f} sigmatch={sigm:.3f} nonzero_idx={nz}')
