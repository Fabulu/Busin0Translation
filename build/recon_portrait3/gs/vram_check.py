import sys, hashlib
import numpy as np
sys.stdout.reconfigure(encoding='utf-8')

RAW = 'C:/programmieren/wizardrytranslation/extracted/packdata_raw'
R1251 = open(f'{RAW}/1251_type01.raw','rb').read()
PORTRAIT_SRC = R1251[0xA1:0xA1+128*256*4]   # 128x256 PSMCT32 payload
CLUT_SRC = R1251[0x200D0:0x200D0+16*16*4]

HDR = 509
GS = {
  'MISSING_Portrait': 'C:/programmieren/wizardrytranslation/build/recon_portrait3/extract/MissingPortraitAndFuckedDialogue__gs.bin',
}

def load_vram(p):
    with open(p,'rb') as f:
        d = f.read()
    return np.frombuffer(d[HDR:HDR+4*1024*1024], dtype=np.uint8).copy()

for label, p in GS.items():
    vram = load_vram(p)
    print(f"==== {label} ====  vram bytes={len(vram)}")
    # dbp is in 256-byte page-block units? In GS, block pointer 'bp' addresses 256-byte units? 
    # Actually GS dbp is in units of 2048-byte 'words'? No: GS BITBLTBUF DBP is in units of 256 bytes? 
    # Standard: BP is in units of 'block' = 256 bytes? -> wrong.
    # GS frame/tex base pointers (TBP0, DBP) are in units of 2048/64 = 'word' = pages of 8192 bytes? 
    # Correct: GS pointers are in units of 256 bytes (a "block" is 256 bytes; pointer granularity is block=256 bytes for FBP*... ) 
    # The forensic uses base = 0x3000 * 256. So dbp unit = 256 bytes. Use that.
    for dbp in (0x3000, 0x3200):
        base = dbp*256
        region = vram[base:base+256*512]
        nz = int(np.count_nonzero(region))
        h = hashlib.md5(region[:0x8000].tobytes()).hexdigest()[:12]
        print(f"  dbp=0x{dbp:04X} base=0x{base:08X} nonzero={nz}/{len(region)} md5[:0x8000]={h}")
    # Does the portrait payload appear ANYWHERE in VRAM? (raw byte search of first 4KB of payload)
    needle = PORTRAIT_SRC[:4096]
    idx = vram.tobytes().find(needle)
    print(f"  portrait payload(4KB) found in VRAM at byteoff: {idx} (dbp={idx//256 if idx>=0 else 'N/A'})")
    # CLUT search
    cneedle = CLUT_SRC[:256]
    cidx = vram.tobytes().find(cneedle)
    print(f"  CLUT(256B) found in VRAM at byteoff: {cidx} (dbp={cidx//256 if cidx>=0 else 'N/A'})")
