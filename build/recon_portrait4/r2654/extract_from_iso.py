import sys,struct,json
sys.stdout.reconfigure(encoding='utf-8')
BASE='C:/programmieren/wizardrytranslation'
SECTOR=2048; NSUBS=44; NAME_SUB=7
FFFE=0xFFFE; FFFF=0xFFFF
KATA="アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲ"
KATA_EXTRA={93:'ー',238:'ン',254:'バ',245:'ジ',252:'デ',270:'ェ',273:'ヴ',246:'ズ',247:'ゼ',248:'ゾ',249:'ダ',253:'ド',272:'ッ'}
def nv_to_kana(nv):
    if 193<=nv<=193+44: return KATA[nv-193]
    return KATA_EXTRA.get(nv,'〓')
pack=open(f'{BASE}/build/recon_portrait4/r2654/PACKDATA_v91.bin','rb').read()
# TOC entry 2654
so,sc,tc=struct.unpack_from('<III',pack,2654*12)
print(f'R2654 TOC: sector_off={so} sector_cnt={sc} type_code={tc}')
data=pack[so*SECTOR:(so+sc)*SECTOR]
print(f'R2654 data {len(data)} bytes, first 16: {data[:16].hex()}')
def read_header(raw,nsubs):
    return [dict(zip(('sub','size','off','z'),struct.unpack_from('<4I',raw,i*16))) for i in range(nsubs)]
def read_sub_entries(raw,off,size):
    cnt=struct.unpack_from('>H',raw,off)[0]
    offs=[struct.unpack_from('>H',raw,off+4+k*4)[0] for k in range(cnt)]
    e=[]
    for k in range(cnt):
        st=off+offs[k]; en=off+(offs[k+1] if k+1<cnt else size); e.append(raw[st:en])
    return cnt,e
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
hdr=read_header(data,NSUBS)
nh=next(h for h in hdr if h['sub']==NAME_SUB)
print(f'sub {NAME_SUB}: off=0x{nh["off"]:06x} size=0x{nh["size"]:04x}')
cnt,entries=read_sub_entries(data,nh['off'],nh['size'])
print(f'count={cnt}')
for k in (7,16,10,18):
    if k<len(entries):
        print(f'  entry {k:2d}: {decode_entry(entries[k])!r}')
print('--- all entries with romaji ---')
romanized=0
for k,seg in enumerate(entries):
    d=decode_entry(seg)
    if d and not d.startswith('['): romanized+=1
print('romanized entries:',romanized)
print('ENTRY 7 =', repr(decode_entry(entries[7])))
