import sys, json, struct, os
sys.stdout.reconfigure(encoding='utf-8')
BASE='C:/programmieren/wizardrytranslation'
NSUBS=44; NAME_SUB=7
FFFE=0xFFFE; FFFF=0xFFFF
KATA="アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲ"
KATA_EXTRA={93:'ー',238:'ン',254:'バ',245:'ジ',252:'デ',270:'ェ',273:'ヴ',246:'ズ',247:'ゼ',248:'ゾ',249:'ダ',253:'ド',272:'ッ'}
def nv_to_kana(nv):
    if 193<=nv<=193+44: return KATA[nv-193]
    return KATA_EXTRA.get(nv,'〓')
def read_header(raw,nsubs):
    return [dict(zip(('sub','size','off','z'),struct.unpack_from('<4I',raw,i*16))) for i in range(nsubs)]
def read_sub_entries(raw,off,size):
    cnt=struct.unpack_from('>H',raw,off)[0]
    offs=[struct.unpack_from('>H',raw,off+4+k*4)[0] for k in range(cnt)]
    entries=[]
    for k in range(cnt):
        st=off+offs[k]; en=off+(offs[k+1] if k+1<cnt else size)
        entries.append(raw[st:en])
    return cnt,entries
def words_of(seg):
    return [struct.unpack_from('>H',seg,p)[0] for p in range(0,len(seg)-1,2)]
def decode_entry(seg):
    out=[]
    for w in words_of(seg):
        if w==FFFF: break
        if w==FFFE: continue
        if 95<=w<=95+94: out.append(chr((w-95)+0x20))
        else: out.append('['+nv_to_kana(w)+':%d]'%w)
    return ''.join(out)
def dump(path,label):
    raw=open(path,'rb').read()
    print(f'\n===== {label} : {path} ({len(raw)} bytes) =====')
    hdr=read_header(raw,NSUBS)
    nh=next(h for h in hdr if h['sub']==NAME_SUB)
    print(f'sub {NAME_SUB}: off=0x{nh["off"]:06x} size=0x{nh["size"]:04x}')
    cnt,entries=read_sub_entries(raw,nh['off'],nh['size'])
    print(f'count={cnt}')
    for k,seg in enumerate(entries):
        d=decode_entry(seg)
        vals=[w for w in words_of(seg) if w not in (FFFE,FFFF)]
        print(f'  entry {k:2d}: {d!r}   raw_vals={vals}')
dump(f'{BASE}/extracted/packdata_raw/2654_type44.raw','PRISTINE')
dump(f'{BASE}/build/packdata_resources/2654_type44.raw','BUILD OUTPUT')
