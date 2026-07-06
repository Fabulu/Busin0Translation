import sys, struct
sys.stdout.reconfigure(encoding='utf-8')
NSUBS=44
def hdr(raw):
    return [dict(zip(('sub','size','off','z'), struct.unpack_from('<4I', raw, i*16))) for i in range(NSUBS)]
def which(raw,off):
    for h in hdr(raw):
        if h['off']<=off<h['off']+h['size']:
            return h
    return None

for fname,label,offs in [
    ('build/recon_fvs/vera/r2654_from_v92iso.raw','v92 ISO',[0x8a4c,0x34ab8]),
    ('extracted/packdata_raw/2654_type44.raw','PRISTINE',[0x831a,0x8a1c,0x2aaa8]),
]:
    raw=open(fname,'rb').read()
    print(f'\n=== {label} ===')
    print('  sub table:')
    for h in hdr(raw):
        print(f'    sub{h["sub"]:2d}: off=0x{h["off"]:06x} size=0x{h["size"]:x} end=0x{h["off"]+h["size"]:06x}')
    for o in offs:
        h=which(raw,o)
        print(f'  offset 0x{o:06x} -> {"sub"+str(h["sub"]) if h else "NONE"} (rel +0x{o-h["off"]:x})' if h else f'  offset 0x{o:06x} -> NONE')
