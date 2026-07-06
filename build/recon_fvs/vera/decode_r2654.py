import sys,json,struct
sys.stdout.reconfigure(encoding='utf-8')
KATA="アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲ"
KATA_EXTRA={93:'ー',238:'ン',254:'バ',245:'ジ',252:'デ',270:'ェ',273:'ヴ',246:'ズ',247:'ゼ',248:'ゾ',249:'ダ',253:'ド',272:'ッ'}
def nv_to_kana(nv):
    if 193<=nv<=237: return KATA[nv-193]
    return KATA_EXTRA.get(nv,f'<{nv}>')
def read_header(raw,nsubs=44):
    return [dict(zip(('sub','size','off','z'),struct.unpack_from('<4I',raw,i*16))) for i in range(nsubs)]
def words_of(seg):
    return [struct.unpack_from('>H',seg,p)[0] for p in range(0,len(seg)-1,2)]
def dump(path):
    print('===',path,'===')
    raw=open(path,'rb').read()
    print('len',len(raw))
    hdr=read_header(raw)
    nh=next(h for h in hdr if h['sub']==7)
    print('sub7 off=0x%06x size=0x%04x'%(nh['off'],nh['size']))
    off,size=nh['off'],nh['size']
    cnt=struct.unpack_from('>H',raw,off)[0]
    offs=[struct.unpack_from('>H',raw,off+4+k*4)[0] for k in range(cnt)]
    print('count',cnt)
    for k in range(cnt):
        st=off+offs[k]; en=off+(offs[k+1] if k+1<cnt else size)
        seg=raw[st:en]
        vals=[w for w in words_of(seg) if w not in (0xFFFE,0xFFFF)]
        s=''
        for v in vals:
            if 95<=v<=189: s+=chr(v-95+0x20)
            else: s+='['+nv_to_kana(v)+']'
        print('  entry %2d  vals=%s  -> %r'%(k,vals,s))
for p in ('extracted/packdata_raw/2654_type44.raw','build/packdata_resources/2654_type44.raw'):
    dump(p)
