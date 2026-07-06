import struct, os, sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath('tools'))
from psmt4_deswizzle import deswizzle_psmt4
from PIL import Image

PIXEL_OFF = 1962944
PIXEL_SIZE = 131072
TEX_W = TEX_H = 512
BW_PSMT4 = 512
DBW_CT32 = 256

def get_packdata_lba(iso):
    iso.seek(16*2048)
    pvd = iso.read(2048)
    root_lba = struct.unpack_from('<I', pvd, 158)[0]
    iso.seek(root_lba*2048)
    root_dir = iso.read(4096)
    pos = 0
    pack_lba = None
    while pos < len(root_dir):
        ln = root_dir[pos]
        if ln == 0: break
        nm_len = root_dir[pos+32]
        nm = root_dir[pos+33:pos+33+nm_len].decode('ascii','replace')
        if 'PACKDATA' in nm:
            pack_lba = struct.unpack_from('<I', root_dir, pos+2)[0]
        pos += ln
    return pack_lba

def get_r2880(iso_path):
    with open(iso_path,'rb') as iso:
        pack_lba = get_packdata_lba(iso)
        base = pack_lba*2048
        # TOC entry 2880
        iso.seek(base + 2880*12)
        so, sc, tc = struct.unpack('<III', iso.read(12))
        abs_off = base + so*2048
        iso.seek(abs_off + PIXEL_OFF)
        blob = iso.read(PIXEL_SIZE)
        return blob, (so, sc, tc)

def decode_png(blob, out):
    linear = bytearray(deswizzle_psmt4(blob, TEX_W, TEX_H, bw_psmt4=BW_PSMT4, dbw_ct32=DBW_CT32))
    img = Image.new("L",(TEX_W,TEX_H))
    img.putdata([min(255,p*17) for p in linear])
    img.save(out)
    return linear

for v in ['v86','v88','v89']:
    p = f'build/BUSIN0_EN_{v}.iso'
    blob, toc = get_r2880(p)
    out = f'build/recon_v89/intro/r2880s7_{v}.png'
    decode_png(blob, out)
    h = __import__('hashlib').md5(blob).hexdigest()[:12]
    print(f'{v}: toc={toc} md5={h} -> {out}')
