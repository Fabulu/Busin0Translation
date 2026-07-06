import zipfile, struct, sys, os, hashlib
sys.stdout.reconfigure(encoding='utf-8')
import zstandard as zstd

# Known portrait resource R1251 raw (extracted)
R1251_PATH='extracted/packdata_raw/1251_type01.raw'
r1251=open(R1251_PATH,'rb').read()
# portrait pixel block at +0xA1 size 0x20000; CLUT at +0x200d0
PORTRAIT_SIG=r1251[0xA1:0xA1+512]
CLUT_SIG=r1251[0x200d0:0x200d0+64]
print('R1251 size',len(r1251),'md5',hashlib.md5(r1251).hexdigest())

def ee_from_p2s(path):
    z=zipfile.ZipFile(path)
    info=z.getinfo('eeMemory.bin')
    raw=z.open('eeMemory.bin').read() if info.compress_type==0 else None
    if raw is None:
        # zstd compressed: read the stored compressed bytes manually
        with z.open('eeMemory.bin') as f:
            comp=f.read()  # zipfile returns DECOMPRESSED only if it knows the method; for 93 it raises
    return raw

# zipfile cannot handle method 93. Read compressed bytes directly from the zip.
def ee_raw(path):
    z=zipfile.ZipFile(path)
    info=z.getinfo('eeMemory.bin')
    # locate local header & compressed data
    with open(path,'rb') as f:
        f.seek(info.header_offset)
        lh=f.read(30)
        assert lh[:4]==b'PK\x03\x04', lh[:4]
        n=struct.unpack_from('<H',lh,26)[0]
        m=struct.unpack_from('<H',lh,28)[0]
        f.seek(info.header_offset+30+n+m)
        comp=f.read(info.compress_size)
    if info.compress_type==0:
        return comp
    # method 93 = zstd
    d=zstd.ZstdDecompressor()
    return d.decompress(comp, max_output_size=info.file_size)

def analyze(path):
    name=os.path.basename(path)
    if path.endswith('.p2s'):
        ee=ee_raw(path)
    else:
        ee=open(path,'rb').read()
    print(f'\n===== {name} (ee {len(ee)} bytes) =====')
    # Is R1251 portrait pixel block present anywhere?
    pos=ee.find(PORTRAIT_SIG)
    clutpos=ee.find(CLUT_SIG)
    print(f'  portrait-pixel-sig found @ {hex(pos) if pos>=0 else "NOT FOUND"}')
    print(f'  R1251 CLUT-sig found     @ {hex(clutpos) if clutpos>=0 else "NOT FOUND"}')
    # CG-slot table: read globals 0x509E00 .. 0x509FA0 (RAM offset == vaddr for EE image)
    base=0x509E00
    print('  CG-slot region 0x509E00..0x509FA0 (u32 LE):')
    for off in range(base, 0x509FA0, 4):
        v=struct.unpack_from('<I',ee,off)[0]
        mark=''
        if 0x1000000<=v<0x2000000: mark='<-RAM ptr'
        print(f'    0x{off:06X}: 0x{v:08X} {mark}')
    # specifically the portrait data ptr & clut ptr
    pdp=struct.unpack_from('<I',ee,0x509F80)[0]
    cgp=struct.unpack_from('<I',ee,0x509F8C)[0]
    print(f'  portrait_data_ptr(0x509F80)=0x{pdp:08X}  clut_ptr(0x509F8C)=0x{cgp:08X}')
    if 0<pdp<len(ee):
        # does ptr point at portrait pixel data?
        chunk=ee[pdp:pdp+0x200]
        ph=chunk.find(PORTRAIT_SIG[:64])
        # also compare to r1251 header
        same_hdr = ee[pdp:pdp+0xA1]==r1251[:0xA1]
        print(f'    *ptr target: matches R1251 header[:0xA1]={same_hdr}; contains pixel-sig-prefix={ph>=0}')
        print(f'    ptr target md5(first 0x204c0)={hashlib.md5(ee[pdp:pdp+0x204c0]).hexdigest() if pdp+0x204c0<=len(ee) else "OOB"}')

if __name__=='__main__':
    for p in sys.argv[1:]:
        try:
            analyze(p)
        except Exception as e:
            print(f'\n===== {p} ERROR: {e} =====')
