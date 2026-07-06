import zipfile, struct, sys, os, hashlib
sys.stdout.reconfigure(encoding='utf-8')
import zstandard as zstd

r1251=open('extracted/packdata_raw/1251_type01.raw','rb').read()
PORTRAIT_SIG=r1251[0xA1:0xA1+256]

def ee_raw(path):
    if not path.endswith('.p2s'):
        return open(path,'rb').read()
    z=zipfile.ZipFile(path); info=z.getinfo('eeMemory.bin')
    with open(path,'rb') as f:
        f.seek(info.header_offset); lh=f.read(30)
        n=struct.unpack_from('<H',lh,26)[0]; m=struct.unpack_from('<H',lh,28)[0]
        f.seek(info.header_offset+30+n+m); comp=f.read(info.compress_size)
    if info.compress_type==0: return comp
    return zstd.ZstdDecompressor().decompress(comp, max_output_size=info.file_size)

# RAM addresses found by disasm:
SLOT_TBL = 0x542748   # 6 x s16 : slot[i] = descriptor index, -1 = free
DESC_BASE= 0x55E5A0   # 30 x 480-byte sprite descriptors (0x560000-8928)
DESC_STRIDE=480

def s16(b,o):
    v=struct.unpack_from('<h',b,o)[0]; return v

def analyze(path):
    name=os.path.basename(path)
    try: ee=ee_raw(path)
    except Exception as e:
        print(f'\n##### {name}: ERR {e}'); return
    if len(ee)<0x600000:
        print(f'\n##### {name}: ee too small ({len(ee)})'); return
    print(f'\n##### {name} (ee {len(ee)})')
    # portrait pixel data resident?
    pp=ee.find(PORTRAIT_SIG)
    print(f'  R1251 portrait pixels resident in RAM @ {hex(pp) if pp>=0 else "ABSENT"}')
    # slot table
    slots=[s16(ee,SLOT_TBL+i*2) for i in range(6)]
    print(f'  SLOT_TBL 0x{SLOT_TBL:06X}: {slots}')
    # descriptor field probe for active slots
    for i,sl in enumerate(slots):
        if sl<0 or sl>=30: continue
        d=DESC_BASE+sl*DESC_STRIDE
        # dump first 0x40 bytes as s16 to spot CG id / format / dbp / wh
        hdr=ee[d:d+0x60]
        fields=[struct.unpack_from('<h',hdr,k)[0] for k in range(0,0x60,2)]
        print(f'   slot[{i}]=desc{sl} @0x{d:06X} s16[0:48]={fields}')
    return slots, pp

paths=sys.argv[1:]
for p in paths: analyze(p)
