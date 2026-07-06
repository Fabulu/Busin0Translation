import struct, json, sys, os
sys.stdout.reconfigure(encoding='utf-8')
os.chdir('C:/programmieren/wizardrytranslation')

NSUBS=44; NAME_SUB=7
KATA_BASE=193
KATA = "アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲ"
KATA_EXTRA = {93:'ー',238:'ン',254:'バ',245:'ジ',252:'デ',270:'ェ',273:'ヴ',246:'ズ',247:'ゼ',248:'ゾ',249:'ダ',253:'ド',272:'ッ'}
def nv_to_kana(nv):
    if KATA_BASE<=nv<=KATA_BASE+44: return KATA[nv-KATA_BASE]
    return KATA_EXTRA.get(nv,f'<{nv}>')

def read_header(raw):
    return [dict(zip(('sub','size','off','z'), struct.unpack_from('<4I', raw, i*16))) for i in range(NSUBS)]

def decode_file(path, label):
    print(f'\n========== {label}: {path} ==========')
    raw = open(path,'rb').read()
    print(f'len={len(raw)}')
    hdr = read_header(raw)
    nh = next(h for h in hdr if h['sub']==NAME_SUB)
    print(f'sub7: off=0x{nh["off"]:06x} size=0x{nh["size"]:x}')
    off, size = nh['off'], nh['size']
    cnt = struct.unpack_from('>H', raw, off)[0]
    print(f'count={cnt}')
    offs = [struct.unpack_from('>H', raw, off+4+k*4)[0] for k in range(cnt)]
    for k in range(cnt):
        st = off+offs[k]
        en = off+(offs[k+1] if k+1<cnt else size)
        seg = raw[st:en]
        words = [struct.unpack_from('>H', seg, p)[0] for p in range(0, len(seg)-1, 2)]
        s=[]
        for w in words:
            if w==0xFFFF: break
            if w==0xFFFE: continue
            if 95<=w<=189: s.append(chr((w-95)+0x20))
            else: s.append('['+nv_to_kana(w)+']')
        decoded=''.join(s)
        rawwords=' '.join(f'{w:04x}' for w in words)
        mark = ' <-- ENTRY 7' if k==7 else ''
        print(f'  e{k:2d}: {decoded:20s} | {rawwords}{mark}')

decode_file('build/recon_fvs/vera/r2654_from_v92iso.raw', 'SHIPPED v92 ISO')
