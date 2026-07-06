import zipfile, struct, sys, os
sys.stdout.reconfigure(encoding='utf-8')
import zstandard as zstd
r1251=open('extracted/packdata_raw/1251_type01.raw','rb').read()
SIG=r1251[0xA1:0xA1+256]

def ee_raw(path):
    if not path.endswith('.p2s'): return open(path,'rb').read()
    z=zipfile.ZipFile(path); info=z.getinfo('eeMemory.bin')
    with open(path,'rb') as f:
        f.seek(info.header_offset); lh=f.read(30)
        n=struct.unpack_from('<H',lh,26)[0]; m=struct.unpack_from('<H',lh,28)[0]
        f.seek(info.header_offset+30+n+m); comp=f.read(info.compress_size)
    if info.compress_type==0: return comp
    return zstd.ZstdDecompressor().decompress(comp, max_output_size=info.file_size)

def analyze(path):
    name=os.path.basename(path); ee=ee_raw(path)
    if len(ee)<0x600000: print(name,'small'); return
    # find ALL occurrences of portrait pixel sig
    occ=[]; st=0
    while True:
        p=ee.find(SIG,st)
        if p<0: break
        occ.append(p); st=p+1
    print(f'\n##### {name}: portrait-pixel copies at {[hex(o) for o in occ]}')
    # the resource buffer start = occ - 0xA1 (R1251 file layout) => candidate ptr targets
    targets=set()
    for o in occ:
        targets.add(o)            # pixel block start
        targets.add(o-0xA1)       # resource buffer start
    # search for 32-bit LE pointers (in RAM range 0..0x2000000) pointing AT any target +/- alignment
    # build set of plausible pointer values: target and target rounded; also the data ptr the BITBLT uses
    wanted={t for t in targets}
    # scan entire RAM for words equal to any wanted value
    found={}
    import array
    a=struct.unpack('<%dI'%(len(ee)//4), ee[:len(ee)//4*4])
    for i,v in enumerate(a):
        if v in wanted:
            found.setdefault(v,[]).append(i*4)
    for v in sorted(found):
        locs=found[v]
        print(f'  ptr-value 0x{v:06X} referenced at {len(locs)} sites: {[hex(x) for x in locs[:20]]}')

for p in sys.argv[1:]: analyze(p)
