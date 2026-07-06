import zipfile, struct, sys, os, hashlib
sys.stdout.reconfigure(encoding='utf-8')
import zstandard as zstd

def ee_raw(path):
    z=zipfile.ZipFile(path); info=z.getinfo('eeMemory.bin')
    with open(path,'rb') as f:
        f.seek(info.header_offset); lh=f.read(30)
        n=struct.unpack_from('<H',lh,26)[0]; m=struct.unpack_from('<H',lh,28)[0]
        f.seek(info.header_offset+30+n+m); comp=f.read(info.compress_size)
    if info.compress_type==0: return comp
    return zstd.ZstdDecompressor().decompress(comp, max_output_size=info.file_size)

# EXE in RAM at vaddr 0x100000. Hash a code region that is patched per-version.
# Use the whole code text region 0x100000..0x4FDC80 and a few sub-hashes.
def exe_region(ee, va, ln):
    return ee[va:va+ln]

# Reference EXEs: pristine JP and v90 patched (file off 0x80 -> vaddr 0x100000)
def exe_from_file(path, va, ln):
    data=open(path,'rb').read()
    fo = va - 0x100000 + 0x80
    return data[fo:fo+ln]

JP_EXE='extracted/SLPM_653.78'
# v90 patched EXE: produced by build; check build dir
V90_EXE_CANDS=['build/SLPM_653.78_patched','build/SLPM_653.78_v90','build/SLPM_653.78']

# pick a region likely patched: save-name / SJIS strings region. Hash whole 0x100000..0x500000
RV=0x100000; RL=0x400000
jp = exe_from_file(JP_EXE, RV, RL)
print('JP exe region md5', hashlib.md5(jp).hexdigest())
for c in V90_EXE_CANDS:
    if os.path.exists(c):
        try:
            r=exe_from_file(c,RV,RL)
            print(f'{c} md5 {hashlib.md5(r).hexdigest()} diffbytes_vs_JP={sum(1 for a,b in zip(jp,r) if a!=b)}')
        except Exception as e:
            print(c,'err',e)

saves=sys.argv[1:]
for s in saves:
    p='RAMdumps/'+s+'.p2s' if not s.endswith('.bin') and not s.endswith('.p2s') else s
    try:
        ee=ee_raw(p) if p.endswith('.p2s') else open(p,'rb').read()
    except Exception as e:
        print(f'{s}: ERR {e}'); continue
    r=exe_region(ee,RV,RL)
    d_jp=sum(1 for a,b in zip(jp,r) if a!=b)
    print(f'{os.path.basename(s):40s} exe md5 {hashlib.md5(r).hexdigest()} diff_vs_JP={d_jp}')
